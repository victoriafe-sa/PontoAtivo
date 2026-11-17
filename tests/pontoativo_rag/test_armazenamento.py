from pathlib import Path

from pontoativo_rag.armazenamento import ChromaStore
from pontoativo_rag.modelos import EmbeddingSegment


def _segment(segment_id: str, parent_id: str, region: str) -> EmbeddingSegment:
    return EmbeddingSegment(
        segment_id=segment_id,
        parent_chunk_id=parent_id,
        source_id=f"fonte-{parent_id}",
        index=0,
        text=f"segmento {segment_id}",
        parent_text=f"texto completo {parent_id}",
        title=f"Documento {parent_id}",
        institution="GDF",
        location=f"https://df.gov.br/{parent_id}",
        checksum_sha256=f"hash-{parent_id}",
        administrative_region=region,
        verification_status="verificado",
    )


def test_chroma_persiste_metadados_e_upsert_e_idempotente(tmp_path: Path) -> None:
    segments = [_segment("s1", "p1", "Ceilândia"), _segment("s2", "p2", "Gama")]
    vectors = [[1.0, 0.0], [0.0, 1.0]]

    store = ChromaStore(tmp_path / "chroma", "teste")
    store.upsert(segments, vectors)
    store.upsert(segments, vectors)
    reopened = ChromaStore(tmp_path / "chroma", "teste")

    assert reopened.count() == 2
    hits = reopened.query([1.0, 0.0], n_results=2)
    assert hits[0].segment_id == "s1"
    assert hits[0].metadata["parent_chunk_id"] == "p1"
    assert hits[0].distance <= hits[1].distance


def test_chroma_aplica_filtro_quando_fornecido(tmp_path: Path) -> None:
    store = ChromaStore(tmp_path / "chroma", "teste")
    store.upsert(
        [_segment("s1", "p1", "Ceilândia"), _segment("s2", "p2", "Gama")],
        [[1.0, 0.0], [0.0, 1.0]],
    )

    hits = store.query(
        [1.0, 0.0],
        n_results=2,
        filters={"administrative_region": "Gama"},
    )

    assert [hit.segment_id for hit in hits] == ["s2"]


def test_chroma_recusa_modelo_de_embedding_diferente(tmp_path: Path) -> None:
    import pytest

    from pontoativo_rag.armazenamento import EmbeddingModelMismatch

    ChromaStore(tmp_path / "chroma", "teste", embedding_model="modelo-a")

    with pytest.raises(EmbeddingModelMismatch):
        ChromaStore(tmp_path / "chroma", "teste", embedding_model="modelo-b")
