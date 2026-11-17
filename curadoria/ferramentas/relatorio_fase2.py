"""Gera métricas auditáveis da Fase 2: fontes, cobertura e acessibilidade."""
from __future__ import annotations

import csv
import json
import re
import sys
import tempfile
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAG_ROOT = ROOT.parent / "PontoAtivo-RAG"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(RAG_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(RAG_ROOT / "src"))
from ferramentas.gerar_base import generate, read_js
from pontoativo_rag.carregamento import load_catalog

TODAY = date(2026, 11, 10)
ACCESSIBILITY_ATTRIBUTES = (
    "step_free_route",
    "entry_barrier_free",
    "circulation",
    "accessible_toilet",
    "accessible_parking",
    "tactile_paving",
    "signage",
    "adapted_equipment",
    "human_support",
)


def _authority(institution: str) -> str:
    text = institution.casefold()
    if any(term in text for term in ("secretaria", "governo", "presid", "ministério", "agência brasilia")):
        return "oficial"
    if any(term in text for term in ("openstreetmap", "nominatim")):
        return "colaborativa"
    return "institucional"


def _region_key(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().casefold().split()
    )


def source_metrics() -> dict:
    path = RAG_ROOT / "dados" / "rag" / "catalogo.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    classified = {
        source.source_id: source
        for source in load_catalog(path)
    }
    metrics = []
    for row in rows:
        required = ("title", "institution", "location", "local_path", "subject", "scope")
        missing = [field for field in required if not row.get(field)]
        metrics.append(
            {
                "source_id": row["source_id"],
                "authority": _authority(row.get("institution", "")),
                "freshness": classified[row["source_id"]].freshness_status,
                "completeness_score": round((len(required) - len(missing)) / len(required), 2),
                "missing_fields": missing,
            }
        )
    return {
        "total": len(metrics),
        "authority": dict(Counter(item["authority"] for item in metrics)),
        "freshness": dict(Counter(item["freshness"] for item in metrics)),
        "completeness": {
            "complete": sum(item["completeness_score"] == 1 for item in metrics),
            "incomplete": sum(item["completeness_score"] < 1 for item in metrics),
            "average_score": round(
                sum(item["completeness_score"] for item in metrics) / len(metrics), 2
            ),
        },
        "items": metrics,
    }


def place_metrics(path: Path) -> dict:
    places = read_js(path)
    region_names = {}
    for item in places:
        name = item.get("ra") or "sem região"
        region_names.setdefault(_region_key(name), name)
    by_region = Counter(
        region_names[_region_key(item.get("ra") or "sem região")] for item in places
    )
    by_type = Counter(item.get("t") or "sem_tipo" for item in places)
    with_coordinates = sum(item.get("lat") is not None and item.get("lon") is not None for item in places)
    attributes = {}
    for attribute in ACCESSIBILITY_ATTRIBUTES:
        known = 0
        levels = Counter()
        for place in places:
            evidence = (place.get("evidence") or {}).get("accessibility_attributes", {})
            value = evidence.get(attribute, {}).get("value")
            if value not in (None, "", False):
                known += 1
            levels[evidence.get(attribute, {}).get("level", "desconhecido")] += 1
        attributes[attribute] = {"known": known, "unknown": len(places) - known, "levels": dict(levels)}
    return {
        "input": str(path.relative_to(ROOT)),
        "total": len(places),
        "with_coordinates": with_coordinates,
        "without_coordinates": len(places) - with_coordinates,
        "coverage_by_region": dict(sorted(by_region.items())),
        "coverage_by_type": dict(sorted(by_type.items())),
        "accessibility_attributes": attributes,
    }


def revision_metrics() -> dict:
    path = ROOT / "data" / "curadoria" / "revisao.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    return {
        "total": len(items),
        "resolved": sum(item.get("status", "").startswith("resolved") for item in items),
        "blocked_external_verification": sum(
            item.get("status") == "blocked_external_verification" for item in items
        ),
        "pending": sum(item.get("status") == "pending" for item in items),
        "by_reason": dict(Counter(item.get("reason", "sem_motivo") for item in items)),
    }


def triage_revisions() -> list[dict]:
    """Classifica pendências sem converter hipótese em evidência publicada."""
    path = ROOT / "data" / "curadoria" / "revisao.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    for item in items:
        if item.get("status") != "pending":
            continue
        item["status"] = "blocked_external_verification"
        item["next_action"] = (
            "Obter confirmação documental ou vistoria; manter fora da publicação "
            "até existir fonte com endereço/coordenada verificável."
        )
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return items


def render(report: dict) -> str:
    sources = report["sources"]
    places = report["places"]
    out = [
        "# Relatório da Fase 2 — Dados",
        "",
        f"**Data de referência:** {TODAY.isoformat()}",
        "",
        "## Autoridade, atualidade e completude das fontes",
        "",
        "Essas dimensões são independentes: uma fonte oficial pode estar antiga ou incompleta.",
        "",
        f"- Fontes catalogadas: **{sources['total']}**",
        f"- Autoridade: `{sources['authority']}`",
        f"- Atualidade: `{sources['freshness']}`",
        f"- Completude média do catálogo: **{sources['completeness']['average_score']:.2f}**",
        f"- Fontes com todos os campos mínimos: **{sources['completeness']['complete']}**",
        "",
        "## Cobertura territorial",
        "",
        f"- Base analisada: `{places['input']}`",
        f"- Locais: **{places['total']}**",
        f"- Com coordenadas: **{places['with_coordinates']}**",
        f"- Sem coordenadas: **{places['without_coordinates']}**",
        "",
        "| Região administrativa | Locais |",
        "|---|---:|",
    ]
    out.extend(f"| {region} | {count} |" for region, count in places["coverage_by_region"].items())
    out += [
        "",
        "## Acessibilidade por atributo",
        "",
        "| Atributo | Com evidência | Sem evidência |",
        "|---|---:|---:|",
    ]
    labels = {
        "step_free_route": "rota sem degraus",
        "entry_barrier_free": "entrada acessível",
        "circulation": "circulação",
        "accessible_toilet": "banheiro acessível",
        "accessible_parking": "vaga acessível",
        "tactile_paving": "piso tátil",
        "signage": "sinalização",
        "adapted_equipment": "equipamento adaptado",
        "human_support": "apoio humano",
    }
    out.extend(
        f"| {labels[key]} | {item['known']} | {item['unknown']} |"
        for key, item in places["accessibility_attributes"].items()
    )
    out += [
        "",
        "## Pendências de curadoria",
        "",
        f"- Total: **{report['revisions']['total']}**",
        f"- Resolvidas: **{report['revisions']['resolved']}**",
        f"- Bloqueadas por confirmação externa: **{report['revisions']['blocked_external_verification']}**",
        f"- Pendentes sem triagem: **{report['revisions']['pending']}**",
        "",
        "Pendências sem fonte verificável permanecem fora da publicação ou sem pino.",
        "Isso é uma proteção de qualidade, não uma afirmação de inexistência do local.",
        "",
    ]
    return "\n".join(out)


def main() -> None:
    triage_revisions()
    candidate = ROOT / "data" / "locais.candidato.js"
    published = ROOT.parent / "site" / "data" / "locais.js"
    places_path = candidate if candidate.exists() else published
    raw_places = read_js(places_path)
    if not raw_places or "evidence" not in raw_places[0]:
        with tempfile.TemporaryDirectory() as temp_dir:
            normalized = Path(temp_dir) / "locais.js"
            generate(places_path, ROOT / "data" / "curadoria", normalized)
            report_places = place_metrics(normalized)
    else:
        report_places = place_metrics(places_path)
    report = {
        "generated_at": TODAY.isoformat(),
        "sources": source_metrics(),
        "places": report_places,
        "revisions": revision_metrics(),
    }
    output_dir = ROOT / "data" / "curadoria"
    (output_dir / "relatorio_fase2.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "docs" / "relatorio-fase2-dados.md").write_text(render(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
