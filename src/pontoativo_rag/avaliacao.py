"""Avaliação reproduzível do PontoAtivo RAG com perguntas e gabarito.

    python -m pontoativo_rag.avaliacao                 # RAG completo (Ollama)
    python -m pontoativo_rag.avaliacao --sem-geracao   # só recuperação

Gera ``experimentos/evidencias/avaliacao_<data>.jsonl`` (registro completo de cada
pergunta) e ``experimentos/evidencias/avaliacao_<data>.md`` (relatório legível). Nenhuma
métrica é estimada: tudo é calculado a partir das execuções registradas. A
fidelidade da resposta ao contexto é deixada para revisão humana.
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .configuracao import Settings
from .geracao import _SENTENCE_BREAK, GroundedAnswer


MIN_RECALL_AT_K = 0.90
MIN_SOURCE_HIT_RATE = 0.95
MAX_FALSE_ABSTENTIONS = 0
MAX_INVALID_CITATIONS = 0
MIN_CITATION_COVERAGE = 0.80
MIN_FACTUAL_SUPPORT = 0.80
MAX_UNSUPPORTED_CLAIMS = 0


@dataclass(frozen=True, slots=True)
class EvaluationQuestion:
    id: str
    categoria: str
    pergunta: str
    respondivel: bool
    fontes_relevantes: tuple[str, ...]
    referencia: str = ""


def load_questions(path: Path) -> list[EvaluationQuestion]:
    questions = []
    with path.open(encoding="utf-8") as file:
        for line in file:
            if line.strip():
                data = json.loads(line)
                data["fontes_relevantes"] = tuple(data.get("fontes_relevantes", ()))
                questions.append(EvaluationQuestion(**data))
    return questions


def unique_sources(result: GroundedAnswer) -> list[str]:
    return list(dict.fromkeys(chunk.source_id for chunk in result.retrieved))


def recall_at_k(relevant: tuple[str, ...], retrieved: list[str]) -> float | None:
    """Fração das fontes relevantes presentes entre as recuperadas (None se não há gabarito)."""
    if not relevant:
        return None
    return len(set(relevant) & set(retrieved)) / len(set(relevant))


def abstained(result: GroundedAnswer) -> bool:
    return result.mode == "abstencao" or result.model_abstained


def _answer_sentences(answer: str) -> list[str]:
    sentences: list[str] = []
    for line in answer.splitlines():
        line = line.strip()
        if not line or line.startswith("[Resposta truncada"):
            continue
        if re.fullmatch(r"(?:\[\s*F\d+\s*\]\s*)+", line) and sentences:
            sentences[-1] += " " + line
            continue
        sentences.extend(
            part.strip()
            # Mesma regra do gerador: "V. Telebrasília" não encerra a frase.
            for part in _SENTENCE_BREAK.split(line)
            if part.strip()
        )
    return sentences


def _singular(token: str) -> str:
    """Reduz plurais regulares do português ao singular, sem acentos.

    É aplicado aos dois lados da comparação, então "alunos" e "aluno" contam
    como o mesmo termo. Não é um lematizador completo: cobre só as formas
    regulares (-s, -es, -ões, -ães, -ais, -éis, -óis).
    """
    if len(token) < 5 or not token.endswith("s") or token.isdigit():
        return token
    for plural, singular in (("oes", "ao"), ("aes", "ao"), ("ais", "al"),
                             ("eis", "el"), ("ois", "ol")):
        if token.endswith(plural):
            return token[: -len(plural)] + singular
    if token.endswith(("res", "zes", "ses")) and len(token) > 5:
        return token[:-2]
    if token.endswith(("as", "es", "os", "us")):
        return token[:-1]
    return token


def _terms(value: str) -> set[str]:
    # Minúsculas antes da regex: sem isso, "Alunos" virava "lunos".
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().casefold()
    )
    stopwords = {
        "para", "como", "qual", "quais", "sobre", "esse", "essa",
        "documento", "documentos", "fonte", "fontes", "citado", "citada",
        "citar", "citacao", "informacao", "informacoes", "segundo",
        "conforme", "tambem", "alem", "assim", "resumo",
    }
    terms = {
        _singular(token)
        for token in re.findall(r"[a-z0-9]{4,}", normalized)
        if token not in stopwords
    }
    # Endereços do DF ("SQN 103", "EQN 112/113") são o fato da frase, mas têm
    # partes curtas que a regra acima descarta; entram como um termo só.
    terms.update(
        letters + number
        for letters, number in re.findall(r"\b([a-z]{2,5})\s?(\d{1,4}(?:/\d{1,4})?)\b", normalized)
    )
    # Números listados à parte ("SQNW, quadras 108, 109 e 111"; "13.672 vagas")
    # também são fatos. Um número que não está na fonte conta contra a frase.
    terms.update(re.findall(r"\b\d{3,}\b", normalized))
    return terms


def _is_non_factual_sentence(sentence: str) -> bool:
    """Ignora metadados de citação e cabeçalhos sem uma afirmação."""
    normalized = sentence.strip().casefold()
    if normalized.endswith(":"):
        return True
    return bool(
        re.match(
            r"^(?:citei?|citado|fontes?|referências?|documentos?)\b",
            normalized,
        )
    )


def factual_answer_metrics(result: GroundedAnswer) -> dict[str, Any]:
    """Mede suporte textual das afirmações e cobertura das citações."""
    if result.mode != "rag" or result.model_abstained:
        return {
            "citation_coverage": None,
            "factual_support": None,
            "unsupported_claims": None,
        }
    sentences = _answer_sentences(result.answer)
    cited_text = " ".join(chunk.text for chunk in result.cited)
    factual_sentences = [
        sentence
        for sentence in sentences
        if _terms(sentence) and not _is_non_factual_sentence(sentence)
    ]
    cited_sentence_count = sum(
        bool(re.search(r"\[\s*F\d+\s*\]", sentence, re.IGNORECASE))
        for sentence in factual_sentences
    )
    def sufficiently_supported(sentence: str) -> bool:
        claim_terms = _terms(re.sub(r"\[\s*F\d+\s*\]", "", sentence))
        if not claim_terms:
            return True
        overlap_terms = claim_terms & _terms(cited_text)
        # Uma única palavra compartilhada não prova suporte. Exigimos pelo
        # menos dois termos substantivos e uma fração mínima da afirmação.
        required = max(2, (len(claim_terms) + 3) // 4)
        return len(overlap_terms) >= required

    supported = sum(sufficiently_supported(sentence) for sentence in factual_sentences)
    return {
        "citation_coverage": round(
            cited_sentence_count / len(factual_sentences), 3
        ) if factual_sentences else 1.0,
        "factual_support": round(
            supported / len(factual_sentences), 3
        ) if factual_sentences else 1.0,
        "unsupported_claims": max(0, len(factual_sentences) - supported),
    }


def score_question(
    question: EvaluationQuestion,
    result: GroundedAnswer,
    retrieval_seconds: float,
) -> dict[str, Any]:
    sources = unique_sources(result)
    irrelevant_top = [
        {"rank": index, "source_id": source_id}
        for index, source_id in enumerate(sources, start=1)
        if source_id not in question.fontes_relevantes
    ]
    cited_sources = list(dict.fromkeys(chunk.source_id for chunk in result.cited))
    did_abstain = abstained(result)
    best = min((chunk.distance for chunk in result.retrieved), default=None)
    return {
        "id": question.id,
        "categoria": question.categoria,
        "pergunta": question.pergunta,
        "respondivel": question.respondivel,
        "fontes_relevantes": list(question.fontes_relevantes),
        "referencia": question.referencia,
        "modo": result.mode,
        "fontes_recuperadas": sources,
        "fontes_irrelevantes_no_topo": irrelevant_top,
        "melhor_distancia": round(best, 4) if best is not None else None,
        "recall_at_k": recall_at_k(question.fontes_relevantes, sources),
        "absteve": did_abstain,
        "abstencao_correta": did_abstain if not question.respondivel else None,
        "falsa_abstencao": did_abstain if question.respondivel else None,
        "fontes_citadas": cited_sources,
        "citou_fonte_relevante": (
            bool(set(cited_sources) & set(question.fontes_relevantes))
            if question.respondivel and result.mode == "rag"
            else None
        ),
        "citacoes_invalidas": result.invalid_citations,
        **factual_answer_metrics(result),
        "tempo_recuperacao_s": round(retrieval_seconds, 3),
        "tempo_geracao_s": round(result.generation_seconds, 3),
        "tentativas_geracao": result.generation_attempts,
        "fidelidade": "pendente de revisão humana",
        "resultado": result.to_dict(),
    }


def load_evaluation(path: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Carrega o JSONL produzido por uma avaliação."""
    with path.open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file if line.strip()]
    if not records or "meta" not in records[0]:
        raise ValueError(f"Arquivo de avaliação inválido: {path}")
    return records[0]["meta"], records[0]["resumo"], records[1:]


def compare_evaluations(
    previous: tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]],
    current: tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]],
) -> dict[str, Any]:
    """Compara duas avaliações e identifica irrelevantes novos no topo."""
    _, previous_summary, previous_rows = previous
    _, current_summary, current_rows = current
    previous_by_id = {row["id"]: row for row in previous_rows}
    current_by_id = {row["id"]: row for row in current_rows}
    changes = []
    new_irrelevant = []
    for question_id, row in current_by_id.items():
        old = previous_by_id.get(question_id, {})
        relevant = set(row.get("fontes_relevantes", []))
        old_sources = old.get("fontes_recuperadas", [])
        current_sources = row.get("fontes_recuperadas", [])
        old_irrelevant = {
            source for source in old_sources[:3] if source not in set(old.get("fontes_relevantes", []))
        }
        current_irrelevant = {
            source for source in current_sources[:3] if source not in relevant
        }
        introduced = sorted(current_irrelevant - old_irrelevant)
        if introduced:
            new_irrelevant.append({"id": question_id, "fontes": introduced})
        changes.append(
            {
                "id": question_id,
                "recall_anterior": old.get("recall_at_k"),
                "recall_atual": row.get("recall_at_k"),
                "fontes_novas": sorted(set(current_sources) - set(old_sources)),
                "fontes_removidas": sorted(set(old_sources) - set(current_sources)),
                "irrelevantes_top3_atual": sorted(current_irrelevant),
                "novas_irrelevantes_top3": introduced,
            }
        )
    return {
        "resumo_anterior": previous_summary,
        "resumo_atual": current_summary,
        "variacao": {
            key: (
                round(current_summary.get(key) - previous_summary.get(key), 6)
                if isinstance(current_summary.get(key), (int, float))
                and isinstance(previous_summary.get(key), (int, float))
                else None
            )
            for key in ("recall_medio_at_k", "acerto_ao_menos_uma_fonte")
        },
        "novas_fontes_irrelevantes_no_top3": new_irrelevant,
        "mudancas_por_pergunta": changes,
    }


def render_comparison(comparison: dict[str, Any], previous_path: Path, current_path: Path) -> str:
    variation = comparison["variacao"]
    out = [
        "# Comparação da avaliação do PontoAtivo RAG",
        "",
        f"- **Avaliação anterior:** `{previous_path.name}`",
        f"- **Avaliação atual:** `{current_path.name}`",
        "",
        "## Resultado agregado",
        "",
        "| Métrica | Anterior | Atual | Variação |",
        "|---|---:|---:|---:|",
    ]
    for key in ("recall_medio_at_k", "acerto_ao_menos_uma_fonte"):
        old = comparison["resumo_anterior"].get(key)
        new = comparison["resumo_atual"].get(key)
        delta = variation.get(key)
        out.append(f"| {key} | {_fmt(old)} | {_fmt(new)} | {_fmt(delta)} |")
    new_irrelevant = comparison["novas_fontes_irrelevantes_no_top3"]
    out += [
        "",
        "## Verificação de fontes irrelevantes no topo",
        "",
        (
            "✅ Nenhuma fonte irrelevante nova apareceu entre as três primeiras posições."
            if not new_irrelevant
            else "⚠️ Foram encontradas novas fontes irrelevantes entre as três primeiras posições:"
        ),
    ]
    for item in new_irrelevant:
        out.append(f"- **{item['id']}:** {', '.join(item['fontes'])}")
    out += [
        "",
        "## Mudanças por pergunta",
        "",
        "| ID | Recall anterior | Recall atual | Irrelevantes no top 3 atual | Novas irrelevantes |",
        "|---|---:|---:|---|---|",
    ]
    for row in comparison["mudancas_por_pergunta"]:
        out.append(
            f"| {row['id']} | {_fmt(row['recall_anterior'])} | {_fmt(row['recall_atual'])} | "
            f"{', '.join(row['irrelevantes_top3_atual']) or 'nenhuma'} | "
            f"{', '.join(row['novas_irrelevantes_top3']) or 'nenhuma'} |"
        )
    return "\n".join(out) + "\n"


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    answerable = [row for row in rows if row["respondivel"]]
    unanswerable = [row for row in rows if not row["respondivel"]]
    rag_answerable = [row for row in answerable if row["modo"] == "rag" and not row["absteve"]]
    generation_was_attempted = any(row["modo"] == "rag" for row in rows)
    return {
        "perguntas": len(rows),
        "respondiveis": len(answerable),
        "sem_resposta_na_base": len(unanswerable),
        "recall_medio_at_k": _mean([row["recall_at_k"] for row in answerable]),
        "acerto_ao_menos_uma_fonte": _mean(
            [1.0 if row["recall_at_k"] else 0.0 for row in answerable]
        ),
        "abstencoes_corretas": sum(1 for row in unanswerable if row["absteve"]),
        "falsas_abstencoes": sum(1 for row in answerable if row["absteve"]),
        "respostas_citando_fonte_relevante": sum(
            1 for row in rag_answerable if row["citou_fonte_relevante"]
        ),
        "respostas_geradas_respondiveis": len(rag_answerable),
        "citacoes_invalidas": sum(len(row["citacoes_invalidas"]) for row in rows),
        "distancia_melhor_respondiveis": _mean(
            [row["melhor_distancia"] for row in answerable if row["melhor_distancia"] is not None]
        ),
        "distancia_melhor_sem_resposta": _mean(
            [row["melhor_distancia"] for row in unanswerable if row["melhor_distancia"] is not None]
        ),
        "tempo_medio_recuperacao_s": _mean([row["tempo_recuperacao_s"] for row in rows]),
        "tempo_medio_geracao_s": _mean(
            [row["tempo_geracao_s"] for row in rows if row["modo"] == "rag"]
        ),
        # Chamadas ao modelo por pergunta que chegou à geração (1 = sem revisão).
        "tentativas_medias_geracao": _mean(
            [row.get("tentativas_geracao", 0) for row in rows if row.get("tentativas_geracao")]
        ),
        "tempo_total_geracao_s": sum(row.get("tempo_geracao_s") or 0 for row in rows),
        "cobertura_media_citacoes": _mean(
            [row["citation_coverage"] for row in rows if row["citation_coverage"] is not None]
        ),
        "suporte_factual_medio": _mean(
            [row["factual_support"] for row in rows if row["factual_support"] is not None]
        ),
        "afirmacoes_sem_suporte": sum(
            row["unsupported_claims"] or 0 for row in rows
        ),
        "geracoes_incompletas": sum(
            generation_was_attempted and row["modo"] == "recuperacao_sem_geracao"
            for row in rows
        ),
    }


def quality_gate_failures(summary: dict[str, Any]) -> list[str]:
    """Retorna violações dos limites mínimos de qualidade da recuperação."""
    failures: list[str] = []
    recall = summary["recall_medio_at_k"]
    source_hit = summary["acerto_ao_menos_uma_fonte"]
    false_abstentions = summary["falsas_abstencoes"]
    invalid_citations = summary["citacoes_invalidas"]
    citation_coverage = summary.get("cobertura_media_citacoes")
    factual_support = summary.get("suporte_factual_medio")
    unsupported_claims = summary.get("afirmacoes_sem_suporte", 0)
    incomplete_generations = summary.get("geracoes_incompletas", 0)
    if recall is None or recall < MIN_RECALL_AT_K:
        failures.append(
            f"Recall@k {recall!r} abaixo do mínimo {MIN_RECALL_AT_K:.2f}"
        )
    if source_hit is None or source_hit < MIN_SOURCE_HIT_RATE:
        failures.append(
            f"acerto de fonte {source_hit!r} abaixo do mínimo {MIN_SOURCE_HIT_RATE:.2f}"
        )
    if false_abstentions > MAX_FALSE_ABSTENTIONS:
        failures.append(
            f"falsas abstenções {false_abstentions} acima do máximo "
            f"{MAX_FALSE_ABSTENTIONS}"
        )
    if invalid_citations > MAX_INVALID_CITATIONS:
        failures.append(
            f"citações inválidas {invalid_citations} acima do máximo "
            f"{MAX_INVALID_CITATIONS}"
        )
    if citation_coverage is not None and citation_coverage < MIN_CITATION_COVERAGE:
        failures.append(
            f"cobertura de citações {citation_coverage!r} abaixo do mínimo "
            f"{MIN_CITATION_COVERAGE:.2f}"
        )
    if factual_support is not None and factual_support < MIN_FACTUAL_SUPPORT:
        failures.append(
            f"suporte factual {factual_support!r} abaixo do mínimo "
            f"{MIN_FACTUAL_SUPPORT:.2f}"
        )
    if unsupported_claims > MAX_UNSUPPORTED_CLAIMS:
        failures.append(
            f"afirmações sem suporte {unsupported_claims} acima do máximo "
            f"{MAX_UNSUPPORTED_CLAIMS}"
        )
    if incomplete_generations:
        failures.append(
            f"gerações incompletas {incomplete_generations} acima do máximo 0"
        )
    return failures


def _fmt(value: Any, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render_markdown(meta: dict[str, Any], summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    out = [
        f"# Avaliação do PontoAtivo RAG — {meta['executado_em']}",
        "",
        "Arquivo gerado automaticamente por `python -m pontoativo_rag.avaliacao`.",
        "Os valores abaixo vêm de uma execução real; nada foi editado à mão.",
        "",
        "## Configuração",
        "",
    ]
    out += [f"- **{key}:** `{value}`" for key, value in meta.items()]
    out += ["", "## Resumo", "", "| Métrica | Valor |", "|---|---|"]
    out += [f"| {key} | {_fmt(value)} |" for key, value in summary.items()]
    failures = quality_gate_failures(summary)
    out += [
        "",
        "## Verificação de qualidade",
        "",
        (
            "✅ Todos os limites foram atendidos."
            if not failures
            else "❌ Limites não atendidos:"
        ),
    ]
    out += [f"- {failure}" for failure in failures]
    out += [
        "",
        "Recall@k é calculado por fonte: fração das fontes do gabarito presentes entre os",
        "trechos recuperados. Distância é a distância cosseno (menor = mais próximo) e",
        "não representa probabilidade de a resposta estar correta.",
        "",
        "## Resultados por pergunta",
        "",
        "| ID | Categoria | Recall@k | Melhor dist. | Modo | Absteve | Citou relevante | Recup. (s) | Geração (s) | Tentativas |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        out.append(
            f"| {row['id']} | {row['categoria']} | {_fmt(row['recall_at_k'])} | "
            f"{_fmt(row['melhor_distancia'], 3)} | {row['modo']} | {_fmt(row['absteve'])} | "
            f"{_fmt(row['citou_fonte_relevante'])} | {_fmt(row['tempo_recuperacao_s'])} | "
            f"{_fmt(row['tempo_geracao_s'], 1)} | {_fmt(row.get('tentativas_geracao'))} |"
        )
    out += ["", "## Respostas registradas (para revisão de fidelidade)", ""]
    for row in rows:
        result = row["resultado"]
        out += [
            f"### {row['id']} — {row['pergunta']}",
            "",
            f"- **Gabarito:** {', '.join(row['fontes_relevantes']) or 'sem resposta na base'}",
            f"- **Referência esperada:** {row['referencia']}",
            f"- **Fontes recuperadas:** {', '.join(row['fontes_recuperadas']) or 'nenhuma'}",
            f"- **Fontes citadas:** {', '.join(row['fontes_citadas']) or 'nenhuma'}",
        ]
        if row["citacoes_invalidas"]:
            out.append(f"- **Citações inválidas:** {', '.join(row['citacoes_invalidas'])}")
        out += ["", "Trechos recuperados:", ""]
        for item in result["retrieved"]:
            page = f", p. {item['page_number']}" if item.get("page_number") else ""
            if item.get("page_end"):
                page += f"–{item['page_end']}"
            section = f", seção {item['section']}" if item.get("section") else ""
            out.append(
                f"- `{item['ref']}` {item['source_id']}{page}{section} — distância {item['distance']:.3f}"
            )
        out += ["", "Resposta:", ""]
        out += [f"> {line}" if line.strip() else ">" for line in result["answer"].splitlines()]
        out += ["", "- **Fidelidade:** _pendente de revisão humana_", ""]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Avaliação do PontoAtivo RAG.")
    parser.add_argument("--perguntas", type=Path, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--sem-geracao", action="store_true")
    parser.add_argument(
        "--verificar-qualidade",
        action="store_true",
        help="falha se as métricas ficarem fora dos limites mínimos",
    )
    parser.add_argument("--rotulo", default="", help="sufixo do nome dos arquivos gerados")
    parser.add_argument(
        "--reranker", choices=("hibrido", "vetorial"), default="hibrido",
        help="estratégia de ordenação dos resultados",
    )
    parser.add_argument("--comparar-anterior", type=Path, default=None)
    parser.add_argument("--comparar-atual", type=Path, default=None)
    args = parser.parse_args(argv)

    if bool(args.comparar_anterior) != bool(args.comparar_atual):
        parser.error("--comparar-anterior e --comparar-atual devem ser usados juntos")
    if args.comparar_anterior and args.comparar_atual:
        comparison = compare_evaluations(
            load_evaluation(args.comparar_anterior),
            load_evaluation(args.comparar_atual),
        )
        output = args.comparar_atual.with_name(
            f"comparacao_{args.comparar_anterior.stem}_vs_{args.comparar_atual.stem}.md"
        )
        output.write_text(
            render_comparison(comparison, args.comparar_anterior, args.comparar_atual),
            encoding="utf-8",
        )
        print(output)
        return 1 if comparison["novas_fontes_irrelevantes_no_top3"] else 0

    from .consulta import answer_question, build_pipeline

    settings = Settings.from_env()
    path = args.perguntas or settings.data_dir / "perguntas_avaliacao.jsonl"
    questions = load_questions(path)
    retriever, generator = build_pipeline(
        settings, use_llm=not args.sem_geracao, reranker=args.reranker
    )
    top_k = args.top_k or settings.top_k

    rows = []
    started = time.perf_counter()
    for question in questions:
        result, retrieval_seconds = answer_question(
            settings, retriever, generator, question.pergunta, top_k=top_k
        )
        row = score_question(question, result, retrieval_seconds)
        rows.append(row)
        print(
            f"{question.id} recall@{top_k}={_fmt(row['recall_at_k'])} "
            f"dist={_fmt(row['melhor_distancia'], 3)} modo={row['modo']} "
            f"absteve={row['absteve']} citadas={row['fontes_citadas']}"
        )

    now = datetime.now()
    meta = {
        "executado_em": now.isoformat(timespec="seconds"),
        "perguntas": path.name,
        "modelo_embeddings": settings.embedding_model,
        "modelo_llm": None if args.sem_geracao else settings.ollama_model,
        "resposta_estruturada": None if args.sem_geracao else settings.structured_answers,
        "tentativas_maximas": None if args.sem_geracao else settings.max_generation_attempts,
        "num_predict": None if args.sem_geracao else settings.ollama_num_predict,
        "reranker": args.reranker,
        "top_k": top_k,
        "limiar_distancia": settings.max_distance,
        "chunk_pai_palavras": settings.parent_chunk_tokens,
        "sobreposicao_palavras": settings.chunk_overlap_tokens,
        "segmento_embedding_palavras": settings.embedding_segment_tokens,
        "vetores_no_banco": retriever.store.count(),
        "duracao_total_s": round(time.perf_counter() - started, 1),
    }
    summary = summarize(rows)
    suffix = f"_{args.rotulo}" if args.rotulo else ""
    stem = settings.evidence_dir / f"avaliacao_{now:%Y%m%d_%H%M%S}{suffix}"
    settings.evidence_dir.mkdir(parents=True, exist_ok=True)
    with stem.with_suffix(".jsonl").open("w", encoding="utf-8") as file:
        file.write(json.dumps({"meta": meta, "resumo": summary}, ensure_ascii=False) + "\n")
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    stem.with_suffix(".md").write_text(render_markdown(meta, summary, rows), encoding="utf-8")

    print("\nRESUMO")
    for key, value in summary.items():
        print(f"  {key}: {_fmt(value)}")
    failures = quality_gate_failures(summary)
    if failures:
        print("\nVERIFICAÇÃO DE QUALIDADE: FALHOU")
        for failure in failures:
            print(f"  - {failure}")
    elif args.verificar_qualidade:
        print("\nVERIFICAÇÃO DE QUALIDADE: OK")
    print(f"\nEvidências: {stem.with_suffix('.md').relative_to(settings.root)}")
    return 1 if args.verificar_qualidade and failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
