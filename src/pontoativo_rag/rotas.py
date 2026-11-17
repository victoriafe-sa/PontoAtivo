"""Compara modelos na barra do mapa: acerto da rota e tempo por pergunta.

A barra do mapa só classifica a pergunta (mapa, documentos, dúvidas, fora do
escopo ou esclarecer). Este teste ajuda a escolher PONTOATIVO_OLLAMA_MODEL_MAPA:
um modelo menor responde mais rápido, mas precisa acertar as rotas.

Uso (no computador da demonstração, com os modelos já baixados no Ollama):

    python -m pontoativo_rag.rotas --modelos gemma4:12b qwen3:4b
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from .configuracao import Settings


def load_questions(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for row in rows:
        if not {"id", "pergunta", "rota"} <= row.keys():
            raise ValueError(f"Pergunta incompleta em {path}: {row}")
    return rows


def run_model(chat, questions: list[dict], clock=time.perf_counter) -> dict:
    """Classifica cada pergunta com o modelo do ``chat`` e mede o tempo."""
    results = []
    for row in questions:
        start = clock()
        try:
            route = chat.classify(row["pergunta"])["rota"]
            error = ""
        except Exception as exc:  # resposta fora do formato conta como erro
            route, error = "erro", type(exc).__name__
        elapsed = clock() - start
        results.append({**row, "obtida": route, "ok": route == row["rota"], "tempo_s": elapsed, "erro": error})
    times = [r["tempo_s"] for r in results]
    return {
        "acertos": sum(r["ok"] for r in results),
        "total": len(results),
        "tempo_medio_s": sum(times) / len(times) if times else 0.0,
        "tempo_max_s": max(times, default=0.0),
        "respostas": results,
    }


def render_markdown(runs: dict[str, dict], when: str) -> str:
    lines = [
        "# Rotas da barra do mapa: comparação de modelos",
        "",
        f"Execução: {when}. Cada modelo classificou as mesmas perguntas, uma vez.",
        "",
        "| Modelo | Acertos | Tempo médio | Tempo máximo |",
        "|---|---:|---:|---:|",
    ]
    for model, run in runs.items():
        lines.append(f"| `{model}` | {run['acertos']}/{run['total']} | "
                     f"{run['tempo_medio_s']:.1f} s | {run['tempo_max_s']:.1f} s |")
    for model, run in runs.items():
        wrong = [r for r in run["respostas"] if not r["ok"]]
        lines += ["", f"## Erros de `{model}`", ""]
        if not wrong:
            lines.append("Nenhum.")
        for r in wrong:
            detail = f" ({r['erro']})" if r["erro"] else ""
            lines.append(f"- {r['id']} \"{r['pergunta']}\": esperado `{r['rota']}`, obtido `{r['obtida']}`{detail}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    from .web import Chat

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--modelos", nargs="+", help="modelos do Ollama a comparar (padrão: o modelo do mapa configurado)")
    parser.add_argument("--perguntas", type=Path, default=None, help="arquivo JSONL com id, pergunta e rota")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    questions = load_questions(args.perguntas or settings.questions_dir / "rotas.jsonl")
    runs = {}
    for model in args.modelos or [settings.map_model]:
        print(f"Testando {model} em {len(questions)} perguntas…", flush=True)
        chat = Chat(replace(settings, ollama_map_model=model))
        try:
            chat.classify("aquecimento")  # carrega o modelo antes de medir
        except Exception:
            pass
        runs[model] = run = run_model(chat, questions)
        print(f"  {run['acertos']}/{run['total']} acertos · {run['tempo_medio_s']:.1f} s por pergunta", flush=True)

    when = datetime.now().strftime("%d/%m/%Y %H:%M")
    path = settings.evidence_dir / f"rotas_{datetime.now():%Y%m%d_%H%M%S}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(runs, when), encoding="utf-8")
    print(f"Relatório: {path}")


if __name__ == "__main__":
    main()
