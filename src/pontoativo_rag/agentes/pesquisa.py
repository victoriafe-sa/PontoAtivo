"""Agente de Pesquisa: recebe uma ação e devolve trechos das fontes, com a origem.

Entrada (a ação, vinda do agente de Interpretação), em JSON:

    {"consulta": "faltas graves nos Centros Olímpicos",   # obrigatório
     "pergunta_original": "o que dá expulsão no COP?",    # opcional, só repassada
     "tipo": "buscar_regra",                                # opcional, só repassado
     "regiao": "Ceilândia"}                                 # opcional: filtro por região

Saída (para os agentes de Análise e Validação):

    {"agente": "pesquisa",
     "acao": {...a ação recebida...},
     "status": "encontrado" | "sem_evidencia",
     "trechos": [{"id": "T1", "texto": "...", "distancia": 0.08,
                  "fonte": {"id": "DOC-003", "titulo": "...", "instituicao": "...",
                            "url": "...", "paginas": "5", "secao": "...",
                            "regiao": "...", "atualidade": "..."}}],
     "motivo": "...",          # por que não há evidência (só em sem_evidencia)
     "limiar": 0.12,           # distância máxima usada para aceitar um trecho
     "descartados": 2,         # trechos recuperados que ficaram fora do limiar
     "segundos": 0.4}

O agente não escreve resposta: só busca e filtra. Um trecho só entra em
``trechos`` se passar na mesma regra de evidência que o gerador usa
(``geracao.trecho_relevante``); assim, "sem_evidencia" aqui significa que o
sistema também se absteria. Os IDs T1, T2... são os que a Análise deve citar.

Uso, com o índice pronto (``python -m pontoativo_rag.ingestao``):

    python -m pontoativo_rag.agentes.pesquisa "faltas graves nos Centros Olímpicos"
    python -m pontoativo_rag.agentes.pesquisa --acao acao.json --saida resultado.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Protocol, Sequence

from ..geracao import trecho_relevante
from ..recuperacao import RetrievedChunk


class Buscador(Protocol):
    def search(
        self, question: str, top_k: int | None = None, filters: dict[str, str] | None = None
    ) -> list[RetrievedChunk]: ...


def _fonte(chunk: RetrievedChunk) -> dict[str, str]:
    return {
        "id": chunk.source_id,
        "titulo": chunk.title,
        "instituicao": chunk.institution,
        "url": chunk.location,
        "paginas": chunk.pages,
        "secao": chunk.section,
        "regiao": chunk.administrative_region,
        "atualidade": chunk.freshness_status,
    }


def validar_acao(acao: Any) -> dict[str, Any]:
    """Confere a ação recebida; aceita só os campos do contrato."""
    if not isinstance(acao, dict):
        raise ValueError("A ação deve ser um objeto JSON.")
    consulta = acao.get("consulta")
    if not isinstance(consulta, str) or not consulta.strip():
        raise ValueError('A ação precisa do campo "consulta" com o texto a buscar.')
    for campo in ("pergunta_original", "tipo", "regiao"):
        if acao.get(campo) is not None and not isinstance(acao[campo], str):
            raise ValueError(f'O campo "{campo}" deve ser texto.')
    return {**acao, "consulta": consulta.strip()}


class AgentePesquisa:
    """Busca trechos para uma ação e devolve só os que servem de evidência."""

    nome = "pesquisa"

    def __init__(
        self,
        buscador: Buscador,
        *,
        max_distance: float,
        distance_scale: float = 1.0,
        top_k: int = 4,
    ) -> None:
        self.buscador = buscador
        self.max_distance = max_distance
        self.distance_scale = distance_scale
        self.top_k = top_k

    def executar(self, acao: dict[str, Any]) -> dict[str, Any]:
        acao = validar_acao(acao)
        inicio = time.perf_counter()
        filtros = {"administrative_region": acao["regiao"]} if acao.get("regiao") else None
        recuperados: Sequence[RetrievedChunk] = self.buscador.search(
            acao["consulta"], top_k=self.top_k, filters=filtros
        )
        aceitos = [c for c in recuperados if trecho_relevante(c, self.max_distance, self.distance_scale)]
        trechos = [
            {
                "id": f"T{i}",
                "texto": chunk.text,
                "distancia": round(chunk.distance, 4),
                "fonte": _fonte(chunk),
            }
            for i, chunk in enumerate(aceitos, start=1)
        ]
        resultado: dict[str, Any] = {
            "agente": self.nome,
            "acao": acao,
            "status": "encontrado" if trechos else "sem_evidencia",
            "trechos": trechos,
            "limiar": self.max_distance,
            "descartados": len(recuperados) - len(aceitos),
            "segundos": round(time.perf_counter() - inicio, 2),
        }
        if not trechos:
            if recuperados:
                mais_perto = min(c.distance for c in recuperados)
                resultado["motivo"] = (
                    f"Nenhum dos {len(recuperados)} trechos recuperados ficou perto o bastante "
                    f"da consulta (melhor distância {mais_perto:.3f}; limiar {self.max_distance:.3f})."
                )
            else:
                resultado["motivo"] = "A busca não retornou nenhum trecho."
        return resultado


def criar_agente(settings=None) -> AgentePesquisa:
    """Monta o agente com o índice e a configuração do projeto."""
    from ..configuracao import Settings
    from ..consulta import build_pipeline

    settings = settings or Settings.from_env()
    buscador, _ = build_pipeline(settings, use_llm=False)
    return AgentePesquisa(
        buscador,
        max_distance=settings.max_distance,
        distance_scale=settings.distance_scale,
        top_k=settings.top_k,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agente de Pesquisa do PontoAtivo.")
    parser.add_argument("consulta", nargs="?", help="texto a buscar (atalho para uma ação simples)")
    parser.add_argument("--acao", type=Path, help="arquivo JSON com a ação completa")
    parser.add_argument("--regiao", help="filtra por região administrativa")
    parser.add_argument("--saida", type=Path, help="grava o resultado neste arquivo JSON")
    args = parser.parse_args(argv)

    if args.acao:
        acao = json.loads(args.acao.read_text(encoding="utf-8"))
    elif args.consulta:
        acao = {"consulta": args.consulta}
        if args.regiao:
            acao["regiao"] = args.regiao
    else:
        parser.error("informe a consulta ou --acao arquivo.json")

    resultado = criar_agente().executar(acao)
    texto = json.dumps(resultado, ensure_ascii=False, indent=2)
    if args.saida:
        args.saida.write_text(texto + "\n", encoding="utf-8")
        print(f"{resultado['status']}: {len(resultado['trechos'])} trecho(s). Resultado em {args.saida}")
    else:
        print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
