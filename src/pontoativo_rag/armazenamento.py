"""Persistência e consulta dos segmentos no ChromaDB local."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb

from .modelos import EmbeddingSegment


@dataclass(frozen=True, slots=True)
class VectorHit:
    segment_id: str
    text: str
    metadata: dict[str, Any]
    distance: float


def build_where(filters: dict[str, str] | None) -> dict[str, Any] | None:
    """Converte filtros simples na sintaxe do Chroma (mais de um campo usa $and)."""
    clean = {key: value for key, value in (filters or {}).items() if value}
    if not clean:
        return None
    if len(clean) == 1:
        return clean
    return {"$and": [{key: value} for key, value in clean.items()]}


class EmbeddingModelMismatch(RuntimeError):
    """A coleção foi criada com outro modelo; os vetores seriam incomparáveis."""


class ChromaStore:
    def __init__(
        self,
        persist_directory: Path,
        collection_name: str,
        *,
        embedding_model: str | None = None,
    ) -> None:
        persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(persist_directory))
        metadata: dict[str, Any] = {"hnsw:space": "cosine"}
        if embedding_model:
            metadata["embedding_model"] = embedding_model
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata=metadata,
        )
        stored_model = (self.collection.metadata or {}).get("embedding_model")
        if embedding_model and stored_model and stored_model != embedding_model:
            raise EmbeddingModelMismatch(
                f"A coleção {collection_name!r} contém vetores de {stored_model!r}, "
                f"mas a configuração usa {embedding_model!r}. Apague a pasta "
                "dados/rag/vetorial/ e execute a ingestão novamente."
            )

    def upsert(
        self,
        segments: Sequence[EmbeddingSegment],
        embeddings: Sequence[Sequence[float]],
    ) -> None:
        if len(segments) != len(embeddings):
            raise ValueError("Cada segmento deve possuir exatamente um embedding.")
        if not segments:
            return
        metadatas = []
        for segment in segments:
            metadata = segment.metadata()
            metadata["parent_text"] = segment.parent_text
            metadatas.append(metadata)
        self.collection.upsert(
            ids=[segment.segment_id for segment in segments],
            documents=[segment.text for segment in segments],
            metadatas=metadatas,
            embeddings=[list(vector) for vector in embeddings],
        )

    def query(
        self,
        vector: Sequence[float],
        *,
        n_results: int = 5,
        filters: dict[str, str] | None = None,
    ) -> list[VectorHit]:
        if self.count() == 0:
            return []
        result = self.collection.query(
            query_embeddings=[list(vector)],
            n_results=min(n_results, self.count()),
            where=build_where(filters),
            include=["documents", "metadatas", "distances"],
        )
        ids = result["ids"][0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        return [
            VectorHit(
                segment_id=segment_id,
                text=document or "",
                metadata=dict(metadata or {}),
                distance=float(distance),
            )
            for segment_id, document, metadata, distance in zip(
                ids, documents, metadatas, distances, strict=True
            )
        ]

    def count(self) -> int:
        return self.collection.count()

    def existing_ids(self, ids: Sequence[str]) -> set[str]:
        """Retorna quais IDs já possuem vetor salvo (evita recodificar)."""
        if not ids:
            return set()
        found: set[str] = set()
        # Consultas em blocos evitam requisições grandes demais ao SQLite.
        for start in range(0, len(ids), 500):
            batch = list(ids[start : start + 500])
            found.update(self.collection.get(ids=batch, include=[])["ids"])
        return found

    def all_ids(self) -> set[str]:
        return set(self.collection.get(include=[])["ids"])

    def delete(self, ids: Sequence[str]) -> None:
        for start in range(0, len(ids), 500):
            self.collection.delete(ids=list(ids[start : start + 500]))

