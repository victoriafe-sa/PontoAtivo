"""Consulta simples com recuperação semântica e síntese local pelo Gemma 4."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from pontoativo_rag.agentes.analise import analisar_duvidas, formatar_rascunho, verificar_pergunta
from geracao.responder import sintetizar
from recuperacao.buscar import buscar, formatar_evidencia


def consultar(pergunta, k=5, caminho_banco=None, *, rascunho=False):
    if rascunho:
        verificar_pergunta(pergunta)
    resultados = buscar(pergunta, k=k, caminho_banco=caminho_banco)
    if rascunho:
        itens = analisar_duvidas(pergunta, resultados)
        return {"consulta": pergunta, "k": k, "resultados": resultados,
                "analise": itens, "rascunho": formatar_rascunho(itens)}
    return {"consulta": pergunta, "k": k, "resultados": resultados,
            "resposta": sintetizar(pergunta, resultados)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pergunta")
    ap.add_argument("-k", type=int, default=5)
    ap.add_argument("--json", dest="saida", help="salva consulta, chunks e resposta")
    ap.add_argument("--rascunho", action="store_true", help="gera um rascunho para Validação")
    args = ap.parse_args()
    if args.k < 1:
        ap.error("k deve ser positivo")
    try:
        registro = consultar(args.pergunta, args.k, rascunho=args.rascunho)
    except (RuntimeError, ValueError) as erro:
        ap.exit(1, f"Falha na consulta: {erro}\n")
    except Exception as erro:
        ap.exit(1, f"Falha na consulta: {erro}\nConfira as dependências e execute python src/ingestao/carga.py se o banco não existir.\n")
    print(f"Consulta: {args.pergunta}\n\n{formatar_evidencia(registro['resultados'])}")
    if args.rascunho:
        print("\nRascunho para Validação:\n" + registro["rascunho"])
    else:
        print("\n" + registro["resposta"])
    if args.saida:
        Path(args.saida).write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
