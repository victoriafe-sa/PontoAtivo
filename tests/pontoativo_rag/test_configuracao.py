import pytest

from pathlib import Path

from pontoativo_rag.configuracao import Settings


def test_settings_usa_defaults_relativos_ao_projeto(tmp_path: Path) -> None:
    settings = Settings.from_env(root=tmp_path)

    assert settings.root == tmp_path.resolve()
    assert settings.sources_dir == tmp_path.resolve() / "dados" / "fontes_originais"
    assert settings.data_dir == tmp_path.resolve() / "dados"
    assert settings.vector_db_dir == tmp_path.resolve() / "dados" / "rag" / "vetorial"
    assert settings.embedding_model == (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    assert settings.parent_chunk_tokens == 450
    assert settings.chunk_overlap_tokens == 50
    assert settings.embedding_segment_tokens == 120
    assert settings.top_k == 4


def test_settings_cria_diretorios_somente_quando_solicitado(tmp_path: Path) -> None:
    settings = Settings.from_env(root=tmp_path)

    assert not settings.data_dir.exists()
    settings.ensure_directories()

    assert settings.sources_dir.is_dir()
    assert settings.data_dir.is_dir()
    assert settings.vector_db_dir.is_dir()
    assert settings.documentation_dir.is_dir()
    assert settings.evidence_dir.is_dir()


def test_settings_le_variaveis_de_ambiente(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PONTOATIVO_TOP_K", "3")
    monkeypatch.setenv("PONTOATIVO_OLLAMA_MODEL", "qwen2.5:3b")
    monkeypatch.setenv("PONTOATIVO_OLLAMA_TIMEOUT", "45")

    settings = Settings.from_env(root=tmp_path)

    assert settings.top_k == 3
    assert settings.ollama_model == "qwen2.5:3b"
    assert settings.ollama_timeout_seconds == 45.0



def test_settings_de_geracao_tem_padroes_e_aceitam_ambiente(tmp_path: Path, monkeypatch) -> None:
    defaults = Settings.from_env(root=tmp_path)
    assert defaults.ollama_num_ctx == 8192
    assert defaults.ollama_num_predict == 400
    assert defaults.ollama_keep_alive == "10m"
    assert defaults.structured_answers is True
    assert defaults.max_generation_attempts == 3

    monkeypatch.setenv("PONTOATIVO_OLLAMA_NUM_CTX", "4096")
    monkeypatch.setenv("PONTOATIVO_OLLAMA_NUM_PREDICT", "250")
    monkeypatch.setenv("PONTOATIVO_OLLAMA_KEEP_ALIVE", "30m")
    monkeypatch.setenv("PONTOATIVO_RESPOSTA_ESTRUTURADA", "não")
    monkeypatch.setenv("PONTOATIVO_TENTATIVAS_GERACAO", "1")
    custom = Settings.from_env(root=tmp_path)

    assert custom.ollama_num_ctx == 4096
    assert custom.ollama_num_predict == 250
    assert custom.ollama_keep_alive == "30m"
    assert custom.structured_answers is False
    assert custom.max_generation_attempts == 1


def test_resposta_estruturada_rejeita_valor_ambiguo(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PONTOATIVO_RESPOSTA_ESTRUTURADA", "talvez")

    with pytest.raises(ValueError):
        Settings.from_env(root=tmp_path)


def test_modelo_do_mapa_usa_o_mesmo_das_respostas_quando_vazio(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PONTOATIVO_OLLAMA_MODEL", "gemma4:12b")
    monkeypatch.delenv("PONTOATIVO_OLLAMA_MODEL_MAPA", raising=False)
    assert Settings.from_env(root=tmp_path).map_model == "gemma4:12b"
    monkeypatch.setenv("PONTOATIVO_OLLAMA_MODEL_MAPA", "  ")
    assert Settings.from_env(root=tmp_path).map_model == "gemma4:12b"


def test_modelo_do_mapa_pode_ser_outro(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PONTOATIVO_OLLAMA_MODEL", "gemma4:12b")
    monkeypatch.setenv("PONTOATIVO_OLLAMA_MODEL_MAPA", "qwen3:4b")
    settings = Settings.from_env(root=tmp_path)
    assert settings.map_model == "qwen3:4b"
    assert settings.ollama_model == "gemma4:12b"
