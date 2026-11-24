# Execuções dos agentes

Registros de rodadas reais dos agentes, guardados para consulta e comparação.
Os exemplos preparados à mão, usados nos testes e nas demonstrações, ficam em
[docs/agentes/exemplos](../../docs/agentes/exemplos/).
As evidências oficiais da entrega ficam em
[docs/entregas/semana-04/evidencias](../../docs/entregas/semana-04/evidencias/).

| Arquivo | O que é |
|---|---|
| [pesquisa/](pesquisa/) | Agente de Pesquisa (17/11): duas ações de entrada e as saídas — uma com evidência (faltas graves nos COPs) e uma sem (previsão do tempo) |
| [analise-natacao.json](analise-natacao.json), [analise-quadribol.json](analise-quadribol.json) | Agente de Análise sobre resultados do protótipo: "natação gratuita" (fontes divergentes e uma lacuna) e "quadribol" (lacuna: as fontes não tratam do tema) |
| [rascunho.json](rascunho.json) | Rascunho em formato antigo (texto livre) de uma pergunta imprópria, gerado antes da moderação; hoje a verificação barra essa pergunta antes da Pesquisa |
| [consulta-integrada-20261119.txt](consulta-integrada-20261119.txt) | Fluxo completo (Interpretação → Pesquisa → Análise) com o índice real, em 19/11 |
| [validacao-parque-da-cidade-20261119](validacao-parque-da-cidade-20261119.txt) ([JSON](validacao-parque-da-cidade-20261119.json)) | Validação no Parque da Cidade (19/11): o primeiro rascunho, preparado à mão, inventa que o caminho até os banheiros é acessível; a Validação por regras reprova e a Análise (qwen3:8b) corrige |
| [validacao-parque-da-cidade-revisor-llama-20261119](validacao-parque-da-cidade-revisor-llama-20261119.txt) ([JSON](validacao-parque-da-cidade-revisor-llama-20261119.json)) | O mesmo cenário com a Validação revisando também pelo modelo llama3.1:8b: reprova nas três rodadas (a última por temporalidade da gratuidade), então a resposta mostra os trechos sem conclusão redigida |
