# Comparação da avaliação do PontoAtivo RAG

- **Avaliação anterior:** `avaliacao_20261110_113500_fase3_vetorial.jsonl`
- **Avaliação atual:** `avaliacao_20261110_113501_fase3_hibrido.jsonl`

## Resultado agregado

| Métrica | Anterior | Atual | Variação |
|---|---:|---:|---:|
| recall_medio_at_k | 0.87 | 0.97 | 0.10 |
| acerto_ao_menos_uma_fonte | 0.92 | 1.00 | 0.08 |

## Verificação de fontes irrelevantes no topo

⚠️ Foram encontradas novas fontes irrelevantes entre as três primeiras posições:
- **Q06:** DOC-002
- **Q08:** DOC-006
- **Q09:** DOC-004
- **Q15:** DOC-020
- **Q16:** DOC-006

## Mudanças por pergunta

| ID | Recall anterior | Recall atual | Irrelevantes no top 3 atual | Novas irrelevantes |
|---|---:|---:|---|---|
| Q01 | 1.00 | 1.00 | DOC-003 | nenhuma |
| Q02 | 1.00 | 1.00 | DOC-005 | nenhuma |
| Q03 | 1.00 | 1.00 | DOC-004, DOC-006 | nenhuma |
| Q04 | 1.00 | 1.00 | DOC-018 | nenhuma |
| Q05 | 1.00 | 1.00 | DOC-004, DOC-006 | nenhuma |
| Q06 | 1.00 | 1.00 | DOC-001, DOC-002 | DOC-002 |
| Q07 | 1.00 | 1.00 | DOC-001 | nenhuma |
| Q08 | 1.00 | 1.00 | DOC-006, DOC-015 | DOC-006 |
| Q09 | 1.00 | 1.00 | DOC-004, DOC-019 | DOC-004 |
| Q10 | 1.00 | 1.00 | DOC-005, DOC-019 | nenhuma |
| Q11 | 0.33 | 0.67 | DOC-004 | nenhuma |
| Q12 | 0.00 | 1.00 | nenhuma | nenhuma |
| Q13 | 1.00 | 1.00 | nenhuma | nenhuma |
| Q14 | — | — | DOC-005, DOC-006, DOC-018 | nenhuma |
| Q15 | — | — | DOC-019, DOC-020, DOC-021 | DOC-020 |
| Q16 | — | — | DOC-005, DOC-006, DOC-014 | DOC-006 |
