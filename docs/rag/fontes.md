# Revisão das fontes do RAG para a entrega

**Data:** 12/11/2026
**Base:** `dados/rag/catalogo.csv` (24 fontes, todas com `verification_status=aprovada`)
**Status:** triagem preparada para decisão da equipe. A coluna **Decisão** fica em
branco até a revisão humana.

## Critério

A entrega trata de atividade física e espaços esportivos **no Distrito Federal**.
Cada fonte foi classificada pelo que ela consegue sustentar numa resposta sobre o DF:

| Grupo | Significado |
|---|---|
| **A. Atende** | Fonte do DF, específica do tema e com data conhecida. Pode ser citada sem ressalva além do aviso padrão de atualidade. |
| **B. Atende com ressalva** | Fonte do DF útil, mas com informação volátil vencida ou data desconhecida. Pode ser usada, desde que a apresentação não a trate como vigente. |
| **C. Contexto nacional** | Lei, programa ou orientação nacional. Explica direitos e caminhos, mas não responde onde ou como algo funciona no DF. |
| **D. Baixo valor** | Pouco relacionada às perguntas da entrega. Candidata a sair do índice. |

A atualidade vem da regra do próprio sistema (`modelos.py`): informação volátil
(horários, vagas, inscrições) é revisada a cada 180 dias, normas a cada 730 e o
restante a cada 365. "Usada em" lista as perguntas de `dados/rag/perguntas/avaliacao.jsonl`
e `perguntas_comparacao_extras.jsonl` que dependem da fonte.

## Triagem

| Fonte | Título | Data | Atualidade | Trechos | Usada em | Grupo | Observação | Decisão |
|---|---|---|---|---:|---|---|---|---|
| DOC-001 | Carta de Serviços SEL-DF (2024) | 2024 | em revisão | 60 | Q01, Q13 | **A** | Principal fonte sobre os 12 COPs. | |
| DOC-002 | Edital de Matrícula dos COPs (2025) | 14/03/2025 | **antiga** | 24 | Q01, Q19, Q20 | **B** | O período de pré-inscrição (17/03 a 20/06/2025) já terminou. Apresentar como "edital de 2025", não como matrícula aberta. Verificar se há edital de 2026. Desde 12/11, só o edital é indexado; os atos de outros órgãos do mesmo recorte do DODF ficam de fora. | |
| DOC-003 | Manual de Uso dos COPs | não identificada | desconhecida | 5 | Q06, Q07 | **B** | Regras e horários sem data. Tentar identificar a data no site da SEL. | |
| DOC-004 | Diretrizes do COP Setor O | 2025 | em revisão | 38 | Q02 | **A** | Anexo do edital de 2025. | |
| DOC-005 | Diretrizes do COP Samambaia | 2025 | em revisão | 36 | Q03 | **A** | Anexo do edital de 2025. | |
| DOC-006 | Termo de Referência de equipamentos dos COPs | 18/08/2022 | antiga | 35 | — | **B** | Documento de compra. Não é usado na avaliação, mas ocupa 35 trechos. | |
| DOC-007 | Organograma da SEL-DF | 2025 | atual | 2 | — | **D** | Não responde a nenhuma pergunta da entrega. | |
| DOC-008 | Relação de Equipamentos Públicos do Plano Piloto | 2025 | atual | 11 | Q12 | **A** | Única lista oficial de PECs por RA. A Q12 errou na avaliação anterior porque a busca não trouxe esta fonte. | |
| DOC-009 | Novacap investe em PECs | 2026 | atual | 4 | Q04 | **A** | Fonte do número "mais de mil PECs" usado no site. | |
| DOC-010 | Novo PEC e acessibilidade em Ceilândia | 29/05/2025 | em revisão | 3 | Q05 | **A** | | |
| DOC-011 | Reforma de PEC na Fercal II | 07/04/2025 | em revisão | 2 | — | **A** | Não é usado na avaliação. | |
| DOC-012 | COPs de portas abertas à comunidade | 04/10/2022 | **antiga** | 3 | Q07 | **B** | Horários de 2022. Não apresentar como horário atual. | |
| DOC-013 | Decreto Distrital 28.494/2007 | 04/12/2007 | antiga* | 2 | Q08 | **A** | *Norma vigente. A data antiga não a invalida. | |
| DOC-014 | Lei Brasileira de Inclusão (13.146/2015) | 06/07/2015 | antiga* | 44 | — | **C** | *Norma vigente. Muito extensa para o que a entrega usa. | |
| DOC-015 | Lei Geral do Esporte (14.597/2023) | 14/06/2023 | em revisão | **67** | — | **C** | Maior fonte do índice e não é usada em nenhuma pergunta. | |
| DOC-016 | Programa SEMEAR | página vigente em 2026 | desconhecida | 5 | Q10 | **C** | | |
| DOC-017 | Manual Paradesporto Brasil em Rede | 22/06/2026 | atual | 19 | — | **C** | | |
| DOC-018 | Diretrizes TEAtivo 2023–2026 | 2023 | antiga | 37 | — | **C** | | |
| DOC-019 | Manual dos Centros de Referência Paralímpicos (CPB) | 2024 | atual | 43 | — | **C** | | |
| DOC-020 | FAQ do esporte paralímpico (CPB) | página vigente em 2026 | desconhecida | 13 | Q11 | **C** | | |
| DOC-021 | Quero ser um atleta paralímpico (CPB) | página vigente em 2026 | desconhecida | **65** | Q11 | **C** | | |
| DOC-022 | Escola Paralímpica de Esportes (CPB) | página vigente em 2026 | desconhecida | 2 | Q09, Q11 | **C** | | |
| DOC-023 | Aplicativo fitness para PcD (notícia) | 14/10/2025 | em revisão | 3 | — | **D** | Notícia de aplicativo, fora do tema de espaços no DF. | |
| DOC-024 | Novo Plano Viver sem Limite | 22/12/2021 | antiga | 10 | — | **D** | Plano de 2021 sem uso na avaliação. | |

## Resumo

| Grupo | Fontes | Trechos | Parcela do índice |
|---|---:|---:|---:|
| A. Atende | 8 | 156 | 29% |
| B. Atende com ressalva | 4 | 67 | 13% |
| C. Contexto nacional | 9 | 295 | 55% |
| D. Baixo valor | 3 | 15 | 3% |
| **Total** | **24** | **533** | |

Contagens atualizadas em 12/11/2026, depois da correção da Q12 (DOC-008 em
11 trechos) e do recorte do edital (DOC-002 em 24 trechos). As leis DOC-014 e
DOC-015 deixaram de ter caracteres corrompidos; o número de trechos delas não
mudou.

## Achados para a apresentação

1. **As fontes nacionais ocupam mais da metade do índice.** As 11 fontes nacionais
   (DOC-014 a DOC-024) somam 308 dos 533 trechos (58%). Elas competem na
   busca com as fontes do DF. As três maiores (DOC-015, DOC-021 e DOC-014) não
   respondem nenhuma pergunta específica do DF.
2. **"Todas aprovadas" não significa "todas vigentes".** As 24 fontes têm
   `verification_status=aprovada`, mas a aprovação atesta a procedência, não a
   atualidade. O edital de 2025 (DOC-002) e os horários de 2022 (DOC-012) estão
   vencidos pela regra do próprio sistema.
3. **Ressalva sobre a matrícula.** A apresentação não deve dizer que as inscrições
   estão abertas. O sistema responde com o período de 2025.

## Recomendação (a confirmar pela equipe)

- Manter os grupos A e B. No grupo B, preencher a data do DOC-003 e conferir se
  existe edital de 2026 para substituir o DOC-002.
- Manter no grupo C só o que a avaliação usa (DOC-016, DOC-020, DOC-021 e DOC-022)
  e decidir se as leis (DOC-014 e DOC-015) entram como contexto ou saem do índice.
- Retirar o grupo D (DOC-007, DOC-023 e DOC-024).
- Qualquer retirada muda o índice. Depois dela, rode de novo
  `python -m pontoativo_rag.ingestao` e a avaliação completa.

Nenhuma fonte foi retirada nesta revisão. A avaliação de 12/11/2026 usou as 24
fontes do catálogo.
