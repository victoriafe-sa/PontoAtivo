# Agente de Pesquisa

**Responsável:** Pedro · **Código:** [`src/pontoativo_rag/agentes/pesquisa.py`](../../src/pontoativo_rag/agentes/pesquisa.py)
· **Testes:** [`tests/pontoativo_rag/test_agente_pesquisa.py`](../../tests/pontoativo_rag/test_agente_pesquisa.py)

## Responsabilidade

Receber uma **ação** (o que o usuário quer saber, já identificado pelo agente de
Interpretação) e devolver os **trechos das fontes oficiais** que servem de
evidência, cada um com a sua origem. O agente não escreve resposta: só busca,
filtra e entrega o material para a Análise e a Validação.

```text
Interpretação ──ação──▶ Pesquisa ──trechos + fontes──▶ Análise ──rascunho──▶ Validação
                                   └───────────trechos + fontes─────────────▶ Validação
```

## Como decide o que entregar

1. Busca na base do assistente (25 fontes, embeddings multilingual-E5 no Chroma,
   busca híbrida com as palavras da consulta), pegando os 4 trechos mais próximos.
2. Mantém só os que passam na **mesma regra de evidência do gerador**
   (`geracao.trecho_relevante`): distância cosseno até 0,12 ou, perto disso,
   trechos com muitas palavras da consulta ou da mesma região.
3. Se nenhum passar, responde `sem_evidencia` e explica o motivo. Assim os outros
   agentes sabem que não devem afirmar nada, em vez de receber trechos fracos.

## Mensagens

**Entrada (ação):**

```json
{
  "pergunta_original": "O que pode fazer um aluno ser desligado do Centro Olímpico?",
  "tipo": "buscar_regra",
  "consulta": "faltas graves que levam ao desligamento do aluno nos Centros Olímpicos e Paralímpicos",
  "regiao": "Ceilândia"
}
```

Só `consulta` é obrigatória. `regiao` filtra pela região administrativa; os
outros campos são repassados sem mudança.

**Saída:**

```json
{
  "agente": "pesquisa",
  "acao": { "...": "a ação recebida" },
  "status": "encontrado",
  "trechos": [
    {
      "id": "T1",
      "texto": "7.3 Falta Grave ...",
      "distancia": 0.1235,
      "fonte": {
        "id": "DOC-003",
        "titulo": "Manual de Uso dos Centros Olimpicos e Paralimpicos",
        "instituicao": "Secretaria de Estado de Esporte e Lazer do Distrito Federal",
        "url": "https://www.esporte.df.gov.br/documents/d/esporte/manual-de-uso-do-cop",
        "paginas": "4",
        "secao": "7. Do descumprimento do Termo de Compromisso ...",
        "regiao": "",
        "atualidade": "..."
      }
    }
  ],
  "limiar": 0.12,
  "descartados": 3,
  "segundos": 8.2
}
```

Quando não há evidência: `"status": "sem_evidencia"`, `"trechos": []` e um
`"motivo"` com a melhor distância encontrada. Os IDs `T1`, `T2`… são os que a
Análise deve citar e a Validação deve conferir.

## Como rodar

Com o índice pronto (`python -m pontoativo_rag.ingestao`), na raiz do repositório:

```bash
.venv/bin/python -m pontoativo_rag.agentes.pesquisa "faltas graves nos Centros Olímpicos"
.venv/bin/python -m pontoativo_rag.agentes.pesquisa --acao docs/agentes/exemplos/acao_faltas_graves.json --saida resultado.json
```

Em Python, para conectar aos outros agentes:

```python
from pontoativo_rag.agentes.pesquisa import criar_agente

pesquisa = criar_agente()
resultado = pesquisa.executar({"consulta": "faltas graves nos Centros Olímpicos"})
```

## Exemplos com dados reais (17/11)

| Ação | Resultado |
|---|---|
| [Faltas graves nos COPs](exemplos/acao_faltas_graves.json) | [encontrado](exemplos/pesquisa_faltas_graves.json): 1 trecho do Manual de Uso dos COPs (DOC-003, p. 4, item 7.3 Falta Grave); 3 trechos descartados |
| [Previsão do tempo](exemplos/acao_sem_resultado.json) | [sem evidência](exemplos/pesquisa_sem_resultado.json): melhor distância 0,172, acima do limiar 0,12 |

## Próximos passos (quarta, 18/11)

- Conectar a saída à **Análise** e à **Validação**. O agente de Análise da
  branch `agente-analise` usa os resultados do protótipo (`prototipo/src/`);
  para receber esta saída, ele precisa ler `trechos[].texto` e `trechos[].fonte`,
  ou usar um pequeno adaptador.
- Testar a busca sem resultado no fluxo completo: com `sem_evidencia`, a Análise
  não deve montar rascunho, e a Comunicação deve dizer que as fontes não cobrem a pergunta.
