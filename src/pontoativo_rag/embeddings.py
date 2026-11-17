"""Geração de embeddings com carregamento tardio do modelo."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any


def _default_factory(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


class EmbeddingProvider:
    def __init__(
        self,
        model_name: str,
        *,
        batch_size: int = 32,
        model_factory: Callable[[str], Any] = _default_factory,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self._model_factory = model_factory
        self._model = None

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if self._model is None:
            self._model = self._model_factory(self.model_name)
        vectors = self._model.encode(
            list(texts),
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        if hasattr(vectors, "tolist"):
            vectors = vectors.tolist()
        return [[float(value) for value in vector] for vector in vectors]

