"""Limpeza, deduplicação e, posteriormente, chunking dos documentos."""

from __future__ import annotations

import re
import hashlib
import json
import unicodedata
from collections.abc import Iterable
from pathlib import Path

from .modelos import EmbeddingSegment, NormalizedDocument, ParentChunk


# Versão da forma como o texto de entrada do embedding é montado. Ela entra no
# ID do segmento: mudar a estratégia invalida os vetores antigos na ingestão.
EMBEDDING_INPUT_VERSION = "titulo+secao+segmento+estrutura+entidade-v5"

# Caracteres de controle (exceto \n e \t) aparecem em PDFs mal codificados.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Marcadores de lista de fontes "Symbol"/"Wingdings" (área de uso privado).
_PRIVATE_BULLETS = re.compile(r"[\uf0a7\uf0b7\uf0d8\uf0fc\uf076]")


def normalize_text(text: str) -> str:
    """Remove ruído de espaço preservando limites de parágrafo."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _PRIVATE_BULLETS.sub("•", _CONTROL_CHARS.sub("", text))
    paragraphs = re.split(r"\n\s*\n+", text)
    normalized = [
        "\n".join(
            line.strip()
            for line in re.sub(r"[ \t\f\v]+", " ", item).split("\n")
            if line.strip()
        )
        for item in paragraphs
    ]
    return "\n\n".join(item for item in normalized if item)


def deduplicate_documents(
    documents: Iterable[NormalizedDocument],
) -> tuple[list[NormalizedDocument], dict[str, str]]:
    """Mantém a primeira fonte de cada conteúdo e registra as duplicadas."""
    unique: list[NormalizedDocument] = []
    owner_by_checksum: dict[str, str] = {}
    duplicates: dict[str, str] = {}
    for document in documents:
        owner = owner_by_checksum.get(document.checksum_sha256)
        if owner is not None:
            duplicates[document.source.source_id] = owner
            continue
        owner_by_checksum[document.checksum_sha256] = document.source.source_id
        unique.append(document)
    return unique, duplicates


def _word_windows(text: str, size: int, overlap: int = 0) -> list[str]:
    words = text.split()
    if not words:
        return []
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("A janela deve ser positiva e a sobreposição menor que ela.")
    step = size - overlap
    return [" ".join(words[start : start + size]) for start in range(0, len(words), step)]


def _stable_id(*parts: object) -> str:
    value = "|".join(str(part) for part in parts)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


# Títulos numerados em maiúsculas ("1.2 COP SETOR O", "1.2.1 EQUIPAMENTOS").
# Exigir maiúsculas evita tratar itens de lista ("1. Atividade Física") como títulos.
_NUMBERED_HEADING = re.compile(
    r"^(\d{1,2}(?:\.\d{1,2}){0,4})(\.|\s*[-–])?\s+(\S.{1,118})$"
)
# Títulos Markdown e títulos HTML convertidos para Markdown na extração.
_MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(\S.{0,148})$")
_MIN_UPPERCASE_RATIO = 0.7
_MIN_HEADING_LETTERS = 5
# Blocos com menos palavras (ex.: número de página isolado) são descartados.
_MIN_BLOCK_WORDS = 3
_SECTION_SEPARATOR = " > "
_LIST_LINE = re.compile(r"^(?:[-*•▪◦]|\d+[.)])\s+")


# Regiões administrativas do DF, com a grafia usada nos metadados. As compostas
# vêm antes das simples ("Sobradinho II" antes de "Sobradinho").
_REGIONS = (
    "Recanto das Emas", "Riacho Fundo II", "Riacho Fundo", "Sobradinho II", "Sobradinho",
    "São Sebastião", "Santa Maria", "Núcleo Bandeirante", "Vicente Pires", "Águas Claras",
    "Jardim Botânico", "Lago Norte", "Lago Sul", "Park Way", "Sol Nascente", "Plano Piloto",
    "Candangolândia", "Brazlândia", "Ceilândia", "Samambaia", "Taguatinga", "Planaltina",
    "Paranoá", "Itapoã", "Estrutural", "Cruzeiro", "Sudoeste", "Varjão", "Fercal",
    "Arniqueira", "Gama", "Guará",
)


def _fold(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in value if not unicodedata.combining(char))


_REGION_PATTERNS = tuple(
    (region, re.compile(rf"\b{re.escape(_fold(region))}\b")) for region in _REGIONS
)


def _section_region(section: str) -> str:
    """Região nomeada pela seção mais específica que cita uma RA.

    Documentos sobre um COP também descrevem outros ("1.3 COP SOBRADINHO" nas
    diretrizes do COP Setor O). Sem isto, esses trechos herdariam a região da
    fonte inteira. Retorna "" quando nenhuma seção nomeia uma RA.
    """
    for part in reversed(section.split(_SECTION_SEPARATOR)):
        folded = _fold(part)
        for region, pattern in _REGION_PATTERNS:
            if pattern.search(folded):
                return region
    return ""


def _entity_key(section: str, title: str) -> str:
    """Usa a seção mais específica como identidade recuperável do local."""
    value = section.split(_SECTION_SEPARATOR)[-1].strip() or title.strip()
    return re.sub(r"\W+", "-", value.casefold(), flags=re.UNICODE).strip("-")


def _structure_kind(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) >= 2 and sum(bool(_LIST_LINE.match(line)) for line in lines) >= 2:
        return "lista"
    if len(lines) >= 2 and sum(";" in line or "\t" in line for line in lines) >= 2:
        return "tabela"
    return "texto"


def detect_heading(line: str) -> tuple[int, str] | None:
    """Retorna (nível, título) se a linha for um título de seção."""
    line = line.strip()
    markdown = _MARKDOWN_HEADING.match(line)
    if markdown:
        return len(markdown.group(1)), markdown.group(2).strip()
    numbered = _NUMBERED_HEADING.match(line)
    if numbered:
        number, separator, title = numbered.groups()
        # "10 DIAS" ou linhas de tabela ("23 PARQUE ...") não são títulos:
        # número inteiro exige separador ("1." ou "1 -").
        if "." not in number and not separator:
            return None
        if title.rstrip().endswith((";", ",")):
            return None
        letters = [char for char in title if char.isalpha()]
        if len(letters) >= _MIN_HEADING_LETTERS:
            ratio = sum(char.isupper() for char in letters) / len(letters)
            if ratio >= _MIN_UPPERCASE_RATIO:
                return numbered.group(1).count(".") + 1, line
    return None


# Linha de tabela georreferenciada: "389 PONTO DE ENCONTRO COMUNITÁRIO SQNW 109 -15.74, -47.90".
_GEO_ROW = re.compile(r"^\d+\s+(.+?)\s+-?\d{1,3}\.\d+\s*,\s*-?\d{1,3}\.\d+\s*$")
_MIN_ROWS_PER_TYPE = 3


def _geo_row_key(description: str) -> str:
    return " ".join(description.split()[:2]).casefold()


def _geo_row_types(units: list[tuple[str, int | None]]) -> dict[str, str]:
    """Descobre o tipo de equipamento de cada grupo de linhas de uma tabela.

    Tabelas como "NÚMERO EQUIPAMENTO ENDEREÇO COORDENADAS" não têm subtítulos,
    então todos os trechos ficariam sem seção e quase idênticos para o modelo de
    embeddings. O tipo é o maior prefixo comum das descrições que começam pelas
    mesmas duas palavras ("PARQUE INFANTIL SQN 102" e "PARQUE INFANTIL SQS 204"
    dão "PARQUE INFANTIL"). Retorna {chave das duas palavras: tipo}.
    """
    groups: dict[str, list[list[str]]] = {}
    for text, _ in units:
        for line in text.split("\n"):
            row = _GEO_ROW.match(line.strip())
            if row:
                description = row.group(1)
                groups.setdefault(_geo_row_key(description), []).append(description.split())
    types: dict[str, str] = {}
    for key, rows in groups.items():
        if len(rows) < _MIN_ROWS_PER_TYPE:
            continue
        prefix = rows[0]
        for words in rows[1:]:
            size = 0
            while size < min(len(prefix), len(words)) and prefix[size] == words[size]:
                size += 1
            prefix = prefix[:size]
        if len(prefix) >= 2:
            types[key] = " ".join(prefix)
    return types


# Títulos que só certas fontes usam e que o detector geral não reconhece sem
# confundir com o texto de outras: {source_id: regra}.
HEADING_RULES = {
    "DOC-001": "maiusculas",  # Carta de Serviços: "PROGRAMA CENTROS OLÍMPICOS E / PARALÍMPICOS"
    "DOC-014": "lei",  # LIVRO, TÍTULO, CAPÍTULO, Seção + nome na linha seguinte
    "DOC-015": "lei",
    "DOC-003": "numerada",  # "1. Dos alunos e usuários acompanhantes", "7.1 Falta leve"
    "DOC-017": "numerada",  # "1. Introdução", "2.1 Em que consiste o Programa"
}
_LAW_HEADING = re.compile(r"^(LIVRO|T[ÍI]TULO|CAP[ÍI]TULO|Se[çc][ãa]o)\s+([IVXLCDM]+|[ÚU]nica|[ÚU]NICA)\b", re.I)
_LAW_LEVEL = {"livro": 1, "titulo": 2, "título": 2, "capitulo": 3, "capítulo": 3, "secao": 4, "seção": 4}
_NUMBERED_TITLE = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,3})\.?\s+([A-ZÀ-Ú][^;:]{2,90})$")


def _is_caps_line(line: str, max_words: int = 8) -> bool:
    letters = [c for c in line if c.isalpha()]
    words = line.split()
    return (
        1 <= len(words) <= max_words and len(letters) >= 4 and not any(c.isdigit() for c in line)
        and sum(c.isupper() for c in letters) / len(letters) >= 0.9
    )


def _prepare_lines(text: str, rule: str | None) -> str:
    """Junta o nome do título à linha do título, quando a fonte os separa."""
    if rule not in {"maiusculas", "lei"}:
        return text
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        line = lines[i].strip()
        if rule == "maiusculas" and _is_caps_line(line):
            parts = [line]
            while i + 1 < len(lines) and _is_caps_line(lines[i + 1].strip()):
                i += 1
                parts.append(lines[i].strip())
            out.append(" ".join(parts))
        elif rule == "lei" and _LAW_HEADING.match(line):
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if nxt and len(nxt.split()) <= 15 and not nxt.lower().startswith("art"):
                line, i = f"{line} – {nxt}", i + 1
            out.append(line)
        else:
            out.append(lines[i])
        i += 1
    return "\n".join(out)


def _rule_heading(line: str, rule: str | None) -> tuple[int, str] | None:
    line = line.strip()
    if (rule == "maiusculas" and len(line.split()) >= 2 and _is_caps_line(line, max_words=14)
            and sum(len(w) == 1 for w in line.split()) < 2):  # "CLASSIFICAÇÃO A B C D" é tabela
        return 1, line
    if rule == "lei":
        match = _LAW_HEADING.match(line)
        if match:
            kind = match.group(1).casefold()
            return _LAW_LEVEL.get(kind, 4), line
    if rule == "numerada":
        match = _NUMBERED_TITLE.match(line)
        if match and len(line.split()) <= 12 and not line.endswith((".", ",")):
            return match.group(1).count(".") + 1, line
    return None


def _split_by_sections(
    units: list[tuple[str, int | None]],
    rule: str | None = None,
) -> list[tuple[str, int | None, str]]:
    """Divide o texto em blocos (texto, página, caminho da seção).

    O caminho da seção é mantido entre páginas: um bloco que começa no meio de
    uma seção continua rotulado com o título dela. Cada título inicia um bloco
    novo, para que duas seções não compartilhem o mesmo chunk; títulos
    consecutivos sem texto entre eles ficam juntos.

    Em tabelas georreferenciadas sem subtítulos, a troca de tipo de equipamento
    funciona como um título implícito (ver ``_geo_row_types``).
    """
    row_types = _geo_row_types(units)
    stack: list[tuple[int, str]] = []
    blocks: list[tuple[str, int | None, str]] = []
    for text, page_number in units:
        lines: list[str] = []
        has_body = False
        block_section = _SECTION_SEPARATOR.join(title for _, title in stack)
        for line in text.split("\n"):
            heading = detect_heading(line) or _rule_heading(line, rule)
            row = _GEO_ROW.match(line.strip()) if row_types else None
            row_type = row_types.get(_geo_row_key(row.group(1))) if row else None
            if row_type and (not stack or stack[-1][1] != row_type):
                if has_body:
                    blocks.append(("\n".join(lines), page_number, block_section))
                    lines, has_body = [], False
                stack = [(1, row_type)]
                block_section = row_type
            if heading is not None:
                if has_body:
                    blocks.append(("\n".join(lines), page_number, block_section))
                    lines, has_body = [], False
                level, title = heading
                while stack and stack[-1][0] >= level:
                    stack.pop()
                stack.append((level, title))
                if not has_body:
                    block_section = _SECTION_SEPARATOR.join(t for _, t in stack)
            elif line.strip():
                has_body = True
            lines.append(line)
        if has_body:
            blocks.append(("\n".join(lines), page_number, block_section))
    # Títulos sem corpo não viram chunk: continuam no caminho da seção seguinte.
    return [block for block in blocks if len(block[0].split()) >= _MIN_BLOCK_WORDS]


_SEPARATORS = ("\n\n", "\n", " ")  # parágrafo, linha, palavra


def _group_blocks(
    blocks: list[tuple[str, int | None, str]], target: int
) -> list[tuple[str, int | None, int | None, str]]:
    """Junta blocos consecutivos da mesma seção-mãe até ~``target`` palavras.

    Um bloco entra no grupo atual se sua seção for a mesma do primeiro bloco
    do grupo ou uma subseção dela ("1.2 COP X > 1.2.1 EQUIPAMENTOS" entra no
    grupo "1.2 COP X"); "1.3 COP Y" nunca entra. Assim, o título de um local
    fica no mesmo chunk que a lista de equipamentos e modalidades, mesmo que
    ela continue na página seguinte. Retorna (texto, pág. inicial, pág. final, seção).
    """
    groups: list[tuple[str, int | None, int | None, str]] = []
    texts: list[str] = []
    anchor = ""
    first_page = last_page = None
    words = 0

    def flush() -> None:
        if texts:
            groups.append(("\n\n".join(texts), first_page, last_page, anchor))

    for text, page, section in blocks:
        size = len(text.split())
        same_family = section == anchor or section.startswith(anchor + _SECTION_SEPARATOR)
        if texts and same_family and words + size <= target:
            texts.append(text)
            last_page = page
            words += size
            continue
        flush()
        texts, anchor, first_page, last_page, words = [text], section, page, page, size
    flush()
    return groups


def _units(
    text: str, budget: int, joiner: str = "\n\n", separators: tuple[str, ...] = _SEPARATORS
) -> list[tuple[str, str]]:
    """Decompõe o texto em unidades de no máximo ``budget`` palavras.

    Tenta primeiro manter parágrafos inteiros; se um parágrafo for grande
    demais, usa linhas; em último caso, palavras. Cada unidade guarda o
    separador que a liga à anterior, para remontar o texto fielmente.
    """
    if len(text.split()) <= budget:
        return [(text, joiner)]
    for position, separator in enumerate(separators):
        parts = [part for part in text.split(separator) if part.strip()]
        if len(parts) > 1:
            units: list[tuple[str, str]] = []
            for part in parts:
                sub = _units(part, budget, separator, separators[position + 1 :])
                units.append((sub[0][0], separator))
                units.extend(sub[1:])
            return units
    return [(text, joiner)]


def _pack(text: str, target: int, overlap: int) -> list[str]:
    """Agrupa unidades inteiras em chunks de até ``target`` palavras.

    Cada chunk seguinte do mesmo bloco começa com as últimas ``overlap``
    palavras do anterior, preservando o contexto na fronteira.
    """
    if overlap < 0 or overlap >= target:
        raise ValueError("A sobreposição deve ser menor que o tamanho do chunk.")
    chunks: list[str] = []
    current, count = "", 0
    for unit, joiner in _units(text.strip(), target - overlap):
        words = len(unit.split())
        if current and count + words > target:
            chunks.append(current)
            tail = " ".join(current.split()[-overlap:]) if overlap else ""
            current, count = tail, len(tail.split())
        current = f"{current}{joiner}{unit.strip()}" if current else unit.strip()
        count += words
    if current.strip():
        chunks.append(current)
    return [normalize_text(chunk) for chunk in chunks]


def create_parent_chunks(
    document: NormalizedDocument,
    target_tokens: int = 450,
    overlap_tokens: int = 50,
) -> list[ParentChunk]:
    """Cria chunks citáveis respeitando seções e parágrafos.

    - um chunk nunca mistura seções irmãs (ex.: dois COPs diferentes);
    - subseções da mesma seção são agrupadas até ~``target_tokens`` palavras,
      inclusive atravessando páginas (registradas em ``page_number``/``page_end``);
    - cada chunk registra o caminho da seção a que pertence.
    """
    units = (
        [(page.text, page.page_number) for page in document.pages]
        if document.pages
        else [(document.text, None)]
    )
    chunks: list[ParentChunk] = []
    rule = HEADING_RULES.get(document.source.source_id)
    units = [(_prepare_lines(text, rule), page) for text, page in units]
    groups = _group_blocks(_split_by_sections(units, rule), target_tokens)
    for text, page_number, page_end, section in groups:
        region = document.source.administrative_region
        # Só fontes de uma RA do DF trocam a região pela da seção: em fontes
        # nacionais, "Vasco da Gama" ou "Santa Maria" não são RAs do DF.
        if region:
            region = _section_region(section) or region
        for window in _pack(text, target_tokens, overlap_tokens):
            index = len(chunks)
            chunk_id = _stable_id(
                document.source.source_id,
                document.checksum_sha256,
                page_number,
                section,
                index,
                window,
                # Na região: trocar a região muda o ID e força gravar o metadado novo.
                region,
            )
            chunks.append(
                ParentChunk(
                    chunk_id=chunk_id,
                    source_id=document.source.source_id,
                    index=index,
                    text=window,
                    title=document.source.title,
                    institution=document.source.institution,
                    location=document.source.location,
                    checksum_sha256=document.checksum_sha256,
                    page_number=page_number,
                    page_end=page_end if page_end != page_number else None,
                    section=section,
                    administrative_region=region,
                    sport_modality=document.source.sport_modality,
                    verification_status=document.source.verification_status,
                    freshness_status=document.source.freshness_status,
                    volatility=document.source.volatility,
                    source_type=document.source.document_type,
                    entity_key=_entity_key(section, document.source.title),
                    structure_kind=_structure_kind(window),
                )
            )
    return chunks


def create_embedding_segments(
    chunk: ParentChunk, max_tokens: int = 120
) -> list[EmbeddingSegment]:
    """Divide um chunk-pai em entradas compatíveis com a janela do modelo."""
    segments: list[EmbeddingSegment] = []
    for index, text in enumerate(_word_windows(chunk.text, max_tokens)):
        segments.append(
            EmbeddingSegment(
                segment_id=_stable_id(
                    chunk.chunk_id, index, text, EMBEDDING_INPUT_VERSION
                ),
                parent_chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                index=index,
                text=text,
                parent_text=chunk.text,
                title=chunk.title,
                institution=chunk.institution,
                location=chunk.location,
                checksum_sha256=chunk.checksum_sha256,
                page_number=chunk.page_number,
                page_end=chunk.page_end,
                section=chunk.section,
                administrative_region=chunk.administrative_region,
                sport_modality=chunk.sport_modality,
                verification_status=chunk.verification_status,
                freshness_status=chunk.freshness_status,
                volatility=chunk.volatility,
                source_type=chunk.source_type,
                entity_key=chunk.entity_key,
                structure_kind=chunk.structure_kind,
            )
        )
    return segments


def write_chunks_jsonl(chunks: Iterable[ParentChunk], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")
