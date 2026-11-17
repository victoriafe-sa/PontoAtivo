"""Geração de embeddings do PontoAtivo.

Modelo: intfloat/multilingual-e5-base (768 dimensões, até 512 tokens, bom em PT-BR).

O modelo E5 exige prefixos: "passage: " nos chunks indexados e "query: " na
pergunta do usuário. As funções abaixo já aplicam os prefixos; quem chama passa
o texto puro.

Os vetores saem normalizados (norma 1), então a similaridade de cosseno é igual
ao produto escalar. No banco vetorial, use a métrica de cosseno.
"""

from sentence_transformers import SentenceTransformer

NOME_MODELO = "intfloat/multilingual-e5-base"
DIMENSAO = 768

_modelo = None


def _carregar_modelo():
    # Carrega uma vez só; na primeira execução o modelo (~1 GB) é baixado.
    global _modelo
    if _modelo is None:
        _modelo = SentenceTransformer(NOME_MODELO)
    return _modelo


def gerar_embeddings(textos, tamanho_lote=32):
    """Converte uma lista de chunks em uma lista de vetores (listas de float)."""
    modelo = _carregar_modelo()
    entradas = ["passage: " + texto for texto in textos]
    vetores = modelo.encode(
        entradas,
        batch_size=tamanho_lote,
        normalize_embeddings=True,
        show_progress_bar=len(entradas) > tamanho_lote,
    )
    return vetores.tolist()


def embedding_da_consulta(pergunta):
    """Converte a pergunta do usuário em um único vetor (lista de float)."""
    modelo = _carregar_modelo()
    vetor = modelo.encode("query: " + pergunta, normalize_embeddings=True)
    return vetor.tolist()
