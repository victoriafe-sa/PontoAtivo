"""Compara o mesmo LLM respondendo com e sem a base do RAG.

Sem RAG, o modelo recebe só a pergunta, em dois cenários: com uma instrução
simples, como alguém usaria um chatbot comum, e com uma instrução cautelosa,
que permite dizer que não sabe. Com RAG, a pergunta passa pelo pipeline
completo: recuperação, geração estruturada e citações.

As respostas são gravadas lado a lado com a referência de cada pergunta, para
revisão humana. Este módulo não dá notas: julgar se uma resposta está certa
exige ler a fonte.

Uso:
    python -m pontoativo_rag.comparacao
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Protocol

from .avaliacao import EvaluationQuestion, load_questions
from .configuracao import Settings
from .geracao import GroundedAnswer

BASELINE_SYSTEMS = {
    "simples": (
        "Você é um assistente sobre esporte, lazer e acessibilidade no Distrito "
        "Federal. Responda em português, de forma objetiva, em até cinco frases."
    ),
    "cautelosa": (
        "Você é um assistente sobre esporte, lazer e acessibilidade no Distrito "
        "Federal. Responda em português, de forma objetiva, em até cinco frases. "
        "Se não souber a resposta, diga que não sabe."
    ),
}
BASELINE_TITLES = {"simples": "Sem RAG, instrução simples", "cautelosa": "Sem RAG, instrução cautelosa"}
BASELINE_OPTIONS = {"temperature": 0}


class TextModel(Protocol):
    def complete(self, system: str, user: str, **kwargs: Any) -> str: ...


RagAnswer = Callable[[str], GroundedAnswer]


def compare_question(
    question: EvaluationQuestion, model: TextModel, rag_answer: RagAnswer
) -> dict[str, Any]:
    baselines = {}
    for name, system in BASELINE_SYSTEMS.items():
        start = time.perf_counter()
        reply = model.complete(system, question.pergunta, options=BASELINE_OPTIONS)
        baselines[name] = {
            "resposta": reply.strip(), "tempo_s": round(time.perf_counter() - start, 1)
        }

    start = time.perf_counter()
    result = rag_answer(question.pergunta)
    rag_seconds = time.perf_counter() - start

    return {
        "id": question.id,
        "categoria": question.categoria,
        "pergunta": question.pergunta,
        "respondivel": question.respondivel,
        "referencia": question.referencia,
        "fontes_relevantes": list(question.fontes_relevantes),
        "sem_rag": baselines,
        "com_rag": {
            "modo": result.mode,
            "resposta": result.answer.strip(),
            "fontes_citadas": list(dict.fromkeys(chunk.source_id for chunk in result.cited)),
            "titulos_citados": list(dict.fromkeys(chunk.title for chunk in result.cited)),
            "tempo_s": round(rag_seconds, 1),
        },
    }


def render_markdown(meta: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Respostas com e sem RAG",
        "",
        f"- Executado em: {meta['executado_em']}",
        f"- Modelo: `{meta['modelo_llm']}` (o mesmo nos dois casos)",
        f"- Perguntas: {len(rows)} ({', '.join(meta['arquivos_perguntas'])})",
        *[f"- {BASELINE_TITLES[name]}: \"{system}\"" for name, system in BASELINE_SYSTEMS.items()],
        "",
    ]
    for row in rows:
        com = row["com_rag"]
        fontes = ", ".join(com["fontes_citadas"]) or "nenhuma"
        lines += [f"## {row['id']}. {row['pergunta']}", "", f"**Referência:** {row['referencia']}", ""]
        for name, sem in row["sem_rag"].items():
            lines += [
                f"**{BASELINE_TITLES[name]}** ({sem['tempo_s']} s)",
                "",
                *[f"> {line}" if line else ">" for line in sem["resposta"].splitlines()],
                "",
            ]
        lines += [
            f"**Com RAG** ({com['tempo_s']} s, modo `{com['modo']}`, fontes: {fontes})",
            "",
            *[f"> {line}" if line else ">" for line in com["resposta"].splitlines()],
            "",
        ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compara respostas com e sem RAG.")
    parser.add_argument(
        "--perguntas", type=Path, action="append", default=None,
        help="arquivo JSONL de perguntas (pode repetir); padrão: avaliação + extras",
    )
    parser.add_argument("--rotulo", default="", help="sufixo do nome dos arquivos gerados")
    args = parser.parse_args(argv)

    from .consulta import answer_question, build_pipeline
    from .geracao import OllamaClient

    settings = Settings.from_env()
    paths = args.perguntas or [
        settings.data_dir / "perguntas_avaliacao.jsonl",
        settings.data_dir / "perguntas_comparacao_extras.jsonl",
    ]
    questions = [question for path in paths for question in load_questions(path)]
    retriever, generator = build_pipeline(settings)
    model = OllamaClient(
        settings.ollama_base_url, settings.ollama_model, settings.ollama_timeout_seconds,
        num_ctx=settings.ollama_num_ctx, num_predict=settings.ollama_num_predict,
        keep_alive=settings.ollama_keep_alive,
    )

    def rag_answer(text: str) -> GroundedAnswer:
        return answer_question(settings, retriever, generator, text)[0]

    rows = []
    started = time.perf_counter()
    for question in questions:
        row = compare_question(question, model, rag_answer)
        rows.append(row)
        print(
            f"{row['id']} sem_rag="
            + "/".join(f"{r['tempo_s']}s" for r in row["sem_rag"].values())
            + f" com_rag={row['com_rag']['tempo_s']}s modo={row['com_rag']['modo']} "
            f"fontes={row['com_rag']['fontes_citadas']}",
            flush=True,
        )

    now = datetime.now()
    meta = {
        "executado_em": now.isoformat(timespec="seconds"),
        "modelo_llm": settings.ollama_model,
        "arquivos_perguntas": [path.name for path in paths],
        "duracao_total_s": round(time.perf_counter() - started, 1),
    }
    suffix = f"_{args.rotulo}" if args.rotulo else ""
    stem = settings.evidence_dir / f"comparacao_sem_rag_{now:%Y%m%d_%H%M%S}{suffix}"
    settings.evidence_dir.mkdir(parents=True, exist_ok=True)
    with stem.with_suffix(".jsonl").open("w", encoding="utf-8") as file:
        file.write(json.dumps({"meta": meta}, ensure_ascii=False) + "\n")
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    stem.with_suffix(".md").write_text(render_markdown(meta, rows), encoding="utf-8")
    print(f"\nRespostas: {stem.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
