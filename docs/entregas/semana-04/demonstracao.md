# Demonstração da colaboração entre agentes

> Roteiro histórico da execução anterior à integração do agente de Validação. Os registros em `evidencias/` correspondem àquela versão. Para demonstrar o novo ciclo de revisão e correção, use o [roteiro da Validação](../../agentes/validacao.md). O script abaixo executa o código atual, mas seu registro legado não detalha todas as mensagens do novo agente.

## Preparação

Executar os comandos na raiz do repositório. São necessários o ambiente Python instalado, o índice vetorial preenchido, o embedding E5 em cache e o Ollama ativo com o modelo configurado (`gemma4:12b` na verificação). Sem o índice, executar a ingestão conforme o README do projeto.

```bash
.venv/bin/python -m pontoativo_rag.diagnostico
```

O diagnóstico verifica dependências e serviço, mas não comprova uma inferência completa nem a qualidade do índice. A execução seguinte é a evidência de ponta a ponta.

## Apresentação em aproximadamente cinco minutos

1. Abrir o diagrama no README desta entrega e apresentar os quatro papéis do fluxo atual, distinguindo-os dos três papéis do registro histórico.
2. Fazer a pergunta: **“Quais são as faltas graves nos Centros Olímpicos?”**
3. Executar o fluxo real:

```bash
.venv/bin/python scripts/demonstrar_multiagentes.py
```

4. Abrir `evidencias/demo.json` e mostrar, em ordem:
   - `interpretacao_para_pesquisa`: a pergunta original e a ação. Neste exemplo, a intenção pode ser `intencao_nao_identificada`; a busca documental continua normalmente.
   - `pesquisa_para_analise`: os trechos `T1…Tn`, textos, documentos, páginas e distâncias.
   - `analise`: a entrada efetivamente enviada ao modelo, sua saída bruta e a checagem de formato e passagens. Se houver repetição, aparecerá outro evento.
   - `resposta`: o resultado do coordenador, fontes citadas e número de tentativas.
5. Abrir `evidencias/demo.txt`, comparar a conclusão com a seção 7.3 do manual recuperado e explicar a conversão dos IDs `Tn` em referências `Fn`.
6. Explicar que a validação garante referências e passagens existentes, mas a adequação semântica também requer leitura da fonte.

O script envolve os recursos reais apenas para registrar suas chamadas. Executa `FluxoDocumental.responder`, a mesma coordenação usada no terminal e no caminho documental web. Não usa mocks ou respostas prontas. Retorna código 1 se terminar sem geração; assim, um fallback não é confundido com demonstração completa.

Os arquivos padrão são sobrescritos em novas execuções. Para preservar a execução anterior:

```bash
.venv/bin/python scripts/demonstrar_multiagentes.py --saida /tmp/pontoativo-demo-nova.json
```

Para mostrar uma intenção reconhecida e outra pergunta do projeto:

```bash
.venv/bin/python scripts/demonstrar_multiagentes.py \
  --pergunta "Como fazer a inscrição nos Centros Olímpicos?" \
  --saida /tmp/pontoativo-demo-inscricao.json
```

Esse segundo cenário é uma sugestão de apresentação, não uma garantia antecipada de resposta correta.

## Evidências automatizadas complementares

```bash
.venv/bin/python -m pytest -q tests/pontoativo_rag/agentes -m 'not integration'
.venv/bin/python -m pytest -q -m 'not integration'
```

Os testes mostram também situações difíceis sem depender da disponibilidade do LLM: referência inválida seguida de correção, ausência de evidência, indisponibilidade do modelo, preservação de condições e fontes. Identificar explicitamente esses casos como testes com componentes simulados.

## Critérios para considerar a demonstração concluída

- O registro declara `simulado: false`.
- Há ação da Interpretação, resultado da Pesquisa e chamada real da Análise.
- O modo final é `rag`, com itens aprovados pela validação.
- A equipe confere a correspondência entre a conclusão, as passagens e a fonte citada.
- A apresentação evidencia as trocas entre os agentes, além da resposta final.

O arquivo `verificacao.md` registra os resultados efetivamente observados nesta preparação.
