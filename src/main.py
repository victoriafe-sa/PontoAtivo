"""Consulta simples com recuperação semântica e resposta extrativa rastreável."""
import argparse
import json
from pathlib import Path

from geracao.responder import responder
from recuperacao.buscar import buscar, formatar_evidencia


def consultar(pergunta, k=5, caminho_banco=None):
    resultados = buscar(pergunta, k=k, caminho_banco=caminho_banco)
    return {"consulta": pergunta, "k": k, "resultados": resultados,
            "resposta": responder(resultados)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pergunta")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--json", dest="saida", help="salva consulta, chunks e resposta")
    args = ap.parse_args()
    if args.k < 1:
        ap.error("k deve ser positivo")
    try:
        registro = consultar(args.pergunta, args.k)
    except Exception as erro:
        ap.exit(1, f"Falha na consulta: {erro}\nConfira as dependências e execute python src/ingestao/carga.py se o banco não existir.\n")
    print(f"Consulta: {args.pergunta}\n\n{formatar_evidencia(registro['resultados'])}")
    print("\n" + registro["resposta"])
    if args.saida:
        Path(args.saida).write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
