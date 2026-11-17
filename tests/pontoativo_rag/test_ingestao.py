from pathlib import Path

from pontoativo_rag.armazenamento import ChromaStore
from pontoativo_rag.configuracao import Settings
from pontoativo_rag.ingestao import ingest_catalog


class SmallEmbedder:
    def encode(self, texts):
        return [[float(len(text)), 1.0] for text in texts]


def test_ingestao_e_idempotente_e_registra_erros_por_fonte(tmp_path: Path) -> None:
    settings = Settings.from_env(root=tmp_path)
    settings.ensure_directories()
    valid = settings.sources_dir / "valida.txt"
    valid.write_text("Espaço esportivo público em Ceilândia.", encoding="utf-8")
    catalog = settings.catalog_path
    catalog.write_text(
        "source_id,title,institution,location,document_type,subject,verification_status\n"
        "fonte-1,Documento,GDF,dados/rag/fontes/valida.txt,txt,esporte,verificado\n"
        "fonte-2,Ausente,GDF,dados/rag/fontes/ausente.txt,txt,esporte,verificado\n",
        encoding="utf-8",
    )
    store = ChromaStore(settings.vector_db_dir, "teste_ingestao")

    first = ingest_catalog(settings, catalog, embedder=SmallEmbedder(), store=store)
    second = ingest_catalog(settings, catalog, embedder=SmallEmbedder(), store=store)

    assert first.documents_loaded == 1
    assert first.documents_failed == 1
    assert first.parent_chunks == 1
    assert first.embedding_segments == 1
    assert "fonte-2" in first.errors
    assert second.embedding_segments == 1
    assert store.count() == 1
    assert (settings.generated_dir / "documentos_normalizados.jsonl").is_file()
    assert (settings.generated_dir / "chunks.jsonl").is_file()



class CountingEmbedder(SmallEmbedder):
    def __init__(self):
        self.encoded = 0

    def encode(self, texts):
        self.encoded += len(texts)
        return super().encode(texts)


def _catalog(settings: Settings, rows: str) -> Path:
    catalog = settings.catalog_path
    catalog.write_text(
        "source_id,title,institution,location,local_path,document_type,subject,verification_status\n"
        + rows,
        encoding="utf-8",
    )
    return catalog


def test_ingestao_nao_recodifica_e_remove_vetores_de_fonte_alterada(tmp_path: Path) -> None:
    settings = Settings.from_env(root=tmp_path)
    settings.ensure_directories()
    source = settings.sources_dir / "fonte.txt"
    source.write_text("Versão original do regulamento.", encoding="utf-8")
    catalog = _catalog(
        settings,
        "f1,Regulamento,SEL,https://df.gov.br/r,dados/rag/fontes/fonte.txt,txt,regras,aprovada\n",
    )
    store = ChromaStore(settings.vector_db_dir, "teste_alteracao")
    embedder = CountingEmbedder()

    ingest_catalog(settings, catalog, embedder=embedder, store=store)
    unchanged = ingest_catalog(settings, catalog, embedder=embedder, store=store)
    assert embedder.encoded == 1
    assert unchanged.segments_reused == 1

    source.write_text("Versão revisada do regulamento.", encoding="utf-8")
    changed = ingest_catalog(settings, catalog, embedder=embedder, store=store)

    assert changed.segments_encoded == 1
    assert changed.segments_removed == 1
    assert store.count() == 1
    hit = store.query([1.0, 1.0], n_results=1)[0]
    assert "revisada" in hit.metadata["parent_text"]
    # A citação usa a URL original, não o caminho local.
    assert hit.metadata["location"] == "https://df.gov.br/r"


def test_ingestao_exclui_fonte_nao_verificada(tmp_path: Path) -> None:
    settings = Settings.from_env(root=tmp_path)
    settings.ensure_directories()
    (settings.sources_dir / "a.txt").write_text("Texto A.", encoding="utf-8")
    catalog = _catalog(
        settings,
        "f1,A,SEL,https://df.gov.br/a,dados/rag/fontes/a.txt,txt,x,pendente\n",
    )
    store = ChromaStore(settings.vector_db_dir, "teste_status")

    report = ingest_catalog(settings, catalog, embedder=SmallEmbedder(), store=store)

    assert report.documents_skipped == 1
    assert "f1" in report.skipped
    assert store.count() == 0
