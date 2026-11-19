"""Demonstra a Validação corrigindo um rascunho e salva a troca entre os agentes.

Pergunta: cadeirante no Parque da Cidade Dona Sarah Kubitschek (fonte F029).

    Interpretação -> Pesquisa -> Análise -> Validação -> Análise (correção) -> Validação -> Comunicação

O que é real e o que é preparado:
- Interpretação, Pesquisa, Validação e o coordenador são o código do projeto.
- A Pesquisa busca no corpus do protótipo (prototipo/dados/chunks.jsonl), onde
  está a F029, com uma busca lexical: o índice vetorial principal não contém
  essa fonte. Distância = 1 - fração dos termos da consulta presentes no trecho.
- O PRIMEIRO rascunho da Análise é o exemplo preparado à mão com a etapa
  inventada (docs/agentes/exemplos/validacao_rascunho_etapa_inventada.json),
  para garantir que haja algo a corrigir. A correção é feita pelo modelo real.
- A Validação usa as regras e, sem --so-regras, o modelo real (revisão semântica).
- A Comunicação é provisória: junta as conclusões aprovadas e o link da fonte.

Uso na raiz:
    PYTHONPATH=src .venv/bin/python scripts/demonstrar_validacao.py --modelo qwen3:8b --so-regras
    PYTHONPATH=src .venv/bin/python scripts/demonstrar_validacao.py --modelo qwen3:8b \\
        --modelo-validacao llama3.1:8b --saida experimentos/agentes/outra-rodada.json
"""

import argparse
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pontoativo_rag.agentes.coordenador import FluxoDocumental
from pontoativo_rag.agentes.pesquisa import AgentePesquisa
from pontoativo_rag.agentes.validacao import AgenteValidacao
from pontoativo_rag.configuracao import Settings
from pontoativo_rag.geracao import OllamaClient
from pontoativo_rag.recuperacao import RetrievedChunk

RAIZ = Path(__file__).resolve().parents[1]
CORPUS = RAIZ / "prototipo" / "dados" / "chunks.jsonl"
DOCUMENTO_F029 = "prototipo/dados/fontes/texto/F029_parque-da-cidade-dona-sarah-kubitschek-sel.txt"
RASCUNHO_INVENTADO = RAIZ / "docs" / "agentes" / "exemplos" / "validacao_rascunho_etapa_inventada.json"
PERGUNTA = ("Uso cadeira de rodas e quero visitar o Parque da Cidade Dona Sarah Kubitschek. "
            "Preciso pagar para entrar? Há banheiros acessíveis? O caminho até eles também é acessível?")
NEUTRAS = {"para", "quero", "preciso", "tambem", "eles", "visitar", "dona"}


def _termos(texto):
    texto = "".join(c for c in unicodedata.normalize("NFKD", texto.casefold())
                    if not unicodedata.combining(c))
    return {p[:6] for p in re.findall(r"\w+", texto) if len(p) >= 4 and p not in NEUTRAS}


class BuscaLexicaCorpus:
    """Buscador do protótipo para a demonstração; não substitui o índice vetorial."""

    def __init__(self, caminho):
        self.chunks = [json.loads(linha) for linha in caminho.read_text(encoding="utf-8").splitlines()]

    def search(self, question, top_k=None, filters=None):
        consulta = _termos(question)
        pontuados = []
        for c in self.chunks:
            fracao = len(consulta & _termos(c["texto_indexado"])) / max(len(consulta), 1)
            m = c["metadados"]
            pontuados.append(RetrievedChunk(
                c["id"], m["id_fonte"], m["titulo"], m["orgao"], m["link"], c["texto"],
                round(1 - fracao, 4), 1, lexical_overlap=fracao,
                freshness_status=m.get("ressalvas", ""),
            ))
        pontuados.sort(key=lambda c: c.distance)
        return pontuados[: top_k or 3]


class AnaliseComPrimeiroRascunhoPreparado:
    """Devolve o rascunho preparado na 1ª chamada; as seguintes vão ao modelo real."""

    def __init__(self, cliente, rascunho):
        self.cliente, self.model, self.rascunho = cliente, cliente.model, rascunho
        self.chamadas = 0

    def complete(self, system, user, **kwargs):
        self.chamadas += 1
        if self.chamadas == 1:
            return json.dumps(self.rascunho, ensure_ascii=False)
        return self.cliente.complete(system, user, **kwargs)


def comunicar(itens, trechos):
    """Comunicação provisória: conclusões aprovadas, na ordem das dúvidas, com a fonte."""
    fontes = {t["id"]: t["fonte"] for t in trechos}
    citadas = {fontes[r]["id"]: fontes[r] for item in itens for r in item["trechos"]}
    linhas = [" ".join(item["conclusao"] for item in itens)]
    for fonte in citadas.values():
        orgao = "SEL-DF" if "SEL-DF" in fonte["instituicao"] else fonte["instituicao"]
        documento = f" · documento da equipe: {DOCUMENTO_F029}" if fonte["id"] == "F029" else ""
        linhas.append(f"Fonte {fonte['id']} · {orgao} · {fonte['url']}{documento}")
    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modelo", help="modelo do Ollama (padrão: PONTOATIVO_OLLAMA_MODEL)")
    parser.add_argument("--modelo-validacao", help="modelo do revisor (padrão: o mesmo de --modelo)")
    parser.add_argument("--so-regras", action="store_true",
                        help="Validação só por regras, sem a revisão semântica do modelo")
    parser.add_argument("--limiar", type=float, default=0.6, help="distância máxima aceita pela Pesquisa")
    parser.add_argument("--saida", type=Path, default=RAIZ / "experimentos" / "agentes" /
                        "validacao-parque-da-cidade-20261119.json")
    args = parser.parse_args()

    settings = Settings.from_env()
    modelo = args.modelo or settings.ollama_model
    cliente = OllamaClient(settings.ollama_base_url, modelo, max(settings.ollama_timeout_seconds, 600),
                           num_ctx=settings.ollama_num_ctx, num_predict=1600,
                           keep_alive=settings.ollama_keep_alive)
    modelo_validacao = args.modelo_validacao or modelo
    revisor = OllamaClient(settings.ollama_base_url, modelo_validacao, max(settings.ollama_timeout_seconds, 600),
                           num_ctx=settings.ollama_num_ctx, num_predict=1600,
                           keep_alive=settings.ollama_keep_alive)
    rascunho = json.loads(RASCUNHO_INVENTADO.read_text(encoding="utf-8"))["itens"]
    eventos = []
    fluxo = FluxoDocumental(
        AgentePesquisa(BuscaLexicaCorpus(CORPUS), max_distance=args.limiar, top_k=3),
        AnaliseComPrimeiroRascunhoPreparado(cliente, rascunho),
        orcamento_segundos=1800, validacao=AgenteValidacao(None if args.so_regras else revisor), max_correcoes=2,
        registrar=eventos.append,
    )
    resposta, segundos = fluxo.responder(PERGUNTA)

    primeira = next(e for e in eventos if e["etapa"] == "analise_para_validacao")
    primeira["origem"] = "rascunho preparado à mão com etapa inventada (injetado na 1ª chamada)"
    ultima = [e for e in eventos if e["etapa"] == "validacao"][-1]
    aprovado = ultima.get("parecer", {}).get("aprovado", False)
    final_itens = [e for e in eventos if e["etapa"] == "analise_para_validacao"][-1]["itens"]
    trechos = [t for e in eventos if e["etapa"] == "pesquisa_para_analise" for t in e["resultado"]["trechos"]]
    if aprovado and resposta.mode == "rag":
        comunicacao = comunicar(final_itens, trechos)
        eventos.append({"etapa": "validacao_para_comunicacao", "itens_aprovados": final_itens})
        eventos.append({"etapa": "comunicacao", "resposta": comunicacao})
    else:
        comunicacao = resposta.answer

    registro = {
        "executado_em": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
        "pergunta": PERGUNTA,
        "modelo_analise": modelo,
        "modelo_validacao": None if args.so_regras else modelo_validacao,
        "pesquisa": "busca lexical no corpus do protótipo (sem embeddings)",
        "simulado": "somente o primeiro rascunho da Análise (preparado à mão)",
        "eventos": eventos,
        "resposta_coordenador": resposta.to_dict(),
        "resposta_comunicacao": comunicacao,
        "recuperacao_segundos": segundos,
    }
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.saida.with_suffix(".txt").write_text(_resumo(eventos, comunicacao) + "\n", encoding="utf-8")
    print(_resumo(eventos, comunicacao))
    print(f"\nRegistro da troca entre os agentes: {args.saida}")
    return 0 if aprovado else 1


def _resumo(eventos, comunicacao):
    linhas = [f"Pergunta: {PERGUNTA}", ""]
    for e in eventos:
        etapa = e["etapa"]
        if etapa == "interpretacao_para_pesquisa":
            linhas.append("[Interpretação → Pesquisa] dúvidas: " + " | ".join(e["duvidas"]))
        elif etapa == "pesquisa_para_analise":
            r = e["resultado"]
            linhas.append(f"[Pesquisa → Análise] {r['status']}: " + ", ".join(
                f"{t['id']}={t['chunk_id']} (dist. {t['distancia']})" for t in r["trechos"]))
        elif etapa == "analise_para_validacao":
            origem = f" ({e['origem']})" if "origem" in e else ""
            linhas.append(f"[Análise → Validação]{origem}")
            linhas += [f"   {i}. ({it['estado']}) {it['conclusao']} {it['trechos']}"
                       for i, it in enumerate(e["itens"], 1)]
        elif etapa == "validacao":
            if "erro" in e:
                linhas.append(f"[Validação, rodada {e['rodada']}] erro: {e['erro']}")
                continue
            p = e["parecer"]
            linhas.append(f"[Validação, rodada {e['rodada']}] aprovado={p['aprovado']} revisão={p['revisao']}")
            linhas += [f"   - item {x['item']} ({x['criterio']}): \"{x['trecho_rascunho']}\"" for x in p["problemas"]]
        elif etapa == "validacao_para_analise":
            linhas.append("[Validação → Análise] trechos para corrigir:")
            linhas += [f"   - {f}" for f in e["feedback"]]
        elif etapa == "validacao_para_pesquisa":
            linhas.append(f"[Validação → Pesquisa] consulta complementar: {e['acao']['consulta']}")
        elif etapa == "comunicacao":
            linhas.append("[Validação → Comunicação] itens aprovados")
    linhas += ["", "Resposta (Comunicação):", comunicacao]
    return "\n".join(linhas)


if __name__ == "__main__":
    raise SystemExit(main())
