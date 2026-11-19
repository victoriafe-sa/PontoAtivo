"""Montagem dos recursos compartilhados pelas consultas documentais."""

from .configuracao import Settings
from .geracao import OllamaClient
from .recuperacao import Retriever


def criar_recuperador(settings: Settings, *, reranker: str = "hibrido") -> Retriever:
    from .armazenamento import ChromaStore
    from .embeddings import EmbeddingProvider

    store = ChromaStore(
        settings.vector_db_dir,
        settings.collection_name,
        embedding_model=settings.embedding_model,
    )
    if store.count() == 0:
        raise SystemExit(
            "O banco vetorial está vazio. Execute antes: python -m pontoativo_rag.ingestao"
        )
    return Retriever(
        EmbeddingProvider(settings.embedding_model), store, top_k=settings.top_k,
        reranker=reranker, distance_scale=settings.distance_scale,
    )


def criar_cliente(settings: Settings, *, num_predict: int | None = None) -> OllamaClient:
    return OllamaClient(
        settings.ollama_base_url,
        settings.ollama_model,
        settings.ollama_timeout_seconds,
        num_ctx=settings.ollama_num_ctx,
        num_predict=num_predict if num_predict is not None else settings.ollama_num_predict,
        keep_alive=settings.ollama_keep_alive,
    )
