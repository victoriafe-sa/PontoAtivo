"""Configuração central do projeto, sem caminhos específicos da máquina."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_EMBEDDING_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def _load_dotenv(root: Path) -> None:
    """Carrega ``.env`` quando python-dotenv estiver instalado."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(root / ".env", override=False)


def _env_int(name: str, default: int, *, minimum: int = 1) -> int:
    value = int(os.getenv(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} deve ser maior ou igual a {minimum}.")
    return value


def _env_float(name: str, default: float, *, minimum: float = 0.0) -> float:
    value = float(os.getenv(name, str(default)))
    if value <= minimum:
        raise ValueError(f"{name} deve ser maior que {minimum}.")
    return value


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    normalized = value.strip().casefold()
    if normalized in {"1", "true", "sim", "s", "yes", "on"}:
        return True
    if normalized in {"0", "false", "nao", "não", "n", "no", "off"}:
        return False
    raise ValueError(f"{name} deve ser verdadeiro (1/sim) ou falso (0/não).")


@dataclass(frozen=True, slots=True)
class Settings:
    """Valores usados por todos os componentes do protótipo."""

    root: Path
    sources_dir: Path
    data_dir: Path
    vector_db_dir: Path
    documentation_dir: Path
    evidence_dir: Path
    embedding_model: str
    collection_name: str
    parent_chunk_tokens: int
    chunk_overlap_tokens: int
    embedding_segment_tokens: int
    top_k: int
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: float
    max_distance: float
    ollama_num_ctx: int = 8192
    ollama_num_predict: int = 400
    ollama_keep_alive: str = "10m"
    structured_answers: bool = True
    max_generation_attempts: int = 3
    # Modelo da barra do mapa (só classifica a pergunta); vazio = o mesmo das respostas.
    ollama_map_model: str = ""

    @classmethod
    def from_env(cls, root: Path | None = None) -> "Settings":
        project_root = (root or Path.cwd()).resolve()
        _load_dotenv(project_root)

        parent_tokens = _env_int("PONTOATIVO_PARENT_CHUNK_TOKENS", 450)
        overlap_tokens = _env_int(
            "PONTOATIVO_CHUNK_OVERLAP_TOKENS", 50, minimum=0
        )
        if overlap_tokens >= parent_tokens:
            raise ValueError(
                "PONTOATIVO_CHUNK_OVERLAP_TOKENS deve ser menor que o chunk-pai."
            )

        return cls(
            root=project_root,
            sources_dir=project_root / "fontes_originais",
            data_dir=project_root / "dados",
            vector_db_dir=project_root / "banco_vetorial",
            documentation_dir=project_root / "documentacao",
            evidence_dir=project_root / "evidencias",
            embedding_model=os.getenv(
                "PONTOATIVO_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL
            ),
            collection_name=os.getenv(
                "PONTOATIVO_CHROMA_COLLECTION", "pontoativo_documentos"
            ),
            parent_chunk_tokens=parent_tokens,
            chunk_overlap_tokens=overlap_tokens,
            embedding_segment_tokens=_env_int(
                "PONTOATIVO_EMBEDDING_SEGMENT_TOKENS", 120
            ),
            # 4 trechos mantêm recall 1,00 nas 18 perguntas e leem ~900 tokens a menos que 5.
            top_k=_env_int("PONTOATIVO_TOP_K", 4),
            ollama_base_url=os.getenv(
                "PONTOATIVO_OLLAMA_BASE_URL", "http://127.0.0.1:11434"
            ).rstrip("/"),
            ollama_model=os.getenv("PONTOATIVO_OLLAMA_MODEL", "gemma4:26b"),
            ollama_map_model=os.getenv("PONTOATIVO_OLLAMA_MODEL_MAPA", "").strip(),
            ollama_timeout_seconds=_env_float("PONTOATIVO_OLLAMA_TIMEOUT", 180.0),
            ollama_num_ctx=_env_int("PONTOATIVO_OLLAMA_NUM_CTX", 8192, minimum=1024),
            ollama_num_predict=_env_int("PONTOATIVO_OLLAMA_NUM_PREDICT", 400, minimum=64),
            ollama_keep_alive=os.getenv("PONTOATIVO_OLLAMA_KEEP_ALIVE", "10m"),
            structured_answers=_env_bool("PONTOATIVO_RESPOSTA_ESTRUTURADA", True),
            max_generation_attempts=_env_int("PONTOATIVO_TENTATIVAS_GERACAO", 3),
            # Distância cosseno máxima para considerar um trecho evidência útil.
            # Não é probabilidade de acerto; é um limiar calibrado na avaliação.
            max_distance=_env_float("PONTOATIVO_MAX_DISTANCE", 0.45),
        )

    @property
    def map_model(self) -> str:
        """Modelo que classifica as perguntas da barra do mapa."""
        return self.ollama_map_model or self.ollama_model

    def ensure_directories(self) -> None:
        """Cria apenas os diretórios de dados utilizados em execução."""
        for directory in (
            self.sources_dir,
            self.data_dir,
            self.vector_db_dir,
            self.documentation_dir,
            self.evidence_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
