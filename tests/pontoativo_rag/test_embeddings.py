from pontoativo_rag.embeddings import EmbeddingProvider


class FakeModel:
    def encode(self, texts, **kwargs):
        return [[float(len(text)), 1.0] for text in texts]


def test_embedding_provider_codifica_em_lotes_e_normaliza() -> None:
    provider = EmbeddingProvider(
        "modelo-teste", batch_size=2, model_factory=lambda _: FakeModel()
    )

    vectors = provider.encode(["um", "texto maior", "fim"])

    assert vectors == [[2.0, 1.0], [11.0, 1.0], [3.0, 1.0]]


def test_embedding_provider_aceita_lista_vazia_sem_carregar_modelo() -> None:
    def fail_if_loaded(_):
        raise AssertionError("modelo não deveria ser carregado")

    provider = EmbeddingProvider("modelo-teste", model_factory=fail_if_loaded)

    assert provider.encode([]) == []



def test_e5_prefixos_para_documento_e_consulta():
    entradas = []
    class Captura:
        def encode(self, texts, **kwargs):
            entradas.extend(texts)
            return [[1.0] for _ in texts]
    provider = EmbeddingProvider("intfloat/multilingual-e5-base", model_factory=lambda _: Captura())
    provider.encode(["edital"])
    provider.encode_query(["como participar?"])
    assert entradas == ["passage: edital", "query: como participar?"]
