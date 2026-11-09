"""Recuperação: pergunta -> chunks mais relevantes, com fonte e score.

Rodar a partir da raiz do projeto (depois da ingestão):
    python src/recuperacao/buscar.py "onde fazer natação com acessibilidade?" -k 5

A busca devolve sempre os k chunks mais próximos (top-k), e não filtra por
limiar de similaridade, porque com o modelo E5 as notas ficam todas numa faixa
alta (cerca de 0,8 a 0,9). Decidir se os chunks bastam para responder é papel
da etapa de geração.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ingestao.banco import obter_cliente, obter_colecao  # noqa: E402


def buscar(pergunta, k=5, filtro=None, caminho_banco=None, embedding_consulta=None):
    """Devolve os k chunks mais próximos da pergunta.

    Cada resultado é um dict com: id, texto, metadados, distancia e
    similaridade (1 - distância de cosseno). `filtro` é um filtro de metadados
    do Chroma, por exemplo {"id_fonte": "N03"}.
    """
    if embedding_consulta is None:
        from ingestao.embeddings import embedding_da_consulta as embedding_consulta

    colecao = obter_colecao(obter_cliente(caminho_banco))
    resposta = colecao.query(
        query_embeddings=[embedding_consulta(pergunta)],
        n_results=k,
        where=filtro,
        include=["documents", "metadatas", "distances"],
    )
    resultados = []
    for id_, texto, meta, dist in zip(
        resposta["ids"][0], resposta["documents"][0],
        resposta["metadatas"][0], resposta["distances"][0],
    ):
        resultados.append({
            "id": id_,
            "texto": texto,
            "metadados": meta,
            "distancia": dist,
            "similaridade": 1 - dist,
        })
    return resultados


def formatar_evidencia(resultados, tamanho_trecho=300):
    """Texto legível com cada chunk recuperado e a sua fonte."""
    linhas = []
    for pos, r in enumerate(resultados, start=1):
        m = r["metadados"]
        trecho = " ".join(r["texto"].split())
        if len(trecho) > tamanho_trecho:
            trecho = trecho[:tamanho_trecho].rstrip() + "…"
        linhas.append(f"[{pos}] {r['id']}  similaridade {r['similaridade']:.3f}")
        linhas.append(f"    {m['titulo']} ({m['orgao']})")
        linhas.append(f"    link: {m['link']}")
        linhas.append(f"    coleta: {m['data_coleta']} | validação: {m['validacao']}")
        linhas.append(f"    trecho: {trecho}")
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser(description="Busca no banco vetorial do PontoAtivo")
    ap.add_argument("pergunta")
    ap.add_argument("-k", type=int, default=5, help="quantos chunks recuperar")
    args = ap.parse_args()
    print(formatar_evidencia(buscar(args.pergunta, k=args.k)))


if __name__ == "__main__":
    main()
