"""Pipeline de ingestão: catálogo -> documentos -> chunks -> vetores no Chroma.

Uso pelo terminal (a partir da pasta do projeto):

    python -m pontoativo_rag.ingestao
"""

from __future__ import annotations

import argparse
import json
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, Sequence

from .carregamento import DocumentLoadError, load_catalog, write_documents_jsonl
from .carregamento import load_document
from .limpeza import clean_documents, drop_duplicate_chunks
from .configuracao import Settings
from .modelos import EmbeddingSegment, NormalizedDocument, SourceRecord
from .processamento import (
    create_embedding_segments,
    create_parent_chunks,
    deduplicate_documents,
    write_chunks_jsonl,
)


# Situações de verificação aceitas na coleção principal. Qualquer outro valor
# (por exemplo "pendente" ou "rejeitada") fica fora e é registrado no relatório.
ACCEPTED_STATUSES = frozenset(
    {"verificado", "verificada", "aprovada", "aprovada_com_ressalvas"}
)


class Embedder(Protocol):
    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...


class VectorStore(Protocol):
    def upsert(self, segments, embeddings) -> None: ...
    def existing_ids(self, ids: Sequence[str]) -> set[str]: ...
    def all_ids(self) -> set[str]: ...
    def delete(self, ids: Sequence[str]) -> None: ...
    def count(self) -> int: ...


@dataclass(slots=True)
class IngestionReport:
    """Resumo auditável de uma execução da ingestão."""

    started_at: str
    catalog_records: int = 0
    documents_loaded: int = 0
    documents_failed: int = 0
    documents_skipped: int = 0
    duplicates: dict[str, str] = field(default_factory=dict)
    parent_chunks: int = 0
    duplicate_chunks: int = 0
    embedding_segments: int = 0
    segments_encoded: int = 0
    segments_reused: int = 0
    segments_removed: int = 0
    vectors_in_store: int = 0
    duration_seconds: float = 0.0
    errors: dict[str, str] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)
    pages_without_text: dict[str, list[int]] = field(default_factory=dict)
    graphical_pages: dict[str, list[int]] = field(default_factory=dict)

    def to_text(self) -> str:
        lines = [
            "PONTOATIVO — RELATÓRIO DE INGESTÃO",
            f"Registros no catálogo ........ {self.catalog_records}",
            f"Documentos carregados ........ {self.documents_loaded}",
            f"Documentos com erro .......... {self.documents_failed}",
            f"Fora da coleção (status) ..... {self.documents_skipped}",
            f"Duplicados por checksum ...... {len(self.duplicates)}",
            f"Chunks-pai ................... {self.parent_chunks}",
            f"  repetidos entre fontes ..... {self.duplicate_chunks} (removidos)",
            f"Segmentos de embedding ....... {self.embedding_segments}",
            f"  codificados agora .......... {self.segments_encoded}",
            f"  reaproveitados do banco .... {self.segments_reused}",
            f"  removidos (obsoletos) ...... {self.segments_removed}",
            f"Vetores no ChromaDB .......... {self.vectors_in_store}",
            f"Duração ...................... {self.duration_seconds:.1f} s",
        ]
        for title, items in (
            ("ERROS", self.errors),
            ("FORA DA COLEÇÃO", self.skipped),
            ("DUPLICADOS (fonte -> fonte mantida)", self.duplicates),
        ):
            if items:
                lines.append(f"\n{title}:")
                lines.extend(f"  - {key}: {value}" for key, value in items.items())
        if self.pages_without_text:
            lines.append("\nPÁGINAS DE PDF SEM TEXTO (possível necessidade de OCR):")
            for key, pages in self.pages_without_text.items():
                lines.append(f"  - {key}: {len(pages)} página(s)")
        if self.graphical_pages:
            lines.append("\nPÁGINAS GRÁFICAS (sem camada de texto; não indexadas):")
            for key, pages in self.graphical_pages.items():
                lines.append(f"  - {key}: {len(pages)} página(s) — {', '.join(map(str, pages))}")
        return "\n".join(lines)


def _normalize_status(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    )
    return "_".join(ascii_value.lower().split())


def resolve_source_path(settings: Settings, source: SourceRecord) -> Path | None:
    """Encontra a cópia local de uma fonte, sempre relativa ao projeto."""
    candidate = source.local_path or source.location
    if not candidate or candidate.startswith(("http://", "https://")):
        return None
    path = Path(candidate)
    return path if path.is_absolute() else settings.root / path


def _load_sources(
    settings: Settings, records: list[SourceRecord], report: IngestionReport
) -> list[NormalizedDocument]:
    documents: list[NormalizedDocument] = []
    for source in records:
        if _normalize_status(source.verification_status) not in ACCEPTED_STATUSES:
            report.documents_skipped += 1
            report.skipped[source.source_id] = (
                f"situação de verificação {source.verification_status!r}"
            )
            continue
        path = resolve_source_path(settings, source)
        if path is None:
            report.documents_failed += 1
            report.errors[source.source_id] = "sem cópia local (execute a coleta)"
            continue
        try:
            document = load_document(path, source)
        except DocumentLoadError as error:
            report.documents_failed += 1
            report.errors[source.source_id] = str(error)
            continue
        if document.missing_pages:
            report.pages_without_text[source.source_id] = list(document.missing_pages)
        if document.graphical_pages:
            report.graphical_pages[source.source_id] = list(document.graphical_pages)
        documents.append(document)
    return documents


def ingest_catalog(
    settings: Settings,
    catalog_path: Path | None = None,
    *,
    embedder: Embedder,
    store: VectorStore,
) -> IngestionReport:
    """Executa a ingestão completa e sincroniza o banco vetorial com o catálogo.

    A ingestão é idempotente: segmentos cujo ID já existe no Chroma não são
    recodificados, e vetores que não correspondem mais a nenhum segmento atual
    (fonte alterada ou removida) são apagados.
    """
    start = time.perf_counter()
    report = IngestionReport(started_at=datetime.now(timezone.utc).isoformat())
    catalog_path = catalog_path or settings.data_dir / "catalogo_fontes.csv"
    records = load_catalog(catalog_path)
    report.catalog_records = len(records)

    loaded = _load_sources(settings, records, report)
    documents, report.duplicates = deduplicate_documents(loaded)
    documents = clean_documents(documents)
    report.documents_loaded = len(documents)

    chunks = [
        chunk
        for document in documents
        for chunk in create_parent_chunks(
            document,
            target_tokens=settings.parent_chunk_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
        )
    ]
    chunks, report.duplicate_chunks = drop_duplicate_chunks(chunks)
    segments: list[EmbeddingSegment] = [
        segment
        for chunk in chunks
        for segment in create_embedding_segments(
            chunk, max_tokens=settings.embedding_segment_tokens
        )
    ]
    report.parent_chunks = len(chunks)
    report.embedding_segments = len(segments)

    write_documents_jsonl(documents, settings.data_dir / "documentos_normalizados.jsonl")
    write_chunks_jsonl(chunks, settings.data_dir / "chunks.jsonl")

    current_ids = [segment.segment_id for segment in segments]
    already_stored = store.existing_ids(current_ids)
    pending = [s for s in segments if s.segment_id not in already_stored]
    if pending:
        vectors = embedder.encode([segment.embedding_input for segment in pending])
        store.upsert(pending, vectors)
    report.segments_encoded = len(pending)
    report.segments_reused = len(segments) - len(pending)

    obsolete = sorted(store.all_ids() - set(current_ids))
    if obsolete:
        store.delete(obsolete)
    report.segments_removed = len(obsolete)
    report.vectors_in_store = store.count()
    report.duration_seconds = time.perf_counter() - start
    return report


def save_report(report: IngestionReport, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingestão das fontes do PontoAtivo.")
    parser.add_argument(
        "--catalogo",
        type=Path,
        default=None,
        help="caminho do catálogo CSV (padrão: dados/catalogo_fontes.csv)",
    )
    args = parser.parse_args(argv)

    from .armazenamento import ChromaStore
    from .embeddings import EmbeddingProvider

    settings = Settings.from_env()
    settings.ensure_directories()
    print(f"Modelo de embeddings: {settings.embedding_model}")
    print(f"Coleção ChromaDB: {settings.collection_name} em {settings.vector_db_dir.name}/")
    report = ingest_catalog(
        settings,
        args.catalogo,
        embedder=EmbeddingProvider(settings.embedding_model),
        store=ChromaStore(
            settings.vector_db_dir,
            settings.collection_name,
            embedding_model=settings.embedding_model,
        ),
    )
    save_report(report, settings.data_dir / "relatorio_ingestao.json")
    print(report.to_text())
    print("\nRelatório salvo em dados/relatorio_ingestao.json")
    return 0 if report.documents_loaded else 1


if __name__ == "__main__":
    raise SystemExit(main())
