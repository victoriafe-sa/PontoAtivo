"""Imagem -> evidência textual -> Análise -> Validação. Execução pelo terminal."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from ..configuracao import Settings
from ..geracao import LLMClient, LLMUnavailable, OllamaClient
from ..recursos import criar_cliente
from .analise import AnaliseInvalida, analisar_duvidas, formatar_rascunho, verificar_pergunta
from .imagem import AgenteImagem, ExtracaoInvalida, ImagemInvalida, MAX_BYTES
from .validacao import AgenteValidacao, ParecerInvalido, feedback_para_analise

AVISO = (
    "A fonte I1 é uma transcrição automática da imagem enviada, não uma fonte "
    "oficial verificada. Pode conter erros de leitura. Datas, horários e vagas "
    "não têm atualidade confirmada; confirme com a organização. A imagem não "
    "comprova condições de acessibilidade no local."
)


def responder_imagem(pergunta: str, conteudo: bytes, *,
                     agente: AgenteImagem, cliente_texto: LLMClient) -> dict:
    verificar_pergunta(pergunta)
    if len(pergunta) > 1000:
        raise ValueError("Use uma pergunta de até 1.000 caracteres.")
    extracao = agente.extrair(conteudo)
    resultado = {"modalidades": ["texto", "imagem"], "pergunta": pergunta,
                 "extracao": extracao, "avisos": [AVISO, *extracao["alertas"]]}
    if extracao["legibilidade"] == "ilegivel":
        return {**resultado, "modo": "abstencao", "itens": [],
                "resposta": "Não consegui ler o cartaz. Envie uma imagem mais nítida."}
    # O contrato legado já é aceito pela Análise e pela Validação.
    trechos = [{"id": "I1", "texto": extracao["texto"], "metadados": {
        "id": "I1", "titulo": "Cartaz enviado pelo usuário",
    }}]
    try:
        itens = analisar_duvidas(pergunta, trechos, cliente=cliente_texto)
        revisor = AgenteValidacao(cliente_texto)
        parecer = revisor.revisar(pergunta, itens, trechos)
        if not parecer["aprovado"]:
            itens = analisar_duvidas(
                pergunta, trechos, cliente=cliente_texto,
                feedback=feedback_para_analise(parecer, itens), rascunho_anterior=itens,
            )
            parecer = revisor.revisar(pergunta, itens, trechos)
    except (AnaliseInvalida, ParecerInvalido, LLMUnavailable) as erro:
        return {**resultado, "modo": "falha_validacao", "itens": [],
                "erro": type(erro).__name__,
                "resposta": "Não foi possível produzir uma resposta validada. Tente novamente."}
    if not parecer["aprovado"]:
        return {**resultado, "modo": "falha_validacao", "itens": [],
                "parecer": parecer,
                "resposta": "A resposta não passou na validação das evidências do cartaz."}
    return {**resultado, "modo": "multimodal", "itens": itens,
            "parecer": parecer, "resposta": formatar_rascunho(itens)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("imagem", type=Path)
    parser.add_argument("pergunta")
    parser.add_argument("--modelo-imagem", default=os.getenv("PONTOATIVO_OLLAMA_MODEL_IMAGEM"))
    args = parser.parse_args()
    config = Settings.from_env()
    modelo = args.modelo_imagem or os.getenv("PONTOATIVO_OLLAMA_MODEL_IMAGEM")
    if not modelo:
        parser.error("Defina --modelo-imagem com um modelo instalado que suporte visão.")
    visual = OllamaClient(config.ollama_base_url, modelo, config.ollama_timeout_seconds,
                          num_predict=4096, num_ctx=config.ollama_num_ctx)
    try:
        with args.imagem.open("rb") as arquivo:
            conteudo = arquivo.read(MAX_BYTES + 1)
        resultado = responder_imagem(args.pergunta, conteudo,
                                    agente=AgenteImagem(visual),
                                    cliente_texto=criar_cliente(config, num_predict=2400))
    except (OSError, ImagemInvalida, ExtracaoInvalida, LLMUnavailable, ValueError) as erro:
        parser.exit(1, f"Falha na consulta multimodal: {erro}\n")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if resultado["modo"] == "falha_validacao":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
