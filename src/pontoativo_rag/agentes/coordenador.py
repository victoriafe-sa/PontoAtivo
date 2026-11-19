"""Fluxo documental compartilhado pelo terminal e pela aplicação web."""

from time import perf_counter

from ..configuracao import Settings
from ..geracao import GroundedAnswer, LLMClient, LLMUnavailable
from ..recursos import criar_cliente, criar_recuperador
from .analise import AnaliseInvalida, analisar_duvidas, verificar_pergunta
from .interpretacao import AgenteInterpretacao
from .pesquisa import AgentePesquisa, criar_agente


class FluxoDocumental:
    def __init__(self, pesquisa: AgentePesquisa, cliente: LLMClient | None, *, orcamento_segundos: float = 180):
        if orcamento_segundos <= 0:
            raise ValueError("O orçamento de execução deve ser positivo.")
        self.interpretacao = AgenteInterpretacao()
        self.pesquisa = pesquisa
        self.cliente = cliente
        self.orcamento_segundos = orcamento_segundos

    def responder(
        self, pergunta: str, *, top_k: int | None = None,
        filters: dict[str, str] | None = None,
    ) -> tuple[GroundedAnswer, float]:
        verificar_pergunta(pergunta)
        inicio = perf_counter()
        prazo = inicio + self.orcamento_segundos
        acao = self.interpretacao.preparar_pesquisa(pergunta)
        resultado, recuperados = self.pesquisa.pesquisar(
            acao, top_k=top_k, filtros=filters,
        )
        tempo_busca = perf_counter() - inicio
        trechos = resultado["trechos"]
        if not trechos:
            return GroundedAnswer(
                pergunta, "abstencao",
                "Os documentos recuperados não oferecem evidências suficientes para responder.",
                recuperados,
            ), tempo_busca

        por_id = {chunk.chunk_id: chunk for chunk in recuperados}
        relevantes = [por_id[trecho["chunk_id"]] for trecho in trechos]
        inicio = perf_counter()
        motivo = "geração desativada"
        tentativas = 0
        if self.cliente is not None:
            def registrar_tentativa() -> None:
                nonlocal tentativas
                if perf_counter() >= prazo:
                    raise LLMUnavailable("Orçamento de execução esgotado")
                tentativas += 1

            try:
                itens = analisar_duvidas(
                    acao["pergunta_original"] or pergunta, trechos,
                    cliente=_ClienteComPrazo(self.cliente, prazo), ao_tentar=registrar_tentativa,
                )
            except LLMUnavailable:
                motivo = "modelo indisponível"
            except AnaliseInvalida:
                motivo = "a análise não passou na validação de citações"
            else:
                indices = {trecho["id"]: i for i, trecho in enumerate(trechos)}
                citados = {ref for item in itens for ref in item["trechos"]}
                linhas = [
                    " ".join([item["conclusao"], *(f"[F{indices[ref] + 1}]" for ref in item["trechos"])])
                    for item in itens
                ]
                return GroundedAnswer(
                    pergunta, "rag", "\n".join(linhas), relevantes,
                    cited=[chunk for ref, chunk in zip(indices, relevantes) if ref in citados],
                    model_abstained=all(item["estado"] == "lacuna" for item in itens),
                    model=self.cliente.model, generation_seconds=perf_counter() - inicio,
                    generation_attempts=tentativas,
                ), tempo_busca

        return GroundedAnswer(
            pergunta, "recuperacao_sem_geracao",
            f"Não foi possível redigir uma resposta ({motivo}). Consulte os trechos recuperados.",
            relevantes, generation_seconds=perf_counter() - inicio,
            generation_attempts=tentativas,
        ), tempo_busca


def criar_fluxo_documental(
    settings: Settings, *, use_llm: bool = True, reranker: str = "hibrido",
) -> FluxoDocumental:
    recuperador = criar_recuperador(settings, reranker=reranker)
    cliente = criar_cliente(
        settings, num_predict=max(1600, settings.ollama_num_predict),
    ) if use_llm else None
    return FluxoDocumental(
        criar_agente(settings, buscador=recuperador), cliente,
        orcamento_segundos=settings.ollama_timeout_seconds,
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
