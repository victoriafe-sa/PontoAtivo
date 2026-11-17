"""Modelos de dados auditáveis compartilhados pelo pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
import re
from typing import Any


@dataclass(frozen=True, slots=True)
class SourceRecord:
    source_id: str
    title: str
    institution: str
    location: str
    document_type: str
    subject: str
    verification_status: str
    publication_date: str = ""
    collected_at: str = ""
    administrative_region: str = ""
    sport_modality: str = ""
    quality: str = ""
    checksum_sha256: str = ""
    # Cópia local da fonte. ``location`` continua sendo a origem citável (URL).
    scope: str = ""
    local_path: str = ""
    notes: str = ""
    volatility: str = ""
    freshness_status: str = ""
    review_interval_days: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_source_freshness(source: SourceRecord, *, today: date | None = None) -> SourceRecord:
    """Preenche a política temporal sem alterar o conteúdo original da fonte."""
    if source.freshness_status and source.volatility and source.review_interval_days:
        return source
    text = " ".join(
        (source.title, source.subject, source.notes, source.sport_modality)
    ).casefold()
    if re.search(r"hor[aá]rio|vaga|pre[cç]o|turma|funcionamento|inscri", text):
        volatility, interval = "alta", 180
    elif re.search(r"lei|decreto|norma|legisla[cç]", text):
        volatility, interval = "baixa", 730
    else:
        volatility, interval = "média", 365

    raw_date = source.publication_date.strip()
    published: date | None = None
    match = re.fullmatch(r"(\d{4})(?:-(\d{2})-(\d{2}))?", raw_date)
    if match:
        year, month, day = match.groups()
        published = date(
            int(year), int(month or 12), int(day or 31)
        )
    if published is None:
        freshness = "desconhecida"
    else:
        age_days = ((today or date.today()) - published).days
        if age_days <= interval:
            freshness = "atual"
        elif age_days <= interval * 2:
            freshness = "em_revisao"
        else:
            freshness = "antiga"
    return SourceRecord(
        **{
            **source.to_dict(),
            "volatility": source.volatility or volatility,
            "freshness_status": source.freshness_status or freshness,
            "review_interval_days": source.review_interval_days or interval,
        }
    )


@dataclass(frozen=True, slots=True)
class DocumentPage:
    page_number: int
    text: str
    section: str = ""


@dataclass(frozen=True, slots=True)
class NormalizedDocument:
    source: SourceRecord
    text: str
    checksum_sha256: str
    pages: tuple[DocumentPage, ...] = field(default_factory=tuple)
    # Páginas sem texto nem imagem identificável: candidatas a OCR.
    missing_pages: tuple[int, ...] = field(default_factory=tuple)
    # Páginas compostas por imagem, como capas e contracapas.
    graphical_pages: tuple[int, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source.to_dict(),
            "text": self.text,
            "checksum_sha256": self.checksum_sha256,
            "pages": [asdict(page) for page in self.pages],
            "missing_pages": list(self.missing_pages),
            "graphical_pages": list(self.graphical_pages),
        }


@dataclass(frozen=True, slots=True)
class ParentChunk:
    chunk_id: str
    source_id: str
    index: int
    text: str
    title: str
    institution: str
    location: str
    checksum_sha256: str
    page_number: int | None = None
    page_end: int | None = None
    section: str = ""
    administrative_region: str = ""
    sport_modality: str = ""
    verification_status: str = ""
    freshness_status: str = ""
    volatility: str = ""
    source_type: str = ""
    entity_key: str = ""
    structure_kind: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class EmbeddingSegment:
    segment_id: str
    parent_chunk_id: str
    source_id: str
    index: int
    text: str
    parent_text: str
    title: str
    institution: str
    location: str
    checksum_sha256: str
    page_number: int | None = None
    page_end: int | None = None
    section: str = ""
    administrative_region: str = ""
    sport_modality: str = ""
    verification_status: str = ""
    freshness_status: str = ""
    volatility: str = ""
    source_type: str = ""
    entity_key: str = ""
    structure_kind: str = ""

    @property
    def embedding_input(self) -> str:
        """Texto efetivamente vetorizado: título + seção + segmento.

        Título e seção dão contexto a segmentos que, isolados, não citam o
        local ou o programa a que se referem. O texto citado continua sendo
        ``text``.
        """
        return "\n".join(part for part in (self.title, self.section, self.text) if part)

    def metadata(self) -> dict[str, str | int]:
        values = asdict(self)
        values.pop("text")
        values.pop("parent_text")
        return {key: value for key, value in values.items() if value not in (None, "")}
