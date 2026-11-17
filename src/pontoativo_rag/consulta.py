"""Consulta interativa pelo terminal.

Exemplos (a partir da pasta do projeto):

    python -m pontoativo_rag.consulta
    python -m pontoativo_rag.consulta --pergunta "O PEC de Ceilândia é acessível?"
    python -m pontoativo_rag.consulta --sem-geracao        # só recuperação
    python -m pontoativo_rag.consulta --regiao Ceilândia --top-k 3
"""

from __future__ import annotations

import argparse
import json
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path

from .configuracao import Settings
from .geracao import AnswerGenerator, GroundedAnswer, OllamaClient
from .recuperacao import Retriever


EXIT_WORDS = {"sair", "exit", "quit", "fim"}
LINE = "─" * 72


def build_pipeline(
    settings: Settings, *, use_llm: bool = True, reranker: str = "hibrido"
) -> tuple[Retriever, AnswerGenerator]:
    """Monta recuperador e gerador com a configuração do projeto."""
    from .armazenamento import ChromaStore
    from .embeddings import EmbeddingProvider

    store = ChromaStore(
        settings.vector_db_dir,
        settings.collection_name,
        embedding_model=settings.embedding_model,
    )
    if store.count() == 0:
        raise SystemExit(
            "O banco vetorial está vazio. Execute antes: python -m pontoativo_rag.ingestao"
        )
    retriever = Retriever(
        EmbeddingProvider(settings.embedding_model), store, top_k=settings.top_k,
        reranker=reranker,
    )
    llm = (
        OllamaClient(
            settings.ollama_base_url,
            settings.ollama_model,
            settings.ollama_timeout_seconds,
            num_ctx=settings.ollama_num_ctx,
            num_predict=settings.ollama_num_predict,
            keep_alive=settings.ollama_keep_alive,
        )
        if use_llm
        else None
    )
    return retriever, AnswerGenerator(
        llm,
        max_distance=settings.max_distance,
        structured=settings.structured_answers,
        max_attempts=settings.max_generation_attempts,
    )


def format_answer(result: GroundedAnswer, retrieval_seconds: float) -> str:
    wrap = lambda text, indent="   ": textwrap.fill(  # noqa: E731
        " ".join(text.split()), width=88, initial_indent=indent, subsequent_indent=indent
    )
    lines = [LINE, "1. PERGUNTA RECEBIDA", wrap(result.question), ""]
    lines.append(
        f"2. TRECHOS RECUPERADOS ({len(result.retrieved)}; "
        f"distância cosseno — menor = mais próximo; recuperação em {retrieval_seconds:.2f} s)"
    )
    if not result.retrieved:
        lines.append("   (nenhum trecho)")
    for number, chunk in enumerate(result.retrieved, start=1):
        page = f" | p. {chunk.pages}" if chunk.pages else ""
        lines.append(f"   [F{number}] {chunk.source_id}{page} | distância {chunk.distance:.3f}")
        lines.append(f"        {chunk.title}")
        if chunk.section:
            lines.append(f"        seção: {chunk.section}")
        lines.append(f"        chunk {chunk.chunk_id}")
        if chunk.filter_metadata_missing:
            lines.append("        (sem metadado de região; mantido para não ocultar evidência)")
        lines.append(wrap(chunk.text[:320] + ("…" if len(chunk.text) > 320 else ""), "        "))
    lines.append("")
    titles = {
        "rag": f"3. RESPOSTA GERADA (modelo {result.model}, {result.generation_seconds:.1f} s)",
        "abstencao": "3. RESPOSTA — ABSTENÇÃO (evidências insuficientes; LLM não consultado)",
        "recuperacao_sem_geracao": "3. RECUPERAÇÃO SEM GERAÇÃO (modo de diagnóstico)",
    }
    lines.append(titles[result.mode])
    lines.extend(wrap(paragraph) for paragraph in result.answer.split("\n") if paragraph.strip())
    lines.append("")
    lines.append("4. REFERÊNCIAS UTILIZADAS")
    references = result.cited if result.mode == "rag" else []
    if references:
        for chunk in references:
            ref = result.retrieved.index(chunk) + 1
            lines.append(f"   [F{ref}] {chunk.reference()}")
    elif result.mode == "recuperacao_sem_geracao":
        lines.append("   Sem resposta redigida; consulte as fontes dos trechos acima.")
    else:
        lines.append("   Nenhuma referência citada.")
    lines.append("")
    lines.append("5. ALERTAS")
    lines.extend(f"   ! {warning}" for warning in result.warnings)
    lines.append(LINE)
    return "\n".join(lines)


def log_query(
    settings: Settings, result: GroundedAnswer, retrieval_seconds: float, output: Path
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "embedding_model": settings.embedding_model,
        "top_k": settings.top_k,
        "max_distance": settings.max_distance,
        "retrieval_seconds": round(retrieval_seconds, 3),
        **result.to_dict(),
    }
    with output.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def answer_question(
    settings: Settings,
    retriever: Retriever,
    generator: AnswerGenerator,
    question: str,
    *,
    top_k: int | None = None,
    filters: dict[str, str] | None = None,
) -> tuple[GroundedAnswer, float]:
    start = time.perf_counter()
    chunks = retriever.search(question, top_k=top_k, filters=filters)
    retrieval_seconds = time.perf_counter() - start
    return generator.generate(question, chunks), retrieval_seconds


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Consulta ao PontoAtivo RAG.")
    parser.add_argument("--pergunta", help="faz uma única pergunta e encerra")
    parser.add_argument("--top-k", type=int, default=None, help="número de trechos (padrão 5)")
    parser.add_argument("--regiao", default=None, help="filtra por região administrativa")
    parser.add_argument("--tipo", default=None, help="filtra por tipo de documento (pdf/html)")
    parser.add_argument("--fonte", default=None, help="filtra por source_id")
    parser.add_argument(
        "--atualidade", choices=("atual", "em_revisao", "antiga", "desconhecida"),
        default=None, help="filtra pelo status temporal da fonte",
    )
    parser.add_argument(
        "--reranker", choices=("hibrido", "vetorial"), default="hibrido",
        help="estratégia de ordenação dos resultados",
    )
    parser.add_argument(
        "--sem-geracao", action="store_true", help="modo de diagnóstico: só recuperação"
    )
    parser.add_argument(
        "--sem-registro", action="store_true", help="não grava evidencias/consultas.jsonl"
    )
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    retriever, generator = build_pipeline(
        settings, use_llm=not args.sem_geracao, reranker=args.reranker
    )
    filters = {
        key: value for key, value in {
            "administrative_region": args.regiao,
            "source_type": args.tipo,
            "source_id": args.fonte,
            "freshness_status": args.atualidade,
        }.items() if value
    } or None
    log_path = settings.evidence_dir / "consultas.jsonl"

    def run(question: str) -> None:
        try:
            result, seconds = answer_question(
                settings, retriever, generator, question, top_k=args.top_k, filters=filters
            )
        except ValueError as error:
            print(f"Pergunta inválida: {error}")
            return
        print(format_answer(result, seconds))
        if not args.sem_registro:
            log_query(settings, result, seconds, log_path)

    if args.pergunta:
        run(args.pergunta)
        return 0

    print("PONTOATIVO — CONSULTA INTELIGENTE")
    mode = "recuperação sem geração" if args.sem_geracao else f"RAG com {settings.ollama_model}"
    print(f"Modo: {mode}. Digite 'sair' (ou Ctrl+C) para encerrar.\n")
    while True:
        try:
            question = input("Digite sua pergunta:\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando. Até logo!")
            return 0
        if question.lower() in EXIT_WORDS:
            print("Encerrando. Até logo!")
            return 0
        if question:
            run(question)
            print()


if __name__ == "__main__":
    raise SystemExit(main())
