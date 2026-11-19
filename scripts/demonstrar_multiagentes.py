"""Executa o coordenador real e registra as mensagens da colaboração.

Uso na raiz: .venv/bin/python scripts/demonstrar_multiagentes.py
Não substitui a busca nem o LLM por respostas simuladas.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pontoativo_rag.agentes.analise import AnaliseInvalida, validar_analise
from pontoativo_rag.agentes.coordenador import criar_fluxo_documental
from pontoativo_rag.configuracao import Settings
from pontoativo_rag.consulta import format_answer


class PesquisaRegistrada:
    def __init__(self, pesquisa, eventos):
        self.pesquisa = pesquisa
        self.eventos = eventos

    def pesquisar(self, acao, **kwargs):
        self.eventos.append({"etapa": "interpretacao_para_pesquisa", "acao": acao})
        resultado, recuperados = self.pesquisa.pesquisar(acao, **kwargs)
        self.eventos.append({"etapa": "pesquisa_para_analise", "resultado": resultado})
        return resultado, recuperados


class ModeloRegistrado:
    def __init__(self, cliente, eventos):
        self.cliente = cliente
        self.model = cliente.model
        self.eventos = eventos

    def complete(self, system, user, **kwargs):
        evento = {"etapa": "analise", "instrucao": system, "entrada": json.loads(user)}
        self.eventos.append(evento)
        try:
            bruto = self.cliente.complete(system, user, **kwargs)
        except Exception as erro:
            evento["erro"] = type(erro).__name__
            raise
        evento["saida_bruta"] = bruto
        # Repete a mesma checagem somente para tornar o resultado visível no registro.
        # A validação e a decisão de repetir continuam no coordenador original.
        trechos = next(e["resultado"]["trechos"] for e in self.eventos
                       if e["etapa"] == "pesquisa_para_analise")
        try:
            evento["itens_validados"] = validar_analise(bruto, trechos)
            evento["validacao"] = "aprovada_formato_e_passagens"
        except AnaliseInvalida:
            evento["validacao"] = "reprovada_formato_ou_passagens"
        return bruto


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pergunta", default="Quais são as faltas graves nos Centros Olímpicos?")
    parser.add_argument("--saida", type=Path,
                        default=Path("docs/entregas/semana-04/evidencias/demo.json"))
    args = parser.parse_args()
    settings = Settings.from_env()
    fluxo = criar_fluxo_documental(settings)
    eventos = []
    fluxo.pesquisa = PesquisaRegistrada(fluxo.pesquisa, eventos)
    fluxo.cliente = ModeloRegistrado(fluxo.cliente, eventos)
    resposta, segundos = fluxo.responder(args.pergunta)
    registro = {
        "executado_em": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
        "simulado": False,
        "modelo": settings.ollama_model,
        "embedding": settings.embedding_model,
        "eventos": eventos,
        "resposta": resposta.to_dict(),
        "recuperacao_segundos": segundos,
    }
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(registro, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    texto = format_answer(resposta, segundos)
    args.saida.with_suffix(".txt").write_text(texto + "\n", encoding="utf-8")
    print(texto)
    print(f"\nMensagens entre agentes: {args.saida}")
    return 0 if resposta.mode == "rag" else 1


if __name__ == "__main__":
    raise SystemExit(main())
