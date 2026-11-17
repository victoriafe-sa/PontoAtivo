"""Modelo de evidência, validação e deduplicação do PontoAtivo."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from math import asin, cos, radians, sin, sqrt
import re
import unicodedata

LEVELS = {"oficial", "organizacao", "colaborativo", "campo", "divergente", "desconhecido"}
DF_BOUNDS = (-16.10, -15.45, -48.35, -47.25)


@dataclass
class Evidence:
    value: object
    level: str
    source_id: str | None = None
    source_date: str | None = None
    checked_at: str | None = None
    note: str | None = None
    attachment: str | None = None

    def __post_init__(self):
        if self.level not in LEVELS:
            raise ValueError(f"nível de evidência inválido: {self.level}")


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    field: str
    message: str


@dataclass(frozen=True)
class Match:
    record_id: str
    distance_m: float
    status: str


@dataclass
class MergeResult:
    record: dict
    conflicts: list[str]


def _plain(value):
    return unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().lower()


def normalize_name(value):
    return re.sub(r"[^a-z0-9]+", " ", _plain(value)).strip()


def normalize_place(record):
    out = deepcopy(record)
    out["name"] = (out.get("name") or out.get("n") or "").strip()
    out["category"] = out.get("category") or out.get("t")
    out["latitude"] = out.get("latitude", out.get("lat"))
    out["longitude"] = out.get("longitude", out.get("lon"))
    out.setdefault("status", "published")
    out.setdefault("evidence", {})
    return out


def _parse_date(value):
    if not value:
        return None
    for pattern in ("%Y-%m-%d", "%m/%Y", "%d/%m/%Y", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            pass
    return None


def validate_place(record, sources, today=None):
    today = today or date.today()
    place = normalize_place(record)
    issues = []
    lat, lon = place.get("latitude"), place.get("longitude")
    if lat is not None and lon is not None:
        if not (DF_BOUNDS[0] <= float(lat) <= DF_BOUNDS[1] and DF_BOUNDS[2] <= float(lon) <= DF_BOUNDS[3]):
            issues.append(Issue("outside_df", "error", "coordinates", "Coordenadas fora do Distrito Federal."))
    coords = place["evidence"].get("coordinates")
    if coords is not None:
        has_pin = lat is not None and lon is not None
        if has_pin and coords.get("level", "desconhecido") == "desconhecido":
            issues.append(Issue("coordinates_unsourced", "error", "coordinates", "Pino publicado sem procedência da coordenada."))
        if not has_pin and coords.get("level", "desconhecido") != "desconhecido":
            issues.append(Issue("coordinates_missing", "error", "coordinates", "Evidência de coordenada sem coordenada publicada."))
    for field, raw in place["evidence"].items():
        level = raw.get("level", "desconhecido")
        if level not in LEVELS:
            issues.append(Issue("invalid_level", "error", field, "Nível de evidência inválido."))
            continue
        if level not in {"desconhecido", "colaborativo"}:
            if not raw.get("source_id") or raw.get("source_id") not in sources:
                issues.append(Issue("missing_source", "error", field, "Fonte cadastrada obrigatória."))
            if not raw.get("checked_at"):
                issues.append(Issue("missing_date", "error", field, "Data de consulta obrigatória."))
            if not raw.get("source_date"):
                if raw.get("source_date_unknown"):
                    issues.append(Issue("source_date_unknown", "review", field, "Data da fonte não publicada; revisar."))
                else:
                    issues.append(Issue("missing_date", "error", field, "Data da fonte obrigatória ou declarada como desconhecida."))
        if level == "campo" and (not raw.get("checked_at") or not raw.get("attachment")):
            issues.append(Issue("field_evidence_incomplete", "error", field, "Vistoria de campo exige data e evidência."))
        source_date = _parse_date(raw.get("source_date"))
        if source_date and (today.year - source_date.year) * 12 + today.month - source_date.month > 24:
            issues.append(Issue("stale_source", "warning", field, "Fonte com mais de 24 meses; revisar sem apagar."))
    return issues


def haversine_m(a_lat, a_lon, b_lat, b_lon):
    radius = 6371000
    p1, p2 = radians(a_lat), radians(b_lat)
    dp, dl = radians(b_lat - a_lat), radians(b_lon - a_lon)
    value = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * radius * asin(sqrt(value))


def find_duplicate_candidates(candidate, published, radius_m=120):
    candidate = normalize_place(candidate)
    if candidate.get("latitude") is None or candidate.get("longitude") is None:
        return []
    result = []
    for raw in published:
        item = normalize_place(raw)
        if item.get("latitude") is None or item.get("longitude") is None:
            continue
        distance = haversine_m(float(candidate["latitude"]), float(candidate["longitude"]), float(item["latitude"]), float(item["longitude"]))
        if distance <= radius_m:
            same = normalize_name(candidate["name"]) == normalize_name(item["name"])
            result.append(Match(item.get("id", ""), round(distance, 1), "duplicate" if same else "possible_duplicate"))
    return sorted(result, key=lambda match: match.distance_m)


def merge_place(existing, candidate):
    base, incoming = normalize_place(existing), normalize_place(candidate)
    merged, conflicts = deepcopy(base), []
    for key, value in incoming.items():
        if key == "evidence":
            for field, evidence in value.items():
                old = merged["evidence"].get(field)
                if old and old.get("value") != evidence.get("value") and old.get("level") != "desconhecido":
                    conflicts.append(field)
                merged["evidence"][field] = deepcopy(evidence)
        elif value not in (None, "", []):
            merged[key] = deepcopy(value)
    return MergeResult(merged, conflicts)


def assess_pec_candidate(candidate, published):
    candidate = normalize_place(candidate)
    if not candidate.get("address") and not candidate.get("end"):
        return {"status": "review", "reason": "address_unconfirmed", "publish": False}
    matches = find_duplicate_candidates(candidate, published)
    if matches:
        return {"status": matches[0].status, "reason": "near_existing_record", "publish": False, "matches": matches}
    return {"status": "candidate", "reason": None, "publish": False}


def validate_community_submission(submission):
    required = ("place_id", "kind", "answers", "submitted_at")
    errors = [field for field in required if not submission.get(field)]
    if not submission.get("consent"):
        errors.append("consent_required")
    return {
        "valid": not errors,
        "errors": errors,
        "status": "pending_review",
        "level": "colaborativo",
    }
