from pathlib import Path
from datetime import date

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from pontoativo_rag.carregamento import (
    CatalogError,
    DocumentLoadError,
    load_catalog,
    load_document,
    write_documents_jsonl,
)
from pontoativo_rag.modelos import SourceRecord
from pontoativo_rag.modelos import classify_source_freshness


def _source(path: Path, source_id: str = "fonte-001") -> SourceRecord:
    return SourceRecord(
        source_id=source_id,
        title="Documento de teste",
        institution="Instituição de teste",
        location=str(path),
        document_type=path.suffix.lstrip("."),
        subject="esporte",
        verification_status="teste",
    )


def _write_text_pdf(path: Path, text: str) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {NameObject("/F1"): font_ref}
            )
        }
    )
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as file:
        writer.write(file)


@pytest.mark.parametrize("suffix", [".txt", ".md"])
def test_carrega_texto_e_markdown(suffix: str, tmp_path: Path) -> None:
    path = tmp_path / f"documento{suffix}"
    path.write_text("Título\n\nInformação sobre esporte inclusivo.", encoding="utf-8")

    document = load_document(path, _source(path))

    assert "esporte inclusivo" in document.text
    assert document.source.source_id == "fonte-001"
    assert len(document.checksum_sha256) == 64


def test_html_em_windows_1252_sem_charset_preserva_acentos(tmp_path: Path) -> None:
    path = tmp_path / "lei.html"
    path.write_bytes("<html><body><p>Lei Brasileira de Inclusão: promoção e acessibilidade.</p></body></html>"
                     .encode("cp1252"))

    document = load_document(path, _source(path))

    assert "Inclusão" in document.text and "promoção" in document.text
    assert "�" not in document.text


def test_html_respeita_o_charset_declarado(tmp_path: Path) -> None:
    path = tmp_path / "pagina.html"
    path.write_bytes('<html><head><meta charset="iso-8859-1"></head><body><p>Educação física</p></body></html>'
                     .encode("latin-1"))

    assert "Educação física" in load_document(path, _source(path)).text


def test_recorte_mantem_so_o_documento_entre_os_marcadores() -> None:
    from pontoativo_rag.carregamento import _crop_pages
    from pontoativo_rag.modelos import DocumentPage

    pages = (
        DocumentPage(1, "Ato da CODHAB.\nEDITAL Nº 1\nRegras da matrícula."),
        DocumentPage(2, "Prazos e vagas."),
        DocumentPage(3, "Assinatura do secretário.\nSECRETARIA DO MEIO AMBIENTE\nAviso alheio."),
    )

    text, kept = _crop_pages(pages, "EDITAL Nº 1", "SECRETARIA DO MEIO AMBIENTE", name="x.pdf")

    assert [page.page_number for page in kept] == [1, 2, 3]
    assert text.startswith("EDITAL Nº 1") and text.endswith("Assinatura do secretário.")
    assert "CODHAB" not in text and "Aviso alheio" not in text


def test_recorte_sem_marcador_falha_em_vez_de_indexar_tudo() -> None:
    from pontoativo_rag.carregamento import _crop_pages
    from pontoativo_rag.modelos import DocumentPage

    with pytest.raises(DocumentLoadError):
        _crop_pages((DocumentPage(1, "Outro documento."),), "EDITAL", "FIM", name="x.pdf")


def test_html_remove_scripts_e_preserva_links(tmp_path: Path) -> None:
    path = tmp_path / "pagina.html"
    path.write_text(
        "<html><body><h1>PEC</h1><script>ignorar()</script>"
        '<p>Fonte <a href="https://df.gov.br/pec">oficial</a></p></body></html>',
        encoding="utf-8",
    )

    document = load_document(path, _source(path))

    assert "PEC" in document.text
    assert "ignorar" not in document.text
    assert "oficial (https://df.gov.br/pec)" in document.text


def test_pdf_preserva_numero_da_pagina(tmp_path: Path) -> None:
    path = tmp_path / "texto.pdf"
    _write_text_pdf(path, "Centro esportivo acessivel")

    document = load_document(path, _source(path))

    assert document.pages[0].page_number == 1
    assert "Centro esportivo acessivel" in document.pages[0].text


def test_rejeita_arquivo_vazio(tmp_path: Path) -> None:
    path = tmp_path / "vazio.txt"
    path.write_text("   ", encoding="utf-8")

    with pytest.raises(DocumentLoadError, match="vazio"):
        load_document(path, _source(path))


def test_pdf_sem_texto_indica_necessidade_de_ocr(tmp_path: Path) -> None:
    path = tmp_path / "digitalizado.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    with path.open("wb") as file:
        writer.write(file)

    with pytest.raises(DocumentLoadError, match="OCR"):
        load_document(path, _source(path))


def test_catalogo_e_jsonl_preservam_origem(tmp_path: Path) -> None:
    document_path = tmp_path / "fonte.txt"
    document_path.write_text("Texto da fonte.", encoding="utf-8")
    catalog_path = tmp_path / "catalogo.csv"
    catalog_path.write_text(
        "source_id,title,institution,location,document_type,subject,verification_status\n"
        f"fonte-001,Título,GDF,{document_path},txt,esporte,verificado\n",
        encoding="utf-8",
    )

    sources = load_catalog(catalog_path)
    document = load_document(document_path, sources[0])
    output = tmp_path / "documentos.jsonl"
    write_documents_jsonl([document], output)

    saved = output.read_text(encoding="utf-8")
    assert '"source_id": "fonte-001"' in saved
    assert '"checksum_sha256"' in saved


def test_classifica_atualidade_por_volatilidade_e_data() -> None:
    source = SourceRecord(
        source_id="lei-001",
        title="Lei de acessibilidade",
        institution="GDF",
        location="https://df.gov.br/lei",
        document_type="html",
        subject="legislação",
        verification_status="aprovada",
        publication_date="2023-01-01",
    )

    classified = classify_source_freshness(source, today=date(2026, 11, 10))

    assert classified.volatility == "baixa"
    assert classified.freshness_status == "em_revisao"
    assert classified.review_interval_days == 730


def test_catalogo_rejeita_id_duplicado(tmp_path: Path) -> None:
    catalog_path = tmp_path / "catalogo.csv"
    catalog_path.write_text(
        "source_id,title,institution,location,document_type,subject,verification_status\n"
        "x,A,GDF,a.txt,txt,esporte,verificado\n"
        "x,B,GDF,b.txt,txt,esporte,verificado\n",
        encoding="utf-8",
    )

    with pytest.raises(CatalogError, match="duplicado"):
        load_catalog(catalog_path)


def test_html_converte_titulos_e_remove_secoes_de_portal(tmp_path: Path) -> None:
    path = tmp_path / "noticia.html"
    path.write_text(
        "<html><body><main><h1>Novo PEC</h1><p>O PEC tem rampa de acesso.</p>"
        "<h2>Leia também</h2><p>Outra notícia sem relação.</p>"
        "<h2>Serviço</h2><p>Endereço informado na nota.</p></main></body></html>",
        encoding="utf-8",
    )

    document = load_document(path, _source(path))

    assert "# Novo PEC" in document.text
    assert "Outra notícia" not in document.text
    assert "## Serviço" in document.text
