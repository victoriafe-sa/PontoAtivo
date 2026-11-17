# Relatório da Fase 3 — Recuperação

**Data de referência:** 2026-11-10

## Implementações

- Listas são preservadas e classificadas como `structure_kind=lista`.
- Estruturas tabulares simples são classificadas como `structure_kind=tabela`.
- Cada chunk recebe `entity_key`, derivada da seção mais específica, para
  manter o local ou entidade associado ao trecho.
- Segmentos persistem `source_type`, `source_id`, `administrative_region` e
  `freshness_status`.
- A consulta aceita filtros por região, tipo de documento, fonte e atualidade.
- O reranker possui dois modos comparáveis: `hibrido` e `vetorial`.

## Comparação de rerankers

| Métrica | Vetorial | Híbrido |
|---|---:|---:|
| Recall médio@5 | 0,87 | **0,97** |
| Acerto de pelo menos uma fonte | 0,92 | **1,00** |
| Falsas abstenções | 0 | 0 |

O reranking híbrido foi mantido como padrão porque recupera evidência lexical
em português que o modo vetorial puro perde, especialmente na Q11 e na Q12.

Avaliações completas:

- [`fase3_vetorial`](../historico/avaliacao_20261110_113500_fase3_vetorial.md)
- [`fase3_hibrido`](../historico/avaliacao_20261110_113501_fase3_hibrido.md)
- [`comparação entre modos`](../historico/comparacao_avaliacao_20261110_113500_fase3_vetorial_vs_avaliacao_20261110_113501_fase3_hibrido.md)

## Validação contra a Fase 1

O modo híbrido não introduziu novas fontes irrelevantes nas três primeiras
posições quando comparado à avaliação final da Fase 1. O Recall médio@5 e o
acerto de fonte permaneceram em 0,97 e 1,00.

## Uso dos filtros

Exemplo:

```bash
python -m pontoativo_rag.consulta \
  --pergunta "Quais modalidades existem?" \
  --tipo pdf \
  --atualidade em_revisao \
  --reranker hibrido
```

Filtros são restritivos quando o metadado existe; trechos sem o metadado
solicitado continuam marcados e não são descartados silenciosamente.
