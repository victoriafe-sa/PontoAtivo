# Experimento de LLM com RAG — semana 3

Os quatro JSONs originais permanecem na pasta superior (`resultados/semana-03`).
Cada prompt contém a pergunta e os cinco resultados completos do respectivo JSON, incluindo texto, ID e metadados. A resposta extrativa original não foi incluída.

## Perguntas

| ID | Pergunta | Evidências originais |
|---|---|---|
| Q1 | A academia pública do Parque da Cidade é gratuita e como utilizar? | `../q1-evidencias.json` |
| Q2 | Quais modalidades esportivas são oferecidas pelos Centros Olímpicos e Paralímpicos do DF? | `../q2-evidencias.json` |
| Q3 | Qual é o endereço do Estádio Bezerrão no Gama? | `../q3-evidencias.json` |
| Q4 | Qual quadra tem vaga disponível amanhã às 19h e acessibilidade verificada para cadeirantes? | `../q4-evidencias.json` |

## Como usar

1. Envie `prompts/q1.txt` integralmente ao Gemini 3.5 Flash, Qwen3 8B e Llama 3.2 3B, em conversas novas e sem ferramentas externas de busca.
2. Salve a resposta integral de cada modelo como `q1.txt` na pasta correspondente.
3. Repita com os prompts Q2, Q3 e Q4, mantendo o conteúdo dos prompts igual nos três modelos.
4. Registre modelo/versão, configurações e data da execução junto da resposta. Na Q4, registre também a data correspondente a “amanhã”.

Pastas de saída:

- `respostas-gemini/`: respostas do Gemini 3.5 Flash.
- `respostas-qwen/`: respostas do Qwen3 8B.
- `respostas-llama/`: respostas do Llama 3.2 3B.

As pastas de respostas começam vazias: nenhum modelo gerador foi executado nesta organização. Resultado esperado: 12 respostas, quatro por modelo.
