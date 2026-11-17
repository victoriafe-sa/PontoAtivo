"""Extração de PDF, HTML, Markdown e texto com rastreabilidade."""

from __future__ import annotations

import hashlib
import csv
import json
import re
from dataclasses import fields
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from pypdf import PdfReader

from .modelos import (
    DocumentPage,
    NormalizedDocument,
    SourceRecord,
    classify_source_freshness,
)
from .processamento import normalize_text


class DocumentLoadError(ValueError):
    """Erro recuperável associado a uma única fonte."""


class CatalogError(ValueError):
    """Erro estrutural no catálogo de fontes."""


_REQUIRED_CATALOG_COLUMNS = {
    "source_id",
    "title",
    "institution",
    "location",
    "document_type",
    "subject",
    "verification_status",
}


def load_catalog(path: Path) -> list[SourceRecord]:
    """Lê e valida IDs e campos mínimos do catálogo CSV."""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = set(reader.fieldnames or ())
        missing = _REQUIRED_CATALOG_COLUMNS - columns
        if missing:
            raise CatalogError("Colunas obrigatórias ausentes: " + ", ".join(sorted(missing)))
        records: list[SourceRecord] = []
        seen: set[str] = set()
        valid_fields = {item.name for item in fields(SourceRecord)}
        for line_number, row in enumerate(reader, start=2):
            source_id = (row.get("source_id") or "").strip()
            if not source_id:
                raise CatalogError(f"source_id vazio na linha {line_number}")
            if source_id in seen:
                raise CatalogError(f"source_id duplicado: {source_id}")
            seen.add(source_id)
            values = {key: (row.get(key) or "").strip() for key in valid_fields}
            records.append(classify_source_freshness(SourceRecord(**values)))
    return records


def write_documents_jsonl(
    documents: Iterable[NormalizedDocument], output: Path
) -> None:
    """Persiste a representação normalizada para auditoria."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for document in documents:
            file.write(json.dumps(document.to_dict(), ensure_ascii=False) + "\n")


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _page_has_images(page: Any) -> bool:
    resources = page.get("/Resources")
    xobjects = resources.get("/XObject") if resources else None
    if not xobjects:
        return False
    for reference in xobjects.values():
        obj = reference.get_object()
        if obj.get("/Subtype") == "/Image":
            return True
    return False


def _load_pdf(
    path: Path,
) -> tuple[str, tuple[DocumentPage, ...], tuple[int, ...], tuple[int, ...]]:
    pages: list[DocumentPage] = []
    missing: list[int] = []
    graphical: list[int] = []
    try:
        reader = PdfReader(path)
        for number, page in enumerate(reader.pages, start=1):
            text = normalize_text(page.extract_text() or "")
            if text:
                pages.append(DocumentPage(page_number=number, text=text))
            elif _page_has_images(page):
                graphical.append(number)
            else:
                missing.append(number)
    except Exception as exc:
        raise DocumentLoadError(f"PDF ilegível: {path.name}: {exc}") from exc
    if not pages:
        raise DocumentLoadError(
            f"PDF sem texto extraível: {path.name}; pode necessitar de OCR."
        )
    return (
        "\n\n".join(page.text for page in pages),
        tuple(pages),
        tuple(missing),
        tuple(graphical),
    )


# Fontes publicadas dentro de um recorte do Diário Oficial trazem atos de outros
# órgãos antes e depois do documento. {source_id: (início, fim)}: o texto começa
# no marcador de início e termina antes do marcador de fim.
RECORTES = {
    # Edital de matrícula dos COPs (DODF nº 50, 14/03/2025, p. 71–74). Antes dele
    # vêm atos da CODHAB e um extrato da SEL com a Terracap; depois, atos da
    # Secretaria do Meio Ambiente e da ADASA.
    "DOC-002": ("EDITAL DE MATRÍCULA Nº 001/2025", "SECRETARIA DE ESTADO DO MEIO AMBIENTE"),
}


def _crop_pages(
    pages: tuple[DocumentPage, ...], start: str, end: str, *, name: str
) -> tuple[str, tuple[DocumentPage, ...]]:
    """Mantém só o trecho entre ``start`` (incluído) e ``end`` (excluído).

    Falha se algum marcador não existir: um PDF diferente do esperado não pode
    ser indexado inteiro sem aviso.
    """
    full = "\n\n".join(page.text for page in pages)
    if full.count(start) != 1 or full.count(end) != 1 or full.index(start) > full.index(end):
        raise DocumentLoadError(f"Recorte não encontrado em {name}: confira os marcadores.")
    kept: list[DocumentPage] = []
    inside = False
    for page in pages:
        text = page.text
        if not inside:
            if start not in text:
                continue
            text, inside = text[text.index(start):], True
        if end in text:
            text = text[: text.index(end)].rstrip()
            if text:
                kept.append(DocumentPage(page_number=page.page_number, text=text, section=page.section))
            break
        kept.append(DocumentPage(page_number=page.page_number, text=text, section=page.section))
    return "\n\n".join(page.text for page in kept), tuple(kept)


# Elementos de página que não carregam conteúdo do documento.
_HTML_NOISE = ["script", "style", "noscript", "nav", "header", "footer", "aside",
               "form", "iframe", "svg", "button"]
# Contêineres de conteúdo principal, do mais específico ao mais genérico.
# ``section.box-internas`` é o corpo das notícias da Agência Brasília; sem ele,
# a lista de "outras notícias" do portal entraria no documento.
_CONTENT_SELECTORS = ("section.box-internas", "article", "main")
# Abaixo deste número de palavras o contêiner é considerado incompleto e o
# próximo é tentado; por fim usa-se a página inteira, para não perder conteúdo.
_MIN_CONTENT_WORDS = 100


# Seções de portais que listam outras páginas, não conteúdo do documento.
_NOISE_SECTIONS = {
    "leia também", "veja também", "tags", "notícias relacionadas",
    "compartilhe", "conteúdo relacionado", "acesse mais notícias",
}


def _drop_noise_sections(text: str) -> str:
    """Remove do texto as seções Markdown cujo título está em _NOISE_SECTIONS."""
    kept: list[str] = []
    skipping_level: int | None = None
    for line in text.split("\n"):
        stripped = line.strip()
        level = len(stripped) - len(stripped.lstrip("#")) if stripped.startswith("#") else 0
        if level and stripped[level:level + 1] == " ":
            label = stripped[level:].strip().casefold()
            if skipping_level is not None and level <= skipping_level:
                skipping_level = None
            if skipping_level is None and label in _NOISE_SECTIONS:
                skipping_level = level
                continue
        if skipping_level is None:
            kept.append(line)
    return "\n".join(kept)


def _main_content(soup: BeautifulSoup):
    for selector in _CONTENT_SELECTORS:
        element = soup.select_one(selector)
        if element and len(element.get_text(" ", strip=True).split()) >= _MIN_CONTENT_WORDS:
            return element
    return soup.body or soup


_DECLARED_CHARSET = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?([\w.:-]+)""", re.IGNORECASE)


def _decode_html(raw: bytes) -> str:
    """Decodifica o HTML sem trocar acentos por "�".

    Ordem: a codificação declarada no próprio arquivo; senão UTF-8; e, se o
    UTF-8 for inválido, Windows-1252. Páginas antigas do Planalto (leis) vêm em
    Windows-1252 sem declarar o charset, e a leitura forçada em UTF-8
    substituía milhares de acentos.
    """
    declared = _DECLARED_CHARSET.search(raw[:4096])
    candidates = [declared.group(1).decode("ascii", "ignore")] if declared else []
    candidates += ["utf-8", "cp1252"]
    for encoding in candidates:
        try:
            return raw.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("cp1252", errors="replace")


def _load_html(path: Path) -> str:
    soup = BeautifulSoup(_decode_html(path.read_bytes()), "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for element in soup(_HTML_NOISE):
        element.decompose()
    root = _main_content(soup)
    # Títulos HTML viram títulos Markdown, reconhecidos pelo chunking por seção.
    for heading in root.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        level = int(heading.name[1])
        label = heading.get_text(" ", strip=True)
        heading.replace_with(f"\n\n{'#' * level} {label}\n\n" if label else "")
    for anchor in root.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True)
        href = anchor["href"].strip()
        # Links externos com rótulo são preservados; âncoras internas,
        # javascript e botões sem texto (ex.: "compartilhar") não.
        if not label:
            anchor.decompose()
        elif href.startswith(("http://", "https://")) and href not in label:
            anchor.replace_with(f"{label} ({href})")
        else:
            anchor.replace_with(label)
    text = _drop_noise_sections(root.get_text("\n", strip=True))
    if title and title not in text[: len(title) + 200]:
        text = f"{title}\n\n{text}"
    return normalize_text(text)


def load_document(path: Path, source: SourceRecord) -> NormalizedDocument:
    """Extrai uma fonte local e mantém seu registro de origem."""
    path = path.resolve()
    if not path.is_file():
        raise DocumentLoadError(f"Arquivo não encontrado: {path.name}")

    suffix = path.suffix.lower()
    pages: tuple[DocumentPage, ...] = ()
    missing: tuple[int, ...] = ()
    graphical: tuple[int, ...] = ()
    if suffix == ".pdf":
        text, pages, missing, graphical = _load_pdf(path)
        if source.source_id in RECORTES:
            text, pages = _crop_pages(pages, *RECORTES[source.source_id], name=path.name)
    elif suffix in {".html", ".htm"}:
        text = _load_html(path)
    elif suffix in {".txt", ".md", ".markdown"}:
        text = normalize_text(path.read_text(encoding="utf-8"))
    else:
        raise DocumentLoadError(f"Formato não suportado: {suffix or '(sem extensão)'}")

    if not text:
        raise DocumentLoadError(f"Arquivo vazio ou sem texto útil: {path.name}")
    return NormalizedDocument(
        source=source,
        text=text,
        checksum_sha256=_checksum(path),
        pages=pages,
        missing_pages=missing,
        graphical_pages=graphical,
    )
