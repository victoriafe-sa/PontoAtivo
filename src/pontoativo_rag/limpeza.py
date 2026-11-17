"""Limpeza do texto extraído, entre a carga das fontes e a divisão em trechos.

Cada regra corrige um defeito medido na base (relatório de 12/11/2026):

- cabeçalhos e rodapés que se repetem na maioria das páginas de um PDF;
- linhas de sumário com pontilhado e anotações sem conteúdo das leis;
- a lista nacional de clubes do CPB (DOC-021), da qual só os do DF importam;
- títulos colados ao item seguinte no Manual de Uso dos COPs (DOC-003);
- palavras sem espaço no PDF das diretrizes do COP Samambaia (DOC-005);
- trechos idênticos vindos de fontes diferentes (modelos de termo de colaboração).
"""
from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import replace

from .modelos import DocumentPage, NormalizedDocument, ParentChunk

# Linha de sumário: texto seguido de pontilhado (e, em geral, o número da página).
_TOC_LINE = re.compile(r"\.{8,}|…{3,}")
# Anotações das leis do Planalto que não dizem nada do conteúdo.
_NOISE_LINES = {"(promulgação partes vetadas)", "(vetado)", "(vetado).", "(revogado)", "(revogado)."}
_REPEAT_SHARE = 0.6  # linha presente em 60% das páginas ou mais = cabeçalho ou rodapé
_REPEAT_MIN_PAGES = 5
_EDGE_LINES = 2  # cabeçalho e rodapé ficam nas primeiras e últimas linhas da página


def _line_key(line: str) -> str:
    # Números variam entre páginas ("PÁGINA 71", "14:34"); comparam-se como iguais.
    return re.sub(r"\d+", "#", " ".join(line.split())).casefold()


def _drop_lines(text: str, keep: Callable[[str], bool]) -> str:
    return "\n".join(line for line in text.split("\n") if keep(line))


def _with_pages(document: NormalizedDocument, transform: Callable[[str], str]) -> NormalizedDocument:
    """Aplica a transformação a cada página (ou ao texto, se não houver páginas)."""
    if not document.pages:
        return replace(document, text=transform(document.text))
    pages = tuple(
        DocumentPage(page_number=p.page_number, text=transform(p.text), section=p.section)
        for p in document.pages
    )
    pages = tuple(p for p in pages if p.text.strip())
    return replace(document, pages=pages, text="\n\n".join(p.text for p in pages))


def repeated_lines(pages: Iterable[DocumentPage]) -> set[str]:
    """Chaves das linhas que aparecem na maioria das páginas (cabeçalhos e rodapés)."""
    pages = list(pages)
    if len(pages) < _REPEAT_MIN_PAGES:
        return set()
    seen = Counter()
    for page in pages:
        lines = [line for line in page.text.split("\n") if line.strip()]
        edges = lines[:_EDGE_LINES] + lines[-_EDGE_LINES:]
        seen.update({_line_key(line) for line in edges if len(line.split()) >= 3})
    return {key for key, count in seen.items() if count / len(pages) >= _REPEAT_SHARE}


def remove_noise(document: NormalizedDocument) -> NormalizedDocument:
    header_footer = repeated_lines(document.pages)

    # Só as bordas de cada página são comparadas com os cabeçalhos: no meio da
    # página, uma linha de tabela que difere só nos números ("SQN 102 -15.77")
    # é conteúdo, não rodapé.
    def edge_filter(text: str) -> str:
        lines = text.split("\n")
        filled = [i for i, line in enumerate(lines) if line.strip()]
        edges = set(filled[:_EDGE_LINES] + filled[-_EDGE_LINES:])
        return "\n".join(
            line for i, line in enumerate(lines)
            if not (i in edges and _line_key(line.strip()) in header_footer)
        )

    def keep(line: str) -> bool:
        stripped = line.strip()
        if _TOC_LINE.search(stripped):
            return False
        if stripped.casefold() in _NOISE_LINES:
            return False
        return True

    return _with_pages(document, lambda text: _drop_lines(edge_filter(text), keep))


# --- DOC-021: só os clubes do Distrito Federal ---------------------------------
_DF_CLUB = re.compile(r"\(61\)|CEP 7[0-3]\.\d{3}-\d{3}|Distrito Federal|Bras[ií]lia")


def keep_df_clubs(text: str) -> str:
    """Mantém a orientação do CPB e só os clubes do DF (DDD 61, CEP 70–73 mil)."""
    head, marker, rest = text.partition("\n### ")
    if not marker:
        return text
    clubs = ("### " + rest).split("\n### ")
    clubs = [c if c.startswith("### ") else "### " + c for c in clubs]
    kept = [c for c in clubs if _DF_CLUB.search(c)]
    note = "Clubes filiados ao CPB no Distrito Federal (a lista nacional completa está no site do CPB):"
    return head.rstrip() + "\n\n" + note + ("\n\n" + "\n".join(kept) if kept else "")


# --- DOC-003: "acompanhantes1.1 Aluno" -> "acompanhantes\n1.1 Aluno" -----------------
_GLUED_NUMBER = re.compile(r"(?<=[A-Za-zÀ-ÿ.;:)])(?=\d{1,2}(?:\.\d{1,2}){1,3}\s)")


def split_glued_numbering(text: str) -> str:
    return _GLUED_NUMBER.sub("\n", text)


# Regras específicas por fonte, aplicadas depois da limpeza geral.
SOURCE_RULES: dict[str, Callable[[str], str]] = {
    "DOC-021": keep_df_clubs,
    "DOC-003": split_glued_numbering,
}


def clean_document(document: NormalizedDocument) -> NormalizedDocument:
    document = remove_noise(document)
    rule = SOURCE_RULES.get(document.source.source_id)
    return _with_pages(document, rule) if rule else document


# --- Palavras coladas (DOC-005) ---------------------------------------------------
GLUED_SOURCES = {"DOC-005"}
_WORD = re.compile(r"[A-Za-zÀ-ÿ]+")
_SHORT_WORDS = {"a", "e", "o"}


def _vocabulary(documents: Iterable[NormalizedDocument], exclude: str) -> Counter:
    vocab = Counter()
    for document in documents:
        if document.source.source_id != exclude:
            vocab.update(word.casefold() for word in _WORD.findall(document.text))
    return vocab


def split_glued_word(token: str, vocab: Counter) -> str:
    """Separa "deentrada" em "de entrada" se a palavra não existe e as partes existem.

    O vocabulário vem das outras fontes. Entre as divisões possíveis, vale a de
    partes mais frequentes ("crianças e", não "criança se").
    """
    low = token.casefold()
    if len(low) < 5 or vocab[low]:
        return token

    def known(part: str) -> bool:
        return part in _SHORT_WORDS or (len(part) >= 2 and vocab[part] >= 3)

    best = None
    for i in range(1, len(low)):
        left, right = low[:i], low[i:]
        if known(left) and known(right):
            score = vocab[left] * vocab[right]
            if best is None or score > best[0]:
                best = (score, i)
    return token if best is None else token[: best[1]] + " " + token[best[1]:]


def fix_glued_words(documents: list[NormalizedDocument]) -> list[NormalizedDocument]:
    fixed = []
    for document in documents:
        if document.source.source_id in GLUED_SOURCES:
            vocab = _vocabulary(documents, document.source.source_id)
            document = _with_pages(
                document, lambda text: _WORD.sub(lambda m: split_glued_word(m.group(0), vocab), text)
            )
        fixed.append(document)
    return fixed


def clean_documents(documents: list[NormalizedDocument]) -> list[NormalizedDocument]:
    return fix_glued_words([clean_document(d) for d in documents])


# --- Trechos idênticos entre fontes -------------------------------------------------
def drop_duplicate_chunks(chunks: list[ParentChunk]) -> tuple[list[ParentChunk], int]:
    """Mantém a primeira ocorrência de um texto repetido em outra fonte."""
    seen: dict[str, str] = {}
    kept, dropped = [], 0
    for chunk in chunks:
        key = " ".join(chunk.text.split()).casefold()
        if key in seen and seen[key] != chunk.source_id:
            dropped += 1
            continue
        seen.setdefault(key, chunk.source_id)
        kept.append(chunk)
    return kept, dropped
