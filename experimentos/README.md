# Experimentos do PontoAtivo

Os experimentos com e sem RAG e o piloto usaram o [protótipo das semanas 1 e 2](../prototipo/); a avaliação do assistente usa o sistema principal ([`src/pontoativo_rag/`](../src/pontoativo_rag/)). Os materiais avulsos (PDF, relatório e planilha) ficam em [`materiais/`](materiais/).

| Experimento | Pergunta avaliada | Resultados |
|---|---|---|
| [Com RAG](experimento-rag/README.md) | Como os modelos respondem quando recebem evidências das fontes do projeto? | [Análise das respostas](experimento-rag/analise-respostas.md) |
| [Sem RAG](experimento-sem-rag/README.md) | Como os modelos respondem às mesmas perguntas sem os trechos recuperados? | [Análise das respostas](experimento-sem-rag/analise-respostas.md) |
| [Piloto](novos-testes/README.md) | Como as respostas variam com a entidade consultada, os limites da evidência e a posição do trecho relevante? | [Análise do piloto](novos-testes/analise-piloto.md) e [rodadas](novos-testes/rodadas/) |
| [Avaliação do assistente](avaliacao-rag/README.md) | O assistente do mapa acha a fonte certa, cita só o que recuperou e se abstém quando deve? | [Resultado oficial (E5)](avaliacao-rag/atual/referencia_gemma12b_e5.md) |

## Materiais complementares

- [Perguntas de avaliação](perguntas_avaliacao.jsonl)
- [Consultas de demonstração](materiais/consultas-demo.md)
- [Comparação de LLMs em PDF](materiais/Compara%C3%A7%C3%A3o%20de%20LLMs%20gemma412b%20%C3%97%20qwen314b.pdf)
- [Relatório do pacote RAG](materiais/relatorio-llm-rag.docx) e [avaliações do assistente](avaliacao-rag/)
- [Planilha de avaliação comparativa](materiais/avaliacao-comparativa.ods)
