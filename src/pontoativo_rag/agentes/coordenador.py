"""Fluxo documental compartilhado pelo terminal e pela aplicação web.

Interpretação -> Pesquisa -> Análise -> Validação -> Comunicação.
A Validação pode devolver o rascunho à Análise e solicitar uma busca complementar.
"""

from collections.abc import Callable
from time import perf_counter

from ..configuracao import Settings
from ..geracao import GroundedAnswer, LLMClient, LLMUnavailable
from ..recursos import criar_cliente, criar_recuperador
from .analise import AnaliseInvalida, analisar_duvidas, verificar_pergunta
from .comunicacao import AgenteComunicacao, ComunicacaoRecusada
from .interpretacao import AgenteInterpretacao
from .pesquisa import AgentePesquisa, criar_agente
from .validacao import AgenteValidacao, ParecerInvalido, feedback_para_analise


class ValidacaoReprovada(RuntimeError):
    """O rascunho continuou sem apoio nas fontes depois das correções permitidas."""


class FluxoDocumental:
    def __init__(
        self, pesquisa: AgentePesquisa, cliente: LLMClient | None, *,
        orcamento_segundos: float = 180, validacao: AgenteValidacao | None = None,
        max_correcoes: int = 1, registrar: Callable[[dict], None] | None = None,
    ):
        if orcamento_segundos <= 0:
            raise ValueError("O orçamento de execução deve ser positivo.")
        if max_correcoes < 0:
            raise ValueError("max_correcoes não pode ser negativo.")
        self.interpretacao = AgenteInterpretacao()
        self.pesquisa = pesquisa
        self.cliente = cliente
        self.orcamento_segundos = orcamento_segundos
        self.validacao = validacao
        self.comunicacao = AgenteComunicacao()
        self.max_correcoes = max_correcoes
        self.registrar = registrar

    def _registrar(self, evento: dict) -> None:
        if self.registrar is not None:
            self.registrar(evento)

    def responder(
        self, pergunta: str, *, top_k: int | None = None,
        filters: dict[str, str] | None = None,
    ) -> tuple[GroundedAnswer, float]:
        verificar_pergunta(pergunta)
        inicio = perf_counter()
        prazo = inicio + self.orcamento_segundos
        acao = self.interpretacao.preparar_pesquisa(pergunta)
        self._registrar({"etapa": "interpretacao_para_pesquisa", "acao": acao,
                         "duvidas": self.interpretacao.identificar_duvidas(pergunta)})
        resultado, recuperados = self.pesquisa.pesquisar(
            acao, top_k=top_k, filtros=filters,
        )
        self._registrar({"etapa": "pesquisa_para_analise", "resultado": resultado})
        tempo_busca = perf_counter() - inicio
        # Cópias: uma busca complementar pedida pela Validação estende estas listas.
        trechos = list(resultado["trechos"])
        recuperados = list(recuperados)
        if not trechos:
            return GroundedAnswer(
                pergunta, "abstencao",
                "Os documentos recuperados não oferecem evidências suficientes para responder.",
                recuperados,
            ), tempo_busca

        inicio = perf_counter()
        motivo = "geração desativada"
        tentativas = 0
        if self.cliente is not None:
            def registrar_tentativa() -> None:
                nonlocal tentativas
                if perf_counter() >= prazo:
                    raise LLMUnavailable("Orçamento de execução esgotado")
                tentativas += 1

            cliente = _ClienteComPrazo(self.cliente, prazo)
            pergunta_analise = acao["pergunta_original"] or pergunta
            try:
                itens = analisar_duvidas(
                    pergunta_analise, trechos, cliente=cliente,
                    ao_tentar=registrar_tentativa, registrar=self._registrar,
                )
                comunicado = None
                if self.validacao is not None:
                    itens, parecer = self._validar(
                        pergunta_analise, itens, trechos, recuperados, acao, cliente,
                        registrar_tentativa, top_k=top_k, filters=filters,
                    )
                    comunicado = self.comunicacao.comunicar(pergunta_analise, itens, trechos, parecer)
            except LLMUnavailable:
                motivo = "modelo indisponível"
            except AnaliseInvalida:
                motivo = "a análise não passou na validação de citações"
            except ParecerInvalido:
                motivo = "a validação não conseguiu revisar o rascunho"
            except ValidacaoReprovada:
                motivo = "o rascunho não passou na validação das fontes"
            except ComunicacaoRecusada:
                motivo = "a comunicação recusou o parecer do rascunho"
            else:
                por_id = {chunk.chunk_id: chunk for chunk in recuperados}
                relevantes = [por_id[trecho["chunk_id"]] for trecho in trechos]
                indices = {trecho["id"]: i for i, trecho in enumerate(trechos)}
                citados = {ref for item in itens for ref in item["trechos"]}
                referencias = None
                if comunicado is not None:
                    texto = comunicado["texto"]
                    referencias = {fonte["id"]: fonte["ref"] for fonte in comunicado["fontes"]}
                    self._registrar({"etapa": "comunicacao", "comunicado": comunicado})
                else:
                    texto = "\n".join(
                        " ".join([item["conclusao"], *(f"[F{indices[ref] + 1}]"
                                                      for ref in item["trechos"])])
                        for item in itens
                    )
                return GroundedAnswer(
                    pergunta, "rag", texto, relevantes,
                    cited=[chunk for ref, chunk in zip(indices, relevantes) if ref in citados],
                    model_abstained=all(item["estado"] == "lacuna" for item in itens),
                    model=self.cliente.model, generation_seconds=perf_counter() - inicio,
                    generation_attempts=tentativas,
                    source_refs=referencias,
                ), tempo_busca

        por_id = {chunk.chunk_id: chunk for chunk in recuperados}
        relevantes = [por_id[trecho["chunk_id"]] for trecho in trechos]
        return GroundedAnswer(
            pergunta, "recuperacao_sem_geracao",
            f"Não foi possível redigir uma resposta ({motivo}). Consulte os trechos recuperados.",
            relevantes, generation_seconds=perf_counter() - inicio,
            generation_attempts=tentativas,
        ), tempo_busca

    def _validar(self, pergunta, itens, trechos, recuperados, acao, cliente, ao_tentar,
                 *, top_k, filters):
        """Valida o rascunho; devolve trechos sem apoio à Análise e, se pedido, busca de novo.

        ``trechos`` e ``recuperados`` são estendidos no lugar quando a Validação
        pede uma consulta complementar à Pesquisa.
        """
        pesquisou_de_novo = False
        # A Validação usa o próprio cliente (ou só regras), sob o mesmo prazo da consulta.
        revisor = (_ClienteComPrazo(self.validacao.cliente, cliente.prazo)
                   if self.validacao.cliente is not None else None)
        for rodada in range(self.max_correcoes + 1):
            try:
                parecer = self.validacao.revisar(
                    pergunta, itens, trechos, pode_pesquisar=not pesquisou_de_novo, cliente=revisor,
                    ao_tentar=ao_tentar,
                )
            except ParecerInvalido as erro:
                self._registrar({"etapa": "validacao", "rodada": rodada + 1, "erro": str(erro),
                                 "saida_bruta": erro.bruto})
                raise
            self._registrar({"etapa": "validacao", "rodada": rodada + 1, "parecer": parecer,
                             "trechos": list(trechos)})
            if parecer["aprovado"]:
                return itens, parecer
            if rodada == self.max_correcoes:
                raise ValidacaoReprovada(parecer["problemas"])
            if consulta := parecer["consulta_complementar"]:
                pesquisou_de_novo = True
                nova_acao = {**acao, "consulta": consulta}
                self._registrar({"etapa": "validacao_para_pesquisa", "acao": nova_acao})
                resultado, novos = self.pesquisa.pesquisar(nova_acao, top_k=top_k, filtros=filters)
                self._registrar({"etapa": "pesquisa_para_analise", "resultado": resultado})
                _acrescentar_trechos(trechos, recuperados, resultado["trechos"], novos)
            feedback = feedback_para_analise(parecer, itens)
            self._registrar({"etapa": "validacao_para_analise", "feedback": feedback,
                             "trechos_para_corrigir": parecer["problemas"]})
            itens = analisar_duvidas(
                pergunta, trechos, cliente=cliente, ao_tentar=ao_tentar,
                feedback=feedback, rascunho_anterior=itens, registrar=self._registrar,
            )
        raise AssertionError("Laço de validação esgotado")


def _acrescentar_trechos(trechos, recuperados, novos_trechos, novos_chunks) -> None:
    """Junta a busca complementar sem repetir chunks e mantendo IDs T1, T2... únicos."""
    vistos = {t["chunk_id"] for t in trechos}
    ja_recuperados = {c.chunk_id for c in recuperados}
    chunks = {c.chunk_id: c for c in novos_chunks}
    for trecho in novos_trechos:
        if trecho["chunk_id"] in vistos:
            continue
        vistos.add(trecho["chunk_id"])
        trechos.append({**trecho, "id": f"T{len(trechos) + 1}"})
        if trecho["chunk_id"] not in ja_recuperados:
            recuperados.append(chunks[trecho["chunk_id"]])


def criar_fluxo_documental(
    settings: Settings, *, use_llm: bool = True, reranker: str = "hibrido",
    validar: bool = True,
) -> FluxoDocumental:
    recuperador = criar_recuperador(settings, reranker=reranker)
    cliente = criar_cliente(
        settings, num_predict=max(1600, settings.ollama_num_predict),
    ) if use_llm else None
    return FluxoDocumental(
        criar_agente(settings, buscador=recuperador), cliente,
        orcamento_segundos=settings.ollama_timeout_seconds,
        validacao=AgenteValidacao(cliente) if validar and cliente is not None else None,
    )


class _ClienteComPrazo:
    """Compartilha o orçamento entre chamadas, sem alterar o cliente reutilizado.

    O timeout HTTP limita inatividade de rede; não interrompe a busca nem
    garante cancelamento da inferência no servidor.
    """

    def __init__(self, cliente: LLMClient, prazo: float):
        self.cliente = cliente
        self.model = cliente.model
        self.prazo = prazo

    def complete(self, system: str, user: str, **kwargs) -> str:
        restante = self.prazo - perf_counter()
        if restante <= 0:
            raise LLMUnavailable("Orçamento de execução esgotado")
        return self.cliente.complete(system, user, timeout_seconds=restante, **kwargs)
