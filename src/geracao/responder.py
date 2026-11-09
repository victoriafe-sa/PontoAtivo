"""Resposta extrativa: reproduz evidências, sem acrescentar fatos ou usar LLM."""


def responder(resultados, limite=3):
    if not resultados:
        return "Não há evidências recuperadas para responder."
    linhas = [
        "Resposta extrativa — os trechos abaixo são evidências candidatas à pergunta. "
        "A proximidade vetorial não garante que respondam a todos os seus pontos.",
    ]
    for r in resultados[:limite]:
        m = r["metadados"]
        linhas.extend([
            f"\n[{r['id']}] {m['titulo']}",
            r["texto"],
            f"Fonte: {m['link']}",
            f"Publicação: {m['data_publicacao']} | Coleta: {m['data_coleta']}",
            f"Validação: {m['validacao']} | Ressalvas: {m['ressalvas']}",
        ])
    linhas.append(
        "\nLimite: os trechos descrevem as fontes nas datas indicadas. "
        "Não confirmam funcionamento, vagas, horários ou acessibilidade atuais. "
        "Se o dado solicitado não aparece nos trechos, não é possível confirmá-lo."
    )
    return "\n".join(linhas)
