"""Formatos compartilhados pelos agentes de Pesquisa, Análise e Validação."""

from typing import Literal, NotRequired, TypedDict


class AcaoPesquisa(TypedDict):
    consulta: str
    pergunta_original: NotRequired[str | None]
    tipo: NotRequired[str | None]
    regiao: NotRequired[str | None]


class Fonte(TypedDict):
    id: str
    titulo: str
    instituicao: str
    url: str
    paginas: str
    secao: str
    regiao: str
    atualidade: str


class Trecho(TypedDict):
    id: str
    chunk_id: str
    texto: str
    distancia: float
    fonte: Fonte
    entidade: str
    metadado_filtro_ausente: bool


class ResultadoPesquisa(TypedDict):
    agente: str
    acao: AcaoPesquisa
    status: Literal["encontrado", "sem_evidencia"]
    trechos: list[Trecho]
    limiar: float
    descartados: int
    segundos: float
    motivo: NotRequired[str]


class PassagemCitada(TypedDict):
    id: str
    passagem: str


class ItemAnalise(TypedDict):
    duvida: str
    estado: Literal["sustentada", "lacuna", "divergencia", "precisa_esclarecimento"]
    conclusao: str
    trechos: list[str]
    evidencias: list[PassagemCitada]
