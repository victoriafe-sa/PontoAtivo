# Avaliação do PontoAtivo RAG — 2026-11-10T11:35:00

Arquivo gerado automaticamente por `python -m pontoativo_rag.avaliacao`.
Os valores abaixo vêm de uma execução real; nada foi editado à mão.

## Configuração

- **executado_em:** `2026-11-10T11:35:00`
- **perguntas:** `perguntas_avaliacao.jsonl`
- **modelo_embeddings:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **modelo_llm:** `None`
- **reranker:** `vetorial`
- **top_k:** `5`
- **limiar_distancia:** `0.45`
- **chunk_pai_palavras:** `450`
- **sobreposicao_palavras:** `50`
- **segmento_embedding_palavras:** `120`
- **vetores_no_banco:** `1487`
- **duracao_total_s:** `7.8`

## Resumo

| Métrica | Valor |
|---|---|
| perguntas | 16 |
| respondiveis | 13 |
| sem_resposta_na_base | 3 |
| recall_medio_at_k | 0.87 |
| acerto_ao_menos_uma_fonte | 0.92 |
| abstencoes_corretas | 3 |
| falsas_abstencoes | 0 |
| respostas_citando_fonte_relevante | 0 |
| respostas_geradas_respondiveis | 0 |
| citacoes_invalidas | 0 |
| distancia_melhor_respondiveis | 0.25 |
| distancia_melhor_sem_resposta | 0.49 |
| tempo_medio_recuperacao_s | 0.49 |
| tempo_medio_geracao_s | — |

## Verificação de qualidade

❌ Limites não atendidos:
- Recall@k 0.8717948717948718 abaixo do mínimo 0.90
- acerto de fonte 0.9230769230769231 abaixo do mínimo 0.95

Recall@k é calculado por fonte: fração das fontes do gabarito presentes entre os
trechos recuperados. Distância é a distância cosseno (menor = mais próximo) e
não representa probabilidade de a resposta estar correta.

## Resultados por pergunta

| ID | Categoria | Recall@k | Melhor dist. | Modo | Absteve | Citou relevante | Recup. (s) | Geração (s) |
|---|---|---|---|---|---|---|---|---|
| Q01 | localizacao | 1.00 | 0.250 | recuperacao_sem_geracao | False | — | 6.63 | 0.0 |
| Q02 | modalidades | 1.00 | 0.315 | recuperacao_sem_geracao | False | — | 0.07 | 0.0 |
| Q03 | localizacao | 1.00 | 0.229 | recuperacao_sem_geracao | False | — | 0.06 | 0.0 |
| Q04 | pecs | 1.00 | 0.257 | recuperacao_sem_geracao | False | — | 0.09 | 0.0 |
| Q05 | acessibilidade | 1.00 | 0.313 | recuperacao_sem_geracao | False | — | 0.06 | 0.0 |
| Q06 | regras | 1.00 | 0.259 | recuperacao_sem_geracao | False | — | 0.06 | 0.0 |
| Q07 | regras | 1.00 | 0.197 | recuperacao_sem_geracao | False | — | 0.06 | 0.0 |
| Q08 | acessibilidade | 1.00 | 0.070 | recuperacao_sem_geracao | False | — | 0.06 | 0.0 |
| Q09 | esporte_adaptado | 1.00 | 0.203 | recuperacao_sem_geracao | False | — | 0.06 | 0.0 |
| Q10 | esporte_adaptado | 1.00 | 0.283 | recuperacao_sem_geracao | False | — | 0.18 | 0.0 |
| Q11 | esporte_adaptado | 0.33 | 0.240 | recuperacao_sem_geracao | False | — | 0.06 | 0.0 |
| Q12 | pecs | 0.00 | 0.309 | recuperacao_sem_geracao | False | — | 0.06 | 0.0 |
| Q13 | regras | 1.00 | 0.266 | recuperacao_sem_geracao | False | — | 0.06 | 0.0 |
| Q14 | sem_resposta | — | 0.478 | abstencao | True | — | 0.06 | 0.0 |
| Q15 | sem_resposta | — | 0.518 | abstencao | True | — | 0.06 | 0.0 |
| Q16 | sem_resposta | — | 0.462 | abstencao | True | — | 0.18 | 0.0 |

## Respostas registradas (para revisão de fidelidade)

### Q01 — Em quais regiões administrativas do DF existem Centros Olímpicos e Paralímpicos?

- **Gabarito:** DOC-001, DOC-002
- **Referência esperada:** DOC-001 p. 57: 12 COPs em Brazlândia, Ceilândia (Parque da Vaquejada e Setor O), Estrutural, Gama, Recanto das Emas, Riacho Fundo I, Samambaia, Santa Maria, São Sebastião, Sobradinho e Planaltina.
- **Fontes recuperadas:** DOC-003, DOC-001, DOC-002
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-003, p. 4 — distância 0.250
- `F2` DOC-001, p. 57 — distância 0.265
- `F3` DOC-002, p. 1 — distância 0.275
- `F4` DOC-002, p. 2–3, seção 10. DOS CRITÉRIOS DE SELEÇÃO — distância 0.284
- `F5` DOC-001, p. 61–62 — distância 0.292

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q02 — Quais modalidades são oferecidas no COP do Setor O, em Ceilândia?

- **Gabarito:** DOC-004
- **Referência esperada:** DOC-004 p. 22, seção 1.2.2: lista de modalidades do COP do Setor O (não confundir com a lista do COP Parque da Vaquejada, p. 20-21).
- **Fontes recuperadas:** DOC-004, DOC-005
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-004, p. 25, seção 11. RECURSOS HUMANOS — distância 0.315
- `F2` DOC-004, p. 17, seção 8. EVENTOS E PARTICIPAÇÃO EM COMPETIÇÕES — distância 0.315
- `F3` DOC-005, p. 25, seção 11. RECURSOSHUMANOS — distância 0.326
- `F4` DOC-004, p. 21–22, seção 10. EQUIPAMENTOS ESPORTIVOS > 1.2 COP SETOR “O” (CEILÂNDIA) — distância 0.334
- `F5` DOC-004, p. 8, seção 6. PROPOSTA PEDAGÓGICA > 6.1 DESPORTO EDUCACIONAL PARA A COMUNIDADE DO COP — distância 0.346

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q03 — Quais equipamentos esportivos o Centro Olímpico de Samambaia possui?

- **Gabarito:** DOC-005
- **Referência esperada:** DOC-005, seção 1.2 COP SAMAMBAIA > equipamentos.
- **Fontes recuperadas:** DOC-005, DOC-004, DOC-006, DOC-003
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-005, p. 20–22, seção 10. EQUIPAMENTOSESPORTIVOS > 1.2 COP SAMAMBAIA — distância 0.229
- `F2` DOC-004, p. 22–24, seção 10. EQUIPAMENTOS ESPORTIVOS > 1.3 COP SOBRADINHO — distância 0.261
- `F3` DOC-006, p. 5, seção 8. DO LOCAL E DO PRAZO DA EXECUÇÃO DO SERVIÇO — distância 0.274
- `F4` DOC-005, p. 22–24, seção 10. EQUIPAMENTOSESPORTIVOS > 1.3 COP SÃO SEBASTIÃO — distância 0.275
- `F5` DOC-003, p. 4 — distância 0.306

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q04 — Quanto a Novacap está investindo em Pontos de Encontro Comunitário e quantos PECs pretende instalar ou revitalizar?

- **Gabarito:** DOC-009
- **Referência esperada:** DOC-009: mais de R$ 10 milhões; quase 200 PECs.
- **Fontes recuperadas:** DOC-009, DOC-018
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-009, seção GDF na Sua Porta investe mais de R$ 10 milhões em pontos de encontro comunitário no DF — distância 0.257
- `F2` DOC-009, seção GDF na Sua Porta investe mais de R$ 10 milhões em pontos de encontro comunitário no DF — distância 0.273
- `F3` DOC-009, seção GDF na Sua Porta investe mais de R$ 10 milhões em pontos de encontro comunitário no DF — distância 0.294
- `F4` DOC-018, p. 16, seção 6.7 NÚMERO DE NÚCLEOS POR PARCERIA — distância 0.355
- `F5` DOC-009 — distância 0.360

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q05 — Que melhorias de acessibilidade foram entregues junto com o novo PEC de Ceilândia?

- **Gabarito:** DOC-010
- **Referência esperada:** DOC-010: 2 mil metros de calçadas na EQNO 11/13 e academia ao ar livre na EQNO 9/11.
- **Fontes recuperadas:** DOC-010, DOC-004, DOC-006, DOC-005
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-010, seção Governo do DF amplia acessibilidade e entrega novo PEC para os moradores de Ceilândia — distância 0.313
- `F2` DOC-010, seção Governo do DF amplia acessibilidade e entrega novo PEC para os moradores de Ceilândia — distância 0.359
- `F3` DOC-004, p. 14, seção 6. PROPOSTA PEDAGÓGICA > 6.3 ESPORTE DE RENDIMENTO > 6.3.1 PROJETO FUTURO CAMPEÃO - PFC — distância 0.382
- `F4` DOC-006, p. 9, seção 12. DAS OBRIGAÇÕES DA CONTRATADA — distância 0.396
- `F5` DOC-005, p. 29, seção 15. AÇÕES FINANCIÁVEIS — distância 0.404

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q06 — Quais condutas são consideradas falta grave nos Centros Olímpicos e Paralímpicos?

- **Gabarito:** DOC-003
- **Referência esperada:** DOC-003 p. 4, item 7.3: ex.: agredir fisicamente funcionários ou usuários, pichar.
- **Fontes recuperadas:** DOC-003, DOC-001, DOC-012, DOC-004
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-003, p. 4 — distância 0.258
- `F2` DOC-001, p. 57 — distância 0.278
- `F3` DOC-001, p. 58 — distância 0.282
- `F4` DOC-012, seção Centros olímpicos e paralímpicos de portas abertas à comunidade — distância 0.287
- `F5` DOC-004, p. 17, seção 8. EVENTOS E PARTICIPAÇÃO EM COMPETIÇÕES — distância 0.292

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q07 — Em que horários acontecem as aulas nos Centros Olímpicos e Paralímpicos?

- **Gabarito:** DOC-012, DOC-003
- **Referência esperada:** DOC-003 item 2.3 (horários por dia da semana) e DOC-012 (notícia de 2022): aulas a partir das 6h45 até 21h, de segunda a sexta; fins de semana como áreas de convivência. Informação datada.
- **Fontes recuperadas:** DOC-003, DOC-001, DOC-022, DOC-002, DOC-012
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-003, p. 2 — distância 0.197
- `F2` DOC-001, p. 57 — distância 0.240
- `F3` DOC-022, seção Escola Paralímpica de Esportes — distância 0.257
- `F4` DOC-002, p. 4, seção 17. DISPOSIÇÕES FINAIS — distância 0.261
- `F5` DOC-012, seção Centros olímpicos e paralímpicos de portas abertas à comunidade — distância 0.273

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q08 — O que o Decreto distrital nº 28.494/2007 determina sobre acessibilidade em instalações esportivas?

- **Gabarito:** DOC-013
- **Referência esperada:** DOC-013: construção, ampliação e recuperação de instalações esportivas devem atender à acessibilidade e ao desenho universal; percurso acessível entre áreas.
- **Fontes recuperadas:** DOC-013, DOC-015, DOC-001
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-013 — distância 0.070
- `F2` DOC-013, seção DECRETO Nº 28.494, DE 04 DE DEZEMBRO DE 2007. — distância 0.086
- `F3` DOC-015 — distância 0.225
- `F4` DOC-015 — distância 0.232
- `F5` DOC-001, p. 41 — distância 0.236

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q09 — Qual faixa etária e quais modalidades a Escola Paralímpica de Esportes atende?

- **Gabarito:** DOC-022
- **Referência esperada:** DOC-022: crianças com deficiência física, visual e intelectual de 7 a 17 anos, em 15 modalidades paralímpicas.
- **Fontes recuperadas:** DOC-022, DOC-003, DOC-019, DOC-004
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-022 — distância 0.203
- `F2` DOC-022, seção Escola Paralímpica de Esportes — distância 0.243
- `F3` DOC-003, p. 4 — distância 0.258
- `F4` DOC-019, p. 30–31, seção 6 – EVENTOS — distância 0.265
- `F5` DOC-004, p. 10, seção 6. PROPOSTA PEDAGÓGICA > 6.2 DESPORTO DE PARTICIPAÇÃO E LAZER — distância 0.281

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q10 — O que o programa Semear oferece para pessoas com deficiência?

- **Gabarito:** DOC-016
- **Referência esperada:** DOC-016: eixos formação esportiva (a partir de 6 anos) e paradesporto para toda a vida.
- **Fontes recuperadas:** DOC-016, DOC-019, DOC-005, DOC-023, DOC-002
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-016, seção Semear > apresentação — distância 0.283
- `F2` DOC-019, p. 25, seção 6 – EVENTOS — distância 0.294
- `F3` DOC-005, p. 7–8, seção 6. PROPOSTA PEDAGÓGICA — distância 0.333
- `F4` DOC-023, seção Governo do Brasil lança primeiro aplicativo fitness para pessoas com deficiência — distância 0.380
- `F5` DOC-002, p. 3, seção 13. DA DOCUMENTAÇÃO E ANÁLISE — distância 0.381

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q11 — Como uma pessoa com deficiência pode começar a praticar esporte paralímpico?

- **Gabarito:** DOC-021, DOC-020, DOC-022
- **Referência esperada:** DOC-021: orientações do CPB e lista de clubes; DOC-020 FAQ.
- **Fontes recuperadas:** DOC-021, DOC-004, DOC-019, DOC-017
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-021, seção Quero ser um ATLETa Paralímpico — distância 0.240
- `F2` DOC-004, p. 7–8, seção 6. PROPOSTA PEDAGÓGICA — distância 0.295
- `F3` DOC-021, seção Quero ser um ATLETa Paralímpico > Encontre um Clube > Secretaria Municipal dos Direitos da Pessoa Com Deficiência de Nova Iguaçu — distância 0.325
- `F4` DOC-019, p. 19, seção 5 - METODOLOGIA — distância 0.329
- `F5` DOC-017, p. 7 — distância 0.342

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q12 — Onde ficam os Pontos de Encontro Comunitário listados no Plano Piloto?

- **Gabarito:** DOC-008
- **Referência esperada:** DOC-008: relação de equipamentos públicos do Plano Piloto com 63 PECs, endereço e coordenadas.
- **Fontes recuperadas:** DOC-019, DOC-004, DOC-018, DOC-005
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-019, p. 6, seção 5 - METODOLOGIA — distância 0.309
- `F2` DOC-004, p. 11, seção 6. PROPOSTA PEDAGÓGICA > 6.2 DESPORTO DE PARTICIPAÇÃO E LAZER — distância 0.334
- `F3` DOC-018, p. 29–30, seção 13.3 INSTRUMENTO DE FORMALIZAÇÃO DAS PARCERIAS — distância 0.339
- `F4` DOC-005, p. 27, seção 13. INDICADORES — distância 0.342
- `F5` DOC-004, p. 27, seção 13. INDICADORES — distância 0.351

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q13 — Quem é isento do pagamento da taxa da Escola de Esportes da Secretaria de Esporte e Lazer?

- **Gabarito:** DOC-001
- **Referência esperada:** DOC-001 p. 56: estudantes da rede pública, alunos com deficiência, idosos acima de 60 anos, integrantes de equipes da SEL de 6 a 17 anos, hipossuficientes.
- **Fontes recuperadas:** DOC-001, DOC-015
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-001, p. 66 — distância 0.266
- `F2` DOC-001, p. 56 — distância 0.349
- `F3` DOC-001, p. 42 — distância 0.352
- `F4` DOC-015 — distância 0.383
- `F5` DOC-015 — distância 0.390

Resposta:

> MODO DE DIAGNÓSTICO — recuperação sem geração (geração desativada). Os trechos abaixo foram recuperados, mas nenhuma resposta foi redigida; isto não é uma demonstração completa de RAG.

- **Fidelidade:** _pendente de revisão humana_

### Q14 — Qual é o preço da mensalidade das academias particulares do Lago Sul?

- **Gabarito:** sem resposta na base
- **Referência esperada:** Nenhuma fonte da base trata de academias particulares ou preços no Lago Sul.
- **Fontes recuperadas:** DOC-018, DOC-006, DOC-005, DOC-017
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-018, p. 25–26, seção 12.5 MATRIZ DE CUSTOS EXEMPLIFICATIVA — distância 0.478
- `F2` DOC-006, p. 9–10, seção 14. DO CUSTO ESTIMADO PARA A CONTRATAÇÃO — distância 0.507
- `F3` DOC-018, p. 24–25, seção 12.1 PROFISSIONAIS E ACADÊMICOS PARA DESENVOLVIMENTO DO PROGRAMA — distância 0.512
- `F4` DOC-005, p. 28, seção 15. AÇÕES FINANCIÁVEIS — distância 0.512
- `F5` DOC-017, p. 24 — distância 0.517

Resposta:

> Não encontrei nos documentos evidências suficientes para responder. Nenhum trecho recuperado ficou dentro do limiar de proximidade configurado (distância cosseno ≤ 0.45).

- **Fidelidade:** _pendente de revisão humana_

### Q15 — Qual quadra de tênis do Gama está livre para reserva hoje à noite?

- **Gabarito:** sem resposta na base
- **Referência esperada:** A base não contém disponibilidade em tempo real nem reservas.
- **Fontes recuperadas:** DOC-019, DOC-021, DOC-006, DOC-015
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-019, p. 39, seção 9 – ITENS DE DESPESA — distância 0.518
- `F2` DOC-021, seção Quero ser um ATLETa Paralímpico > Encontre um Clube > Tênis para Todos — distância 0.579
- `F3` DOC-006, p. 13, seção 19. DISPOSIÇÕES GERAIS — distância 0.594
- `F4` DOC-015 — distância 0.598
- `F5` DOC-006, p. 11, seção 14. DO CUSTO ESTIMADO PARA A CONTRATAÇÃO — distância 0.608

Resposta:

> Não encontrei nos documentos evidências suficientes para responder. Nenhum trecho recuperado ficou dentro do limiar de proximidade configurado (distância cosseno ≤ 0.45).

- **Fidelidade:** _pendente de revisão humana_

### Q16 — O PEC da Fercal tem banheiro adaptado para cadeirantes?

- **Gabarito:** sem resposta na base
- **Referência esperada:** DOC-011 está disponível, mas a fonte sobre o PEC da Fercal II não confirma a existência de banheiro adaptado para cadeirantes.
- **Fontes recuperadas:** DOC-005, DOC-014
- **Fontes citadas:** nenhuma

Trechos recuperados:

- `F1` DOC-005, p. 20–22, seção 10. EQUIPAMENTOSESPORTIVOS > 1.2 COP SAMAMBAIA — distância 0.462
- `F2` DOC-014 — distância 0.557
- `F3` DOC-005, p. 14, seção 6. PROPOSTA PEDAGÓGICA > 6.3 ESPORTE DE RENDIMENTO > 6.3.1 PROJETO FUTURO CAMPEÃO -PFC — distância 0.561
- `F4` DOC-014 — distância 0.569
- `F5` DOC-005, p. 17, seção 8. EVENTOS E PARTICIPAÇÃO EMCOMPETIÇÕES — distância 0.584

Resposta:

> Não encontrei nos documentos evidências suficientes para responder. Nenhum trecho recuperado ficou dentro do limiar de proximidade configurado (distância cosseno ≤ 0.45).

- **Fidelidade:** _pendente de revisão humana_
