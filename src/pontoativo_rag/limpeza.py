"""Limpeza do texto extraído, entre a carga das fontes e a divisão em trechos.

Cada regra corrige um defeito medido na base (relatório de 12/11/2026):

- cabeçalhos e rodapés que se repetem na maioria das páginas de um PDF;
- linhas de sumário com pontilhado e anotações sem conteúdo das leis;
- a lista nacional de clubes do CPB (DOC-021), da qual só os do DF importam;
- títulos colados ao item seguinte no Manual de Uso dos COPs (DOC-003);
- palavras sem espaço no PDF das diretrizes do COP Samambaia (DOC-005);
- trechos idênticos vindos de fontes diferentes (modelos de termo de colaboração).

Auditoria de 17/11/2026:

- link de impressão do SEI no rodapé de cada página do DOC-006;
- abertura das páginas HTML antes do título (data "às 09h56 - Atualizado em",
  título da aba do navegador, item de menu) e o botão "Compartilhe" (DOC-024);
- palavras coladas por vírgula e em sequência no DOC-005
  ("evitar,nosjogosdesportivoscoletivos");
- trechos sem conteúdo, só com títulos ou artigos vetados (DOC-015).
"""
from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import replace

from .modelos import DocumentPage, NormalizedDocument, ParentChunk

# Linha de sumário: texto seguido de pontilhado (e, em geral, o número da página).
_TOC_LINE = re.compile(r"\.{8,}|…{3,}")
# Anotações das leis do Planalto que não dizem nada do conteúdo.
_NOISE_LINES = {"(promulgação partes vetadas)", "(vetado)", "(vetado).", "(revogado)", "(revogado).",
                ":", "compartilhe"}
# Rodapé do SEI com o link de impressão do documento.
_SEI_PRINT = re.compile(r"sei\.df\.gov\.br/sei/controlador\.php")
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
        if _SEI_PRINT.search(stripped):
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


# --- Páginas HTML: o que vem antes do título ------------------------------------------
_HTML_HEADING = re.compile(r"#{1,2} \S")
_PREAMBLE_LINES = 4


def drop_html_preamble(text: str) -> str:
    """Remove o que antecede o primeiro título da página, se ele vier logo no início.

    Ali ficam a data de publicação do portal, o título da aba do navegador e
    itens de menu ("Agricultura"); a data já está no catálogo e o título se repete
    no próprio cabeçalho. Sem título nas primeiras linhas, nada é removido.
    """
    lines = text.split("\n")
    filled = [i for i, line in enumerate(lines) if line.strip()]
    for i in filled[:_PREAMBLE_LINES + 1]:
        if _HTML_HEADING.match(lines[i].strip()):
            return "\n".join(lines[i:])
    return text


# Regras específicas por fonte, aplicadas depois da limpeza geral.
SOURCE_RULES: dict[str, Callable[[str], str]] = {
    "DOC-021": keep_df_clubs,
    "DOC-003": split_glued_numbering,
}


def clean_document(document: NormalizedDocument) -> NormalizedDocument:
    document = remove_noise(document)
    if document.source.document_type == "html":
        document = _with_pages(document, drop_html_preamble)
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

    O vocabulário vem das outras fontes. Vale a divisão com menos partes e, entre
    elas, a de partes mais frequentes ("crianças e", não "criança se"). Sequências
    longas também se separam: "nosjogoscoletivos" vira "nos jogos coletivos".
    """
    low = token.casefold()
    if len(low) < 5 or vocab[low]:
        return token

    def known(part: str) -> bool:
        return part in _SHORT_WORDS or (len(part) >= 2 and vocab[part] >= 3)

    # best[i] = (partes, -frequência, cortes) da melhor divisão de low[:i]
    best: list[tuple[int, float, tuple[int, ...]] | None] = [None] * (len(low) + 1)
    best[0] = (0, 0.0, ())
    for end in range(1, len(low) + 1):
        for start in range(end):
            part = low[start:end]
            if best[start] is None or not known(part):
                continue
            parts, neg_score, cuts = best[start]
            candidate = (parts + 1, neg_score - math.log(vocab[part] + 1), cuts + (end,))
            if best[end] is None or candidate[:2] < best[end][:2]:
                best[end] = candidate
    result = best[len(low)]
    if result is None or result[0] < 2:
        return token
    pieces, start = [], 0
    for end in result[2]:
        pieces.append(token[start:end])
        start = end
    return " ".join(pieces)


_GLUED_COMMA = re.compile(r"(?<=[A-Za-zÀ-ÿ]),(?=[A-Za-zÀ-ÿ])")
# "dos12anos" -> "dos 12 anos"; horários e medidas ("7h40", "21h50", "50min") ficam.
_GLUED_DIGITS = re.compile(r"(?<=[A-Za-zÀ-ÿ])(?<!\dh)(?=\d)|(?<=\d)(?!min\b)(?=[A-Za-zÀ-ÿ]{3,})")


# Termos raros demais nas outras fontes para a separação automática.
GLUED_BY_HAND = {
    "nosjogosdesportivoscoletivos": "nos jogos desportivos coletivos",
    "asquaisexigemperfeição": "as quais exigem perfeição",
}


def unglue(text: str, vocab: Counter) -> str:
    text = _GLUED_DIGITS.sub(" ", _GLUED_COMMA.sub(", ", text))
    return _WORD.sub(lambda m: GLUED_BY_HAND.get(m.group(0)) or split_glued_word(m.group(0), vocab), text)


def fix_glued_words(documents: list[NormalizedDocument]) -> list[NormalizedDocument]:
    fixed = []
    for document in documents:
        if document.source.source_id in GLUED_SOURCES:
            vocab = _vocabulary(documents, document.source.source_id)
            document = _with_pages(document, lambda text: unglue(text, vocab))
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


# --- Trechos sem conteúdo -------------------------------------------------------------
# Títulos de leis e artigos vazios ou vetados: "Seção V", "Art. 24.", "Art. 20. (VETADO)."
_EMPTY_LINE = re.compile(
    r"(?i)(?:t[íi]tulo|cap[íi]tulo|se[çc][ãa]o|subse[çc][ãa]o)\s+[ivxlc\d]+\b.*"
    r"|art\.\s*\d+[º°o]?(?:-[a-z])?\.?(?:\s*\((?:vetado|revogado)\)\.?)?"
)
_MIN_CONTENT_WORDS = 3


def has_content(chunk: ParentChunk) -> bool:
    """Falso para trechos só com títulos ou artigos vazios ou vetados."""
    rest = [line for line in chunk.text.split("\n") if line.strip() and not _EMPTY_LINE.fullmatch(line.strip())]
    return len(" ".join(rest).split()) >= _MIN_CONTENT_WORDS


def drop_empty_chunks(chunks: list[ParentChunk]) -> tuple[list[ParentChunk], int]:
    kept = [chunk for chunk in chunks if has_content(chunk)]
    return kept, len(chunks) - len(kept)
