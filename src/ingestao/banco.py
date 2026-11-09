"""Banco vetorial do PontoAtivo (Chroma, local e persistente).

O banco fica em dados/vetorial/ (fora do git). Há uma única coleção,
``pontoativo_fontes``, com a métrica de **cosseno**, que é a recomendada para
os embeddings normalizados do modelo multilingual-e5-base.

Os embeddings são gerados por nós (src/ingestao/embeddings.py) e passados ao
Chroma já prontos; por isso a coleção é criada com ``embedding_function=None``
e o Chroma nunca baixa nem usa um modelo próprio.
"""

from pathlib import Path

import chromadb

RAIZ = Path(__file__).resolve().parents[2]
CAMINHO_BANCO = RAIZ / "dados" / "vetorial"
NOME_COLECAO = "pontoativo_fontes"


def obter_cliente(caminho=None):
    """Abre (ou cria) o banco persistente na pasta indicada."""
    caminho = Path(caminho) if caminho else CAMINHO_BANCO
    caminho.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(caminho))


def recriar_colecao(cliente):
    """Apaga a coleção antiga (se houver) e cria uma nova, vazia, com cosseno.

    Recriar a cada ingestão evita chunks duplicados ou de versões antigas.
    """
    try:
        cliente.delete_collection(NOME_COLECAO)
    except Exception:
        pass  # não existia
    try:
        # Chroma 1.x
        return cliente.create_collection(
            name=NOME_COLECAO,
            configuration={"hnsw": {"space": "cosine"}},
            embedding_function=None,
        )
    except (TypeError, ValueError):
        # Chroma 0.x
        return cliente.create_collection(
            name=NOME_COLECAO,
            metadata={"hnsw:space": "cosine"},
            embedding_function=None,
        )


def obter_colecao(cliente):
    """Abre a coleção já criada pela ingestão."""
    return cliente.get_collection(name=NOME_COLECAO, embedding_function=None)
