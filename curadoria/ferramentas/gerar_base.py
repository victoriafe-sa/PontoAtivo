"""Gera a base estática multifonte de forma determinística, segura e idempotente.

Princípios:
- Nunca sobrescreve data/locais.js diretamente: gera em arquivo temporário, valida
  sem erros e só então copia para o destino (após backup automático).
- Níveis de evidência por atributo (endereço, coordenadas, acessibilidade, modalidades).
- Preserva a categoria 'clube' para clubes/academias privadas.
- Mapeia o legado de acessibilidade (acc.adaptado nos COPs e CETEFE) sem inflar para 'campo'.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ferramentas.curadoria import validate_place

TODAY = "2026-11-10"
CATEGORY_CLUBE = "clube"
DEFAULT_BACKUP_NAME = "locais.original-20261105.js"
OFFICIAL_SOURCES = {"ide_df", "ide_df_parques", "ide_df_espacos_comunitarios", "sel_df", "sel_df_cops", "ibram_uc_tabela"}

ACC_KEYS = [
    ("step_free_route", "rota"),
    ("entry_barrier_free", "entrada"),
    ("circulation", "circulacao"),
    ("accessible_toilet", "banheiro"),
    ("accessible_parking", "vaga"),
    ("tactile_paving", "tatil"),
    ("signage", "sinalizacao"),
    ("adapted_equipment", "adaptado"),
    ("human_support", "apoio"),
]


def read_js(path: Path | str) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8")
    match = re.search(r"window\.PA_LOCAIS\s*=\s*(\[.*\]);?\s*$", text, re.S)
    if not match:
        raise ValueError("window.PA_LOCAIS não encontrado")
    return json.loads(match.group(1))


def default_ownership(record: dict) -> str:
    if record.get("ownership"):
        return record["ownership"]
    return "social" if record.get("t") == "para" else "public"


def legacy_source_id(record: dict) -> str:
    f = record.get("fonte", "")
    if "IDE-DF" in f and "Espaços comunitários" in f:
        return "ide_df_espacos_comunitarios"
    if "IDE-DF" in f and "Parques" in f:
        return "ide_df_parques"
    if "IDE-DF" in f:
        return "ide_df"
    if "Centros Olímpicos" in f or "cops" in record.get("url", ""):
        return "sel_df_cops"
    if "Secretaria" in f:
        return "sel_df"
    if "Unidades de Conservação" in f or "Ibram" in f:
        return "ibram_uc_tabela"
    if "UnB" in f:
        return "unb_esporte"
    if "Agência Gov" in f or "Metrópoles" in f:
        return "agencia_gov_enap"
    return "osm"


def build_accessibility_attributes(record: dict, legacy_acc: dict, source_id: str, source_date: str | None) -> dict:
    attrs = {}
    is_official = source_id in OFFICIAL_SOURCES
    is_org = source_id in {"unb_esporte", "agencia_gov_enap", "cetefe", "cpb"}
    declared_level = "oficial" if is_official else "organizacao" if is_org else "colaborativo"
    for long_name, legacy_short in ACC_KEYS:
        val = legacy_acc.get(legacy_short)
        if val in ("ok", "info"):
            attrs[long_name] = {
                "value": val,
                "level": declared_level,
                "source_id": source_id,
                "source_date": source_date,
                "checked_at": TODAY,
                "note": "Informado pela fonte institucional; não constitui vistoria técnica em campo.",
            }
            if not source_date:
                attrs[long_name]["source_date_unknown"] = True
        else:
            attrs[long_name] = {"value": None, "level": "desconhecido"}
    return attrs


def legacy_evidence(record: dict) -> dict:
    src = legacy_source_id(record)
    src_date = record.get("data")
    is_official = src in OFFICIAL_SOURCES
    has_coords = record.get("lat") is not None and record.get("lon") is not None
    is_aprox = bool(record.get("aprox") or "Aproximada" in record.get("geo", "") or "Nominatim" in record.get("geo", ""))

    addr_ev = {
        "value": record.get("end"),
        "level": "oficial" if is_official else "organizacao" if src != "osm" else "colaborativo",
        "source_id": src,
        "checked_at": TODAY,
    }
    if src_date:
        addr_ev["source_date"] = src_date
    else:
        addr_ev["source_date_unknown"] = True

    if has_coords:
        coords_src = "osm" if is_aprox else src
        coords_level = "colaborativo" if is_aprox else ("oficial" if is_official else "organizacao")
        coords_ev = {
            "value": True,
            "level": coords_level,
            "source_id": coords_src,
            "checked_at": TODAY,
        }
        if coords_src != "osm" and src_date:
            coords_ev["source_date"] = src_date
        elif coords_src != "osm":
            coords_ev["source_date_unknown"] = True
    else:
        coords_ev = {
            "value": None,
            "level": "desconhecido",
            "note": "Localização exata pendente.",
        }

    legacy_acc = record.get("acc") or {}
    acc_attrs = build_accessibility_attributes(record, legacy_acc, src, src_date)
    has_acc = any(v.get("level") != "desconhecido" for v in acc_attrs.values())
    acc_summary = {
        "value": "info" if has_acc else None,
        "level": declared_level_summary(acc_attrs) if has_acc else "desconhecido",
    }
    if has_acc:
        acc_summary["source_id"] = src
        acc_summary["checked_at"] = TODAY
        if src_date:
            acc_summary["source_date"] = src_date
        else:
            acc_summary["source_date_unknown"] = True

    mods_ev = {
        "value": record.get("mods", []),
        "level": "colaborativo" if record.get("mods_inferidas") else ("oficial" if is_official else "organizacao"),
        "source_id": src,
        "checked_at": TODAY,
    }
    if record.get("mods_inferidas"):
        mods_ev["note"] = "Modalidades deduzidas a partir do tipo de equipamento público."
    if src_date:
        mods_ev["source_date"] = src_date
    else:
        mods_ev["source_date_unknown"] = True

    return {
        "address": addr_ev,
        "coordinates": coords_ev,
        "accessibility": acc_summary,
        "accessibility_attributes": acc_attrs,
        "modalities": mods_ev,
    }


def declared_level_summary(attrs: dict) -> str:
    levels = {v.get("level") for v in attrs.values() if v.get("level") != "desconhecido"}
    if "campo" in levels:
        return "campo"
    if "oficial" in levels:
        return "oficial"
    if "organizacao" in levels:
        return "organizacao"
    if "colaborativo" in levels:
        return "colaborativo"
    return "desconhecido"


def curated_to_legacy(place: dict, private: bool = False) -> dict:
    modalities = place.get("modalities", [])
    mods = [m["name"] if isinstance(m, dict) else m for m in modalities]
    category = CATEGORY_CLUBE if private else ("para" if place.get("ownership") == "social" or place["id"].startswith("para-") else "estadio")
    checked_date = place.get("checked_at", TODAY)
    src_id = place.get("source_id") or (place["evidence"].get("address", {}).get("source_id"))
    src_url = place.get("source_url") or "https://www.cpb.org.br/"
    fonte_label = place.get("source_name") or ("Site oficial do estabelecimento" if private else "Site oficial da organização")

    ev_in = deepcopy(place.get("evidence", {}))
    # Garante estrutura padronizada com accessibility_attributes
    acc_attrs = ev_in.get("accessibility_attributes") or build_accessibility_attributes(
        place, {}, src_id or "osm", None
    )
    ev_in["accessibility_attributes"] = acc_attrs
    ev_in.setdefault("accessibility", {"value": None, "level": "desconhecido"})

    has_coords = place.get("latitude") is not None and place.get("longitude") is not None
    if not has_coords:
        ev_in["coordinates"] = {
            "value": None,
            "level": "desconhecido",
            "note": "Coordenada sem procedência documentada; sem pino até confirmação.",
        }

    return {
        "id": place["id"],
        "n": place["name"],
        "t": category,
        "ra": place.get("region"),
        "end": place.get("address"),
        "lat": place.get("latitude"),
        "lon": place.get("longitude"),
        "mods": mods,
        "custo": "Privado — confirme regras de acesso" if private else "Confirme com a organização",
        "gratis": False,
        "acc": {},
        "fonte": fonte_label,
        "url": src_url,
        "data": checked_date,
        "ownership": place.get("ownership", "private" if private else "social"),
        "access_rule": place.get("access_rule", "unknown"),
        "reviewed_at": TODAY,
        "evidence": ev_in,
        "obs": place.get("review_note"),
    }


def generate(input_js: Path | str, curated_dir: Path | str, output_js: Path | str) -> list[dict]:
    records = read_js(input_js)
    curated_path = Path(curated_dir)
    by_id: dict[str, dict] = {}

    for raw in records:
        rid = raw["id"]
        # Mantém apenas a primeira ocorrência (resolve pqu-5 duplicado 3x na base de 05/11)
        if rid in by_id:
            continue
        rec = deepcopy(raw)
        rec["ownership"] = default_ownership(rec)
        rec["reviewed_at"] = TODAY
        rec["evidence"] = legacy_evidence(rec)
        by_id[rid] = rec

    # 1. Aplica parques resolvidos (12 oficiais com geometria ONDA)
    parks_path = curated_path / "parques_resolvidos.json"
    if parks_path.exists():
        for park in json.loads(parks_path.read_text(encoding="utf-8")):
            pid = park["id"]
            if pid not in by_id:
                continue
            r = by_id[pid]
            r["lat"], r["lon"] = park["latitude"], park["longitude"]
            r["geo"] = "Ponto representativo interno da poligonal oficial Ibram/ONDA"
            r["aprox"] = True
            r["evidence"]["coordinates"] = {
                "value": True,
                "level": "oficial",
                "source_id": park.get("source_id", "ibram_onda"),
                "source_date": TODAY,
                "checked_at": TODAY,
                "note": "Ponto representativo da área do parque; não indica portaria nem entrada oficial.",
            }

    # 2. CETEFE (atualiza registro já existente preservando pino aproximado de 05/11)
    # e outros locais de paradesporto
    para_path = curated_path / "paradesporto.json"
    if para_path.exists():
        for place in json.loads(para_path.read_text(encoding="utf-8")):
            pid = place["id"]
            if pid == "para-cetefe" and pid in by_id:
                old = by_id[pid]
                old["end"] = place.get("address") or old.get("end")
                old["ownership"] = place.get("ownership", "social")
                old["access_rule"] = place.get("access_rule", "contact")
                old["reviewed_at"] = TODAY
                old["obs"] = place.get("review_note") or old.get("obs")
                # Preserva lat/lon aproximados do OSM de 05/11 declarando explicitamente como colaborativo
                old["evidence"]["address"] = deepcopy(place["evidence"]["address"])
                old["evidence"]["coordinates"] = {
                    "value": True,
                    "level": "colaborativo",
                    "source_id": "osm",
                    "checked_at": TODAY,
                    "note": "Coordenada aproximada ao nível de setor/bairro (OpenStreetMap); confirmar entrada exata.",
                }
                # Modalidades do CETEFE com suas fontes institucionais
                old["mods"] = [m["name"] if isinstance(m, dict) else m for m in place.get("modalities", [])]
                old["evidence"]["modalities"] = {
                    "value": old["mods"],
                    "level": "organizacao",
                    "source_id": "cetefe",
                    "checked_at": TODAY,
                    "source_date_unknown": True,
                }
                old["acc"] = {"adaptado": "info"}
                old["evidence"]["accessibility_attributes"]["adapted_equipment"] = {
                    "value": "info",
                    "level": "organizacao",
                    "source_id": "cetefe",
                    "checked_at": TODAY,
                    "source_date_unknown": True,
                    "note": "Entidade de paradesporto; oferta de modalidades confirmada no site institucional.",
                }
            else:
                new_rec = curated_to_legacy(place, private=False)
                by_id[pid] = new_rec

    # 3. Privados (sempre categoria 'clube')
    priv_path = curated_path / "privados.json"
    if priv_path.exists():
        for place in json.loads(priv_path.read_text(encoding="utf-8")):
            pid = place["id"]
            by_id[pid] = curated_to_legacy(place, private=True)

    # 4. Espaços comunitários da IDE-DF (campos, quadras e praças sem equivalente na base),
    # gerados por ferramentas/importar_espacos_comunitarios.py já deduplicados
    epc_path = curated_path / "espacos_comunitarios.json"
    if epc_path.exists():
        for raw in json.loads(epc_path.read_text(encoding="utf-8")):
            if raw["id"] in by_id:
                continue
            rec = deepcopy(raw)
            rec["ownership"] = "public"
            rec["reviewed_at"] = TODAY
            rec["evidence"] = legacy_evidence(rec)
            by_id[rec["id"]] = rec

    result = sorted(by_id.values(), key=lambda r: r["id"])

    meta = {
        "generated_at": TODAY,
        "count": len(result),
        "evidence_model": "per_attribute",
        "levels": ["oficial", "organizacao", "colaborativo", "campo", "divergente", "desconhecido"],
        "ownerships": ["public", "private", "social"],
        "accessibility_attributes": [k for k, _ in ACC_KEYS],
    }

    content = (
        "// Gerado automaticamente – base de locais PontoAtivo (Brasília/DF) com curadoria multifonte.\n"
        f"window.PA_META = {json.dumps(meta, ensure_ascii=False, sort_keys=True, separators=(',', ':'))};\n"
        f"window.PA_LOCAIS = {json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',', ':'))};\n"
    )

    out_file = Path(output_js)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(content, encoding="utf-8")
    return result


def validate_records(records: list[dict], sources: dict, today: date) -> list[tuple[str, str, str]]:
    errors = []
    for r in records:
        rec = {**r, "name": r.get("n", ""), "latitude": r.get("lat"), "longitude": r.get("lon")}
        issues = validate_place(rec, sources, today)
        for issue in issues:
            if issue.severity == "error":
                errors.append((r.get("id", ""), issue.field, issue.message))
    return errors


def publish_with_safety(
    input_js: Path | str,
    curated_dir: Path | str,
    target_js: Path | str,
    backup_path: Path | str | None = None,
    validate_fn=None,
) -> list[dict]:
    target = Path(target_js)
    curated = Path(curated_dir)
    sources = {s["id"]: s for s in json.loads((curated / "fontes.json").read_text(encoding="utf-8"))}

    with tempfile.TemporaryDirectory(prefix="pa_gen_") as td:
        tmp_out = Path(td) / "candidate_locais.js"
        records = generate(input_js, curated_dir, tmp_out)

        if validate_fn is not None:
            custom_errs = validate_fn(records)
            if custom_errs:
                raise ValueError(f"falha de validação customizada: {custom_errs}")

        errors = validate_records(records, sources, date(2026, 11, 10))
        if errors:
            raise ValueError(f"a base gerada contém {len(errors)} erro(s) de validação: {errors[:5]}")

        # Se o destino já existe, garante backup
        if target.exists():
            backup = Path(backup_path) if backup_path else target.parent / DEFAULT_BACKUP_NAME
            if not backup.exists():
                shutil.copy2(target, backup)

        shutil.copy2(tmp_out, target)
        return records


def main():
    parser = argparse.ArgumentParser(description="Gera a base multifonte do PontoAtivo com segurança.")
    parser.add_argument("--input", default="data/locais.original-20261105.js")
    parser.add_argument("--curadoria", default="data/curadoria")
    parser.add_argument("--output", default="data/locais.candidato.js", help="Padrão seguro: nunca sobrescreve ../site/data/locais.js sem --publish")
    parser.add_argument("--publish", action="store_true", help="Autorização explícita para substituir ../site/data/locais.js com backup")
    parser.add_argument("--backup", default="data/" + DEFAULT_BACKUP_NAME)
    args = parser.parse_args()

    # O mapa publicado fica em site/; a curadoria roda dentro de curadoria/.
    target = "../site/data/locais.js" if args.publish else args.output
    if args.publish:
        recs = publish_with_safety(args.input, args.curadoria, target, args.backup)
        print(f"PUBLICADO COM SUCESSO: {len(recs)} locais em {target}")
    else:
        recs = generate(args.input, args.curadoria, target)
        print(f"GERADO EM {target}: {len(recs)} locais (base publicada inalterada)")


if __name__ == "__main__":
    main()
