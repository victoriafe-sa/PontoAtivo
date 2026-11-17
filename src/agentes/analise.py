from geracao.responder import sintetizar


def analisar(pergunta, resultados):
    
    if not resultados:
        return "A Pesquisa não encontrou evidências para analisar."

    instrucao = (
        "Você é o agente de Análise do PontoAtivo. "
        "Prepare um rascunho para o agente de Validação. "
        "Separe a pergunta do usuário em dúvidas individuais. "
        "Para cada dúvida, escreva a conclusão e cite o ID do trecho que a sustenta. "
        "Se os trechos forem insuficientes, diga qual informação está faltando. "
        "Preserve as datas e ressalvas relevantes das fontes.\n\n"
        f"Pergunta do usuário:\n{pergunta}"
    )
    return sintetizar(instrucao, resultados)