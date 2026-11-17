from pontoativo_rag.modelos import NormalizedDocument, SourceRecord
from pontoativo_rag.processamento import deduplicate_documents, normalize_text


def _document(source_id: str, checksum: str) -> NormalizedDocument:
    return NormalizedDocument(
        source=SourceRecord(
            source_id=source_id,
            title=source_id,
            institution="GDF",
            location=f"{source_id}.txt",
            document_type="txt",
            subject="esporte",
            verification_status="verificado",
        ),
        text="Texto normalizado.",
        checksum_sha256=checksum,
    )


def test_normalizacao_remove_ruido_sem_unir_paragrafos() -> None:
    raw = "  Primeiro   parágrafo.\r\n\r\n\r\n Segundo\tparágrafo.  "

    assert normalize_text(raw) == "Primeiro parágrafo.\n\nSegundo parágrafo."


def test_deduplicacao_mantem_primeiro_documento_por_checksum() -> None:
    first = _document("fonte-001", "abc")
    duplicate = _document("fonte-002", "abc")
    distinct = _document("fonte-003", "def")

    unique, duplicates = deduplicate_documents([first, duplicate, distinct])

    assert [item.source.source_id for item in unique] == ["fonte-001", "fonte-003"]
    assert duplicates == {"fonte-002": "fonte-001"}


def test_normalizacao_remove_controles_e_marcadores_de_pdf() -> None:
    from pontoativo_rag.processamento import normalize_text

    assert normalize_text("atribui\x00ções\n Piscina") == "atribuições\n• Piscina"
