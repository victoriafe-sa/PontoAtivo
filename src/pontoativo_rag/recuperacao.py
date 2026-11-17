"""Recuperação semântica: pergunta -> vetor -> segmentos -> chunks citáveis."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any, Protocol, Sequence

from .armazenamento import VectorHit


# Para cada chunk desejado buscamos alguns segmentos a mais, pois vários
# segmentos podem pertencer ao mesmo chunk-pai e serão agregados.
# The local collection is small enough to inspect a broad candidate window.
# This preserves lexical matches that can rank far below semantic neighbors.
# Janela suficientemente ampla para agregar segmentos irmãos sem consultar
# quase toda a coleção a cada pergunta. Com top_k=5, são até 250 candidatos.
SEGMENTS_PER_CHUNK = 50
EXPANDED_SEGMENTS_PER_CHUNK = 200
# Sem nenhum trecho com pelo menos 3/4 dos termos da pergunta, a janela é ampliada.
# Com 0,50, uma notícia que repetia metade dos termos impedia a ampliação e
# escondia a tabela de PECs do Plano Piloto (Q12).
STRONG_LEXICAL_OVERLAP = 0.75
SECTION_MATCH_BONUS = 0.10
# Os bônus da busca híbrida foram medidos com o MiniLM, cujo limiar de abstenção
# é 0,45. Outros modelos espalham as distâncias em outra escala (o E5 fica entre
# 0,06 e 0,21), então os bônus são multiplicados por ``distance_scale``
# (limiar do modelo ÷ 0,45). Com o MiniLM, a escala é 1 e nada muda.
REFERENCE_MAX_DISTANCE = 0.45
_TOKEN = re.compile(r"[a-z0-9]{3,}", re.IGNORECASE)
_STOPWORDS = frozenset(
    "a ao aos as com da das de do dos e em entre para por que qual quais "
    "um uma uns umas no nos na nas onde há ha".split()
)


class QueryEmbedder(Protocol):
    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...


class QueryStore(Protocol):
    def query(
        self, vector, *, n_results: int, filters: dict[str, str] | None = None
    ) -> list[VectorHit]: ...


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    """Trecho citável devolvido ao usuário e ao gerador.

    ``distance`` é a distância cosseno do segmento mais próximo do chunk:
    0 indica vetores idênticos e valores maiores indicam menor proximidade.
    Não é uma probabilidade de a informação estar correta.
    """

    chunk_id: str
    source_id: str
    title: str
    institution: str
    location: str
    text: str
    distance: float
    matched_segments: int
    page_number: int | None = None
    page_end: int | None = None
    section: str = ""
    administrative_region: str = ""
    verification_status: str = ""
    filter_metadata_missing: bool = False
    lexical_overlap: float = 0.0
    freshness_status: str = ""
    source_type: str = ""
    entity_key: str = ""
    structure_kind: str = ""
    region_match: bool = False

    @property
    def similarity(self) -> float:
        """Similaridade cosseno (1 - distância), apenas para leitura humana."""
        return 1.0 - self.distance

    @property
    def pages(self) -> str:
        """Página ou intervalo de páginas, para citação ("21" ou "21–22")."""
        if not self.page_number:
            return ""
        if self.page_end and self.page_end != self.page_number:
            return f"{self.page_number}–{self.page_end}"
        return str(self.page_number)

    def reference(self) -> str:
        page = f", p. {self.pages}" if self.pages else ""
        section = f", seção {self.section}" if self.section else ""
        return f"{self.source_id} — {self.title}{page}{section} — {self.location}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _aggregate(
    hits: Sequence[VectorHit],
    *,
    missing_filter_keys: set[str] | None = None,
    query_terms: set[str] | None = None,
    scale: float = 1.0,
) -> list[RetrievedChunk]:
    grouped: dict[str, RetrievedChunk] = {}
    for hit in hits:
        meta = hit.metadata
        parent_id = str(meta.get("parent_chunk_id") or hit.segment_id)
        previous = grouped.get(parent_id)
        if previous is not None:
            grouped[parent_id] = RetrievedChunk(
                **{
                    **previous.to_dict(),
                    "distance": min(previous.distance, hit.distance),
                    "matched_segments": previous.matched_segments + 1,
                }
            )
            continue
        page = meta.get("page_number")
        page_end = meta.get("page_end")
        grouped[parent_id] = RetrievedChunk(
            chunk_id=parent_id,
            source_id=str(meta.get("source_id", "")),
            title=str(meta.get("title", "")),
            institution=str(meta.get("institution", "")),
            location=str(meta.get("location", "")),
            text=str(meta.get("parent_text") or hit.text),
            distance=hit.distance,
            matched_segments=1,
            page_number=int(page) if page not in (None, "") else None,
            page_end=int(page_end) if page_end not in (None, "") else None,
            section=str(meta.get("section", "")),
            administrative_region=str(meta.get("administrative_region", "")),
            verification_status=str(meta.get("verification_status", "")),
            freshness_status=str(meta.get("freshness_status", "")),
            source_type=str(meta.get("source_type", "")),
            entity_key=str(meta.get("entity_key", "")),
            structure_kind=str(meta.get("structure_kind", "")),
            filter_metadata_missing=bool(
                missing_filter_keys
                and any(key not in meta for key in missing_filter_keys)
            ),
        )
    if not query_terms:
        return sorted(grouped.values(), key=lambda chunk: chunk.distance)

    def exact_region_match(chunk: RetrievedChunk) -> bool:
        region_terms = _tokens(chunk.administrative_region)
        return len(region_terms) >= 2 and region_terms <= query_terms

    def rerank_key(chunk: RetrievedChunk) -> tuple[float, float]:
        searchable = _tokens(
            " ".join(
                (
                    chunk.title,
                    chunk.section,
                    chunk.text,
                    chunk.location,
                    chunk.administrative_region,
                )
            )
        )
        overlap = len(query_terms & searchable) / len(query_terms)
        region_match = exact_region_match(chunk)
        # A lexical match can correct a near-tie from the vector search, but
        # cannot rescue a distant result that lacks semantic similarity.
        score = chunk.distance - scale * min(0.12, 0.12 * overlap)
        # A pergunta que cita o nome da seção mais específica do trecho ("faltas
        # graves" e a seção "7.3 Falta Grave") aponta para ele mesmo quando o
        # embedding, diluído pelo resto do texto, o deixa mais longe.
        section_terms = _tokens(chunk.section.split(" > ")[-1])
        if len(query_terms & section_terms) >= 2:
            score -= scale * SECTION_MATCH_BONUS
        if region_match:
            # Região ajuda a desempatar, mas não pode superar sozinha uma
            # diferença semântica grande.
            score -= scale * 0.18
        return score, chunk.distance

    ranked = sorted(grouped.values(), key=rerank_key)
    return [
        RetrievedChunk(
            **{
                **chunk.to_dict(),
                "lexical_overlap": _lexical_overlap(chunk, query_terms),
                "region_match": exact_region_match(chunk),
            }
        )
        for chunk in ranked
    ]


def _singular(token: str) -> str:
    # Plural regular simples: "pontos" casa com "ponto", "quadras" com "quadra".
    return token[:-1] if len(token) > 4 and token.endswith("s") and not token.endswith("ss") else token


def _tokens(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return {
        _singular(token.lower())
        for token in _TOKEN.findall(normalized)
        if token.lower() not in _STOPWORDS
    }


def _lexical_overlap(chunk: RetrievedChunk, query_terms: set[str]) -> float:
    searchable = _tokens(
        " ".join(
            (
                chunk.title,
                chunk.section,
                chunk.text,
                chunk.location,
                chunk.administrative_region,
            )
        )
    )
    return len(query_terms & searchable) / len(query_terms) if query_terms else 0.0


class Retriever:
    def __init__(
        self,
        embedder: QueryEmbedder,
        store: QueryStore,
        *,
        top_k: int = 5,
        reranker: str = "hibrido",
        distance_scale: float = 1.0,
    ):
        if reranker not in {"hibrido", "vetorial"}:
            raise ValueError("reranker deve ser 'hibrido' ou 'vetorial'")
        self.embedder = embedder
        self.store = store
        self.top_k = top_k
        self.reranker = reranker
        self.distance_scale = distance_scale

    def search(
        self,
        question: str,
        top_k: int | None = None,
        filters: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        """Retorna até ``top_k`` chunks, do mais próximo ao menos próximo.

        Com filtros, trechos que não possuem o campo filtrado também são
        mantidos (marcados), para que a ausência de metadado não esconda
        documentos possivelmente relevantes.
        """
        question = question.strip()
        if not question:
            raise ValueError("A pergunta está vazia.")
        k = top_k or self.top_k
        encode_query = getattr(self.embedder, "encode_query", self.embedder.encode)
        vector = encode_query([question])[0]
        n_segments = k * SEGMENTS_PER_CHUNK
        clean_filters = {key: value for key, value in (filters or {}).items() if value}

        hits = self.store.query(vector, n_results=n_segments, filters=clean_filters or None)
        if clean_filters:
            unfiltered = self.store.query(vector, n_results=n_segments, filters=None)
            seen = {hit.segment_id for hit in hits}
            hits = list(hits) + [
                hit
                for hit in unfiltered
                if hit.segment_id not in seen
                and any(key not in hit.metadata for key in clean_filters)
            ]
        if self.reranker == "vetorial":
            chunks = _aggregate(hits, missing_filter_keys=set(clean_filters) or None)
            return chunks[:k]
        chunks = _aggregate(
            hits,
            missing_filter_keys=set(clean_filters) or None,
            query_terms=_tokens(question),
            scale=self.distance_scale,
        )
        # A janela curta é o caminho normal. Só amplia a consulta quando a
        # janela foi preenchida e nenhum resultado apresenta correspondência
        # lexical forte; assim, buscas difíceis mantêm recall sem varrer a
        # coleção inteira para toda pergunta.
        if (
            len(hits) >= n_segments
            and chunks
            and max(chunk.lexical_overlap for chunk in chunks) < STRONG_LEXICAL_OVERLAP
        ):
            expanded_n = k * EXPANDED_SEGMENTS_PER_CHUNK
            expanded_hits = self.store.query(
                vector, n_results=expanded_n, filters=clean_filters or None
            )
            if clean_filters:
                seen = {hit.segment_id for hit in expanded_hits}
                expanded_unfiltered = self.store.query(
                    vector, n_results=expanded_n, filters=None
                )
                expanded_hits = list(expanded_hits) + [
                    hit
                    for hit in expanded_unfiltered
                    if hit.segment_id not in seen
                    and any(key not in hit.metadata for key in clean_filters)
                ]
            chunks = _aggregate(
                expanded_hits,
                missing_filter_keys=set(clean_filters) or None,
                query_terms=_tokens(question),
                scale=self.distance_scale,
            )
        return chunks[:k]
