from pontoativo_rag.armazenamento import VectorHit
from pontoativo_rag.recuperacao import Retriever


class QueryEmbedder:
    def encode(self, texts):
        return [[1.0, 0.0] for _ in texts]


class QueryStore:
    def __init__(self):
        self.requested = []

    def query(self, vector, *, n_results, filters=None):
        self.requested.append(n_results)
        return [
            VectorHit(
                "s1",
                "segmento 1",
                {
                    "parent_chunk_id": "p1",
                    "parent_text": "Texto completo do primeiro chunk.",
                    "source_id": "fonte-1",
                    "title": "Documento 1",
                    "location": "https://df.gov.br/1",
                    "page_number": 2,
                },
                0.10,
            ),
            VectorHit(
                "s2",
                "segmento 2",
                {
                    "parent_chunk_id": "p1",
                    "parent_text": "Texto completo do primeiro chunk.",
                    "source_id": "fonte-1",
                    "title": "Documento 1",
                    "location": "https://df.gov.br/1",
                    "page_number": 2,
                },
                0.20,
            ),
            VectorHit(
                "s3",
                "segmento 3",
                {
                    "parent_chunk_id": "p2",
                    "parent_text": "Texto completo do segundo chunk.",
                    "source_id": "fonte-2",
                    "title": "Documento 2",
                    "location": "https://df.gov.br/2",
                },
                0.15,
            ),
        ]


def test_recuperacao_agrega_segmentos_por_chunk_e_ordena_distancia() -> None:
    store = QueryStore()
    retriever = Retriever(QueryEmbedder(), store)

    results = retriever.search("Onde praticar esporte?", top_k=2)

    assert [result.chunk_id for result in results] == ["p1", "p2"]
    assert results[0].distance == 0.10
    assert results[0].page_number == 2
    assert results[0].source_id == "fonte-1"
    assert max(store.requested) <= 200


def test_recuperacao_rejeita_pergunta_vazia() -> None:
    retriever = Retriever(QueryEmbedder(), QueryStore())

    try:
        retriever.search("   ")
    except ValueError as error:
        assert "vazia" in str(error)
    else:
        raise AssertionError("pergunta vazia deveria falhar")


class LexicalStore:
    def query(self, vector, *, n_results, filters=None):
        return [
            VectorHit(
                "generic",
                "atividades e regras gerais",
                {
                    "parent_chunk_id": "generic",
                    "parent_text": "Atividades e regras gerais do programa.",
                    "title": "Manual geral",
                    "source_id": "geral",
                },
                0.20,
            ),
            VectorHit(
                "exact",
                "Centro Olímpico e Paralímpico de Ceilândia",
                {
                    "parent_chunk_id": "exact",
                    "parent_text": "Centro Olímpico e Paralímpico de Ceilândia.",
                    "title": "Centros Olímpicos do Distrito Federal",
                    "source_id": "cop",
                },
                0.27,
            ),
        ]


def test_reranking_lexical_prioriza_local_exato_em_empate_semantico() -> None:
    retriever = Retriever(QueryEmbedder(), LexicalStore())

    results = retriever.search(
        "Onde fica o Centro Olímpico e Paralímpico de Ceilândia?", top_k=2
    )

    assert [result.chunk_id for result in results] == ["exact", "generic"]


class RegionStore:
    def query(self, vector, *, n_results, filters=None):
        return [
            VectorHit("generic", "PEC no DF", {"parent_chunk_id":"generic", "parent_text":"PEC no DF", "source_id":"geral"}, 0.30),
            VectorHit("target", "PEC listado", {"parent_chunk_id":"target", "parent_text":"Endereços dos PECs", "source_id":"plano", "administrative_region":"Plano Piloto"}, 0.45),
        ]


def test_regiao_exata_desempata_sem_bonus_excessivo() -> None:
    results = Retriever(QueryEmbedder(), RegionStore()).search(
        "Onde ficam os PECs do Plano Piloto?", top_k=2
    )

    assert results[0].chunk_id == "target"
    assert results[0].region_match is True
    assert results[1].region_match is False


class FilterStore:
    """Simula um banco em que apenas um trecho possui região registrada."""

    def __init__(self):
        self.hits = [
            VectorHit("a", "a", {"parent_chunk_id": "pa", "source_id": "f-a",
                                  "administrative_region": "Ceilândia"}, 0.30),
            VectorHit("b", "b", {"parent_chunk_id": "pb", "source_id": "f-b"}, 0.20),
            VectorHit("c", "c", {"parent_chunk_id": "pc", "source_id": "f-c",
                                  "administrative_region": "Gama"}, 0.10),
        ]

    def query(self, vector, *, n_results, filters=None):
        if not filters:
            return self.hits
        return [h for h in self.hits
                if all(h.metadata.get(k) == v for k, v in filters.items())]


def test_filtro_mantem_trechos_sem_metadado_e_exclui_regiao_diferente() -> None:
    retriever = Retriever(QueryEmbedder(), FilterStore())

    results = retriever.search("PEC", filters={"administrative_region": "Ceilândia"})

    ids = [r.chunk_id for r in results]
    assert ids == ["pb", "pa"]
    assert results[0].filter_metadata_missing is True
    assert results[1].filter_metadata_missing is False


def test_similaridade_e_complemento_da_distancia() -> None:
    result = Retriever(QueryEmbedder(), QueryStore()).search("x", top_k=1)[0]

    assert abs(result.similarity - 0.90) < 1e-9


def test_reranker_vetorial_preserva_ordem_da_distancia() -> None:
    retriever = Retriever(QueryEmbedder(), LexicalStore(), reranker="vetorial")

    results = retriever.search(
        "Onde fica o Centro Olímpico e Paralímpico de Ceilândia?", top_k=2
    )

    assert [result.chunk_id for result in results] == ["generic", "exact"]


def test_bonus_da_regiao_acompanha_a_escala_do_modelo() -> None:
    # Com o E5 as distâncias são ~1/4 das do MiniLM: a mesma diferença de 0,15
    # é grande demais para a região compensar, e a ordem segue a semântica.
    pergunta = "Onde ficam os PECs do Plano Piloto?"
    minilm = Retriever(QueryEmbedder(), RegionStore()).search(pergunta, top_k=2)
    e5 = Retriever(QueryEmbedder(), RegionStore(), distance_scale=0.12 / 0.45).search(pergunta, top_k=2)
    assert minilm[0].chunk_id == "target"
    assert e5[0].chunk_id == "generic"
