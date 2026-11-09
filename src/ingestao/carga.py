"""Ingestão: fontes -> chunks -> embeddings -> banco vetorial.

Rodar a partir da raiz do projeto:
    python src/ingestao/carga.py

Cria (ou recria) a coleção em dados/vetorial/. Na primeira execução o modelo
de embeddings (~1 GB) é baixado.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestao.banco import CAMINHO_BANCO, obter_cliente, recriar_colecao  # noqa: E402
from ingestao.chunking import chunkar_pasta  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
PASTA_FONTES = RAIZ / "dados" / "fontes" / "texto"
LOTE_CHROMA = 256


def carregar(pasta=PASTA_FONTES, caminho_banco=None, gerar=None):
    """Executa a ingestão completa e devolve um resumo.

    `gerar` é a função que transforma uma lista de textos em vetores. Por
    padrão usa o modelo real (ingestao.embeddings.gerar_embeddings); os testes
    passam uma função mais leve.
    """
    if gerar is None:
        from ingestao.embeddings import gerar_embeddings as gerar

    t0 = time.time()
    chunks, descartados = chunkar_pasta(pasta)
    t_chunking = time.time() - t0

    # O embedding é gerado a partir de texto_indexado (título + trecho);
    # o banco guarda o texto original para citar.
    t0 = time.time()
    vetores = gerar([c["texto_indexado"] for c in chunks])
    t_embeddings = time.time() - t0
    assert len(vetores) == len(chunks)

    colecao = recriar_colecao(obter_cliente(caminho_banco))
    for i in range(0, len(chunks), LOTE_CHROMA):
        lote = chunks[i:i + LOTE_CHROMA]
        colecao.add(
            ids=[c["id"] for c in lote],
            embeddings=vetores[i:i + LOTE_CHROMA],
            documents=[c["texto"] for c in lote],
            metadatas=[c["metadados"] for c in lote],
        )

    total = colecao.count()
    assert total == len(chunks), f"banco tem {total} chunks, esperava {len(chunks)}"
    return {
        "fontes": len({c["metadados"]["id_fonte"] for c in chunks}),
        "chunks": total,
        "dimensao": len(vetores[0]),
        "registros_descartados": descartados,
        "segundos_chunking": round(t_chunking, 1),
        "segundos_embeddings": round(t_embeddings, 1),
    }


def main():
    resumo = carregar(caminho_banco=CAMINHO_BANCO)
    print("Ingestão concluída")
    for chave, valor in resumo.items():
        print(f"  {chave}: {valor}")
    print(f"  banco: {CAMINHO_BANCO}")


if __name__ == "__main__":
    main()
