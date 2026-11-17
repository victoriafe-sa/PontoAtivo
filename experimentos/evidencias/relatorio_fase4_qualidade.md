# Relatório da Fase 4 — Qualidade da resposta

## Controles implementados

- avaliação factual baseada no suporte textual dos trechos citados;
- cobertura de citações por afirmação da resposta;
- detecção de afirmações sem suporte;
- contagem de citações inválidas;
- identificação de falsas abstenções;
- perguntas negativas e adversariais no conjunto de avaliação;
- gate automático com limiares mínimos.

## Limiares

- Recall médio@5: `>= 0,90`;
- acerto de pelo menos uma fonte: `>= 0,95`;
- falsas abstenções: `0`;
- citações inválidas: `0`;
- cobertura de citações: `>= 0,80` quando há respostas geradas;
- suporte factual médio: `>= 0,80` quando há respostas geradas;
- afirmações sem suporte: `0`.

As métricas de geração ficam como `—` no modo `--sem-geracao`; nesse modo o
gate avalia somente recuperação, abstenção e citações produzidas pelo sistema.

## Casos negativos e adversariais

As perguntas Q14–Q18 cobrem:

- preço ausente;
- disponibilidade em tempo real ausente;
- acessibilidade não confirmada;
- injeção de instruções na pergunta;
- tentativa de generalizar acessibilidade para todos os locais.

Na execução sem geração, as cinco perguntas negativas/adversariais produziram
abstenções corretas.

## Execução com LLM

A avaliação completa em [`avaliacao_20261110_114544_fase4_completa.md`](historico/avaliacao_20261110_114544_fase4_completa.md) encontrou
falhas reais de qualidade do modelo:

- 1 falsa abstenção;
- cobertura de citações abaixo do limite;
- afirmações sem suporte.

O gate falhou deliberadamente. Isso é importante: a automação agora impede que
uma resposta gerada seja considerada aprovada apenas porque a recuperação foi
boa. A falha deve ser tratada com ajuste de prompt/modelo e revisão das
respostas antes de liberar o modo RAG como aprovado.

## Iterações e estado atual

Foram adicionados controles para:

- remover uma abstenção contraditória quando a própria resposta contém
  citações válidas;
- repetir uma chamada ao modelo quando a resposta está vazia, começa com
  abstenção apesar de haver evidência ou não contém citação válida;
- rejeitar respostas que continuam com afirmações sem citação depois das
  tentativas de regeneração; nenhuma citação é anexada automaticamente;
- exigir pelo menos dois termos substantivos coincidentes para considerar uma
  afirmação apoiada pelo texto citado; uma palavra genérica não é suficiente;
- excluir do cálculo factual apenas cabeçalhos de listas e metadados como
  “Citei os documentos”, que não são afirmações sobre o domínio.

A última execução completa com `llama3.2:3b` foi
[`avaliacao_20261110_145018_fase4_final_llm_gate.md`](historico/avaliacao_20261110_145018_fase4_final_llm_gate.md). Seus resultados foram:

- recall médio@5: `0,97`;
- acerto de fonte: `1,00`;
- falsas abstenções: `0`;
- abstenções corretas: `5`;
- citações inválidas: `0`;
- cobertura média de citações: `0,50` (limite: `0,80`);
- suporte factual médio: `0,91`;
- afirmações sem suporte: `5` (limite: `0`).

Uma reprodução isolada de Q05 com `gemma4:26b` produziu duas frases,
ambas citadas com `[F1]`, em 91,9 segundos. Entretanto, a validação em lote
com esse modelo ultrapassou 35 minutos por causa do custo das tentativas de
regeneração e foi interrompida sem certificação do conjunto completo.

A avaliação somente de recuperação, após as correções, está registrada em
[`avaliacao_20261110_161823_correcao_achados_recuperacao_final_v2.md`](historico/avaliacao_20261110_161823_correcao_achados_recuperacao_final_v2.md) e passou:

- recall médio@5: `0,97`;
- acerto de fonte: `1,00`;
- falsas abstenções: `0`;
- abstenções corretas: `5`;
- gerações incompletas: `0` (não houve tentativa de geração).

Conclusão: a recuperação, a proveniência e o fail-closed estão aprovados.
A geração completa ainda não está certificada: o modelo pequeno falha no
contrato de citações e o modelo maior é lento demais para a validação em lote
atual. A Fase 4 permanece aberta até uma execução integral concluída com um
modelo que produza respostas citadas dentro do tempo operacional definido.

## Execução de 12/11/2026 com `gemma4:12b`

O `gemma4:26b` não cabe na memória de GPU do computador de teste (Mac M4, 24 GB) e
roda em grande parte na CPU. O `gemma4:12b` (8 GB) roda inteiro na GPU. Os modelos
gemma4 têm modo de raciocínio. Com ele ligado, o raciocínio consumia todo o
`num_predict` e a resposta voltava vazia. O cliente do Ollama agora envia
`"think": false` (`geracao.py`).

A avaliação completa, sem interrupção, está em
[`avaliacao_20261112_100019_gemma4_12b_completa.md`](historico/avaliacao_20261112_100019_gemma4_12b_completa.md):

| Métrica | `llama3.2:3b` (10/11) | `gemma4:12b` (12/11) | Limite |
|---|---:|---:|---:|
| Recall médio@5 | 0,97 | 0,97 | ≥ 0,90 |
| Acerto de fonte | 1,00 | 1,00 | ≥ 0,95 |
| Falsas abstenções | 0 | 0 | 0 |
| Abstenções corretas | 5 | 5 | — |
| Citações inválidas | 0 | 0 | 0 |
| Cobertura média de citações | 0,50 | **1,00** | ≥ 0,80 |
| Suporte factual médio | 0,91 | **1,00** | ≥ 0,80 |
| Afirmações sem suporte | 5 | **0** | 0 |
| Tempo médio de geração | — | 71 s | — |
| Tentativas médias | — | 1,15 | — |

**Verificação automática: OK.** É a primeira execução integral aprovada no portão.

O portão confere a forma das citações e a sobreposição de termos, não a correção
das respostas. A Fase 4 só fica concluída depois da revisão humana em
[`revisao_humana_rag_20261112_100019.md`](historico/revisao_humana_rag_20261112_100019.md). Se a revisão aceitar o resultado,
copie o relatório para `evidencias/avaliacao_atual.md`.

O tempo de 71 s por resposta é o limite deste hardware (cerca de 6 tokens/s) e
precisa ser mencionado na demonstração.

### Revisão humana (12/11/2026)

Revisor: Pedro Augusto Reis Alvim. Detalhes em
[`revisao_humana_rag_20261112_100019.md`](historico/revisao_humana_rag_20261112_100019.md).

| Resultado | Quantidade |
|---|---:|
| Correta | 10/13 |
| Parcial | 2/13 (Q04, Q05) |
| Incorreta | 1/13 (Q12) |
| Abstenção adequada | 4/5 |
| Abstenção inadequada | 1/5 (Q16) |
| Frases sem apoio | nenhuma registrada |

**Avaliação não aceita para a entrega.** Por isso,
`evidencias/avaliacao_atual.md` não foi criado. A Fase 4 continua aberta.

## Correção da Q12 e nova execução (12/11/2026, 10h50)

Na revisão humana, a Q12 foi a única resposta incorreta. O sistema disse que o
DOC-008 só tinha parques infantis. A causa estava na recuperação: o DOC-008 é uma
tabela sem subtítulos ("número, equipamento, endereço, coordenadas"). Todos os
trechos ficavam sem seção e quase idênticos para o modelo de embeddings, então o
trecho de cabeçalho vencia e os trechos com os PECs ficavam fora do top 5.

Correções:

- `processamento.py`: em tabelas georreferenciadas, cada tipo de equipamento vira
  uma seção ("PARQUE INFANTIL", "QUADRA DE ESPORTE", "PONTO DE ENCONTRO
  COMUNITÁRIO"). A seção entra no texto vetorizado e na comparação lexical. Só
  linhas que terminam em coordenadas ativam a regra, e só o DOC-008 tem esse formato.
- `recuperacao.py`: a comparação lexical ignora o plural regular ("pontos" casa
  com "ponto").
- `recuperacao.py`: a janela de busca é ampliada quando nenhum trecho tem 3/4 dos
  termos da pergunta. Antes, o limite era 1/2, e uma notícia que repetia metade dos
  termos impedia a ampliação.

Resultado em
[`avaliacao_20261112_105034_gemma4_12b_correcao_q12.md`](historico/avaliacao_20261112_105034_gemma4_12b_correcao_q12.md):

| Métrica | 10h00 | 10h50 |
|---|---:|---:|
| Recall médio@5 | 0,97 | **1,00** |
| Acerto de fonte | 1,00 | 1,00 |
| Cobertura de citações | 1,00 | 1,00 |
| Suporte factual | 1,00 | 1,00 |
| Afirmações sem suporte | 0 | 0 |
| Tentativas médias | 1,15 | **1,00** |
| Tempo médio de geração | 71 s | 68 s |

**Verificação automática: OK.** A Q12 agora responde com PECs do Plano Piloto
(SQS 415, SQS 416, EQS 102/103, EQS 104/105), citando a página 16 do DOC-008.
Ela lista 4 dos 63 PECs da tabela. A lista completa por região é função do mapa.

A mudança na ordem dos trechos alterou 10 das 13 respostas. A revisão humana das
10h00 vale só para aquela execução. Esta execução precisa de revisão própria em
[`revisao_humana_rag.md`](revisao_humana_rag.md).

## Qual computador estas evidências representam

As execuções de 12/11/2026 rodaram num Mac M4 de 24 GB com `gemma4:12b`. O padrão
do projeto continua sendo `gemma4:26b`, usado no computador pessoal do autor. Se a
demonstração usar o `gemma4:26b`, as respostas serão diferentes das revisadas aqui.
Nesse caso, rode `python -m pontoativo_rag.avaliacao --verificar-qualidade` nesse
computador e faça a revisão humana sobre essa execução. Seria a primeira execução
completa com o `gemma4:26b`: a de 10/11/2026 foi interrompida depois de 35 minutos.

## Correções da auditoria de extração (12/11/2026, 11h51)

Uma auditoria externa reproduziu a extração e apontou três problemas, confirmados
nos dados:

| Problema | Antes | Depois |
|---|---:|---:|
| Caracteres `�` nas leis (DOC-014 e DOC-015) | 12.695 | 0 |
| Trechos do edital (DOC-002) com atos de outros órgãos | presentes | 0 |
| Trechos do edital | 30 | 24 |
| Trechos com a região de outra RA | 3 | 0 |

Correções:

- `carregamento.py`: o HTML é decodificado pela codificação declarada; sem ela,
  por UTF-8 e, se falhar, por Windows-1252. As duas leis do Planalto vêm em
  Windows-1252 sem declarar o charset, e a leitura forçada em UTF-8 trocava os
  acentos por `�`.
- `carregamento.py`: o DOC-002 é um recorte do DODF. O texto agora começa em
  "EDITAL DE MATRÍCULA Nº 001/2025" e termina antes de "SECRETARIA DE ESTADO DO
  MEIO AMBIENTE". Ficam de fora atos da CODHAB, um extrato da SEL com a Terracap e
  o SEBRAE, e atos da ADASA e do Meio Ambiente. Se um marcador sumir, a ingestão
  falha em vez de indexar o recorte inteiro.
- `processamento.py`: em fontes de uma RA, uma seção que nomeia outra RA passa a
  região dela ao trecho. Corrigidos: COP Sobradinho (DOC-004, era Ceilândia),
  COP São Sebastião e COP Riacho Fundo I (DOC-005, eram Samambaia). Fontes
  nacionais não mudam: "Vasco da Gama" e "Santa Maria" não são RAs do DF.

Resultado em
[`avaliacao_20261112_115119_gemma4_12b_correcao_auditoria.md`](historico/avaliacao_20261112_115119_gemma4_12b_correcao_auditoria.md):
recall médio@5 de 1,00, acerto de fonte de 1,00, cobertura de citações de 1,00,
suporte factual de 1,00, nenhuma afirmação sem suporte, 5 abstenções corretas e
tempo médio de geração de 78 s. **Verificação automática: OK.**

7 das 13 respostas mudaram (Q01, Q02, Q03, Q05, Q08, Q10, Q13). A revisão humana
desta execução está pendente em [`revisao_humana_rag.md`](revisao_humana_rag.md).

Ficaram fora desta correção: a Carta de Serviços sem seções (60 trechos), as
palavras coladas do DOC-005 ("deentrada") e o cabeçalho repetido do DOC-006.

## Limpeza dos dados do RAG (12/11/2026, 17h18)

Depois da auditoria, uma medição da base apontou ruído restante. A limpeza
(`limpeza.py`, regras de título por fonte em `processamento.py`) mudou:

| Indicador | Antes | Depois |
|---|---:|---:|
| Trechos sem seção | 216 (39%) | 25 (5%) |
| Trechos da lista nacional de clubes (DOC-021) | 66 | 2 (só os 3 do DF) |
| Palavras coladas no DOC-005 | dezenas | 1 |
| Cabeçalho SEI repetido (DOC-006) | 13 | 0 |
| Linhas de sumário pontilhadas | várias | 0 |
| Trechos idênticos entre fontes | 2 | 0 |
| Fontes sem data de publicação | 5 | 1 (DOC-003) |

A base também ganhou o DOC-025 (Guia dos Espaços Públicos de Lazer do DF, UnB),
aprovado com ressalvas.

Resultado em
[`avaliacao_20261112_171807_gemma4_12b_limpeza.md`](historico/avaliacao_20261112_171807_gemma4_12b_limpeza.md):
recall médio@5 de 1,00, acerto de fonte de 1,00, cobertura de citações de 1,00,
suporte factual de 1,00, nenhuma afirmação sem suporte, 5 abstenções corretas e
76 s por resposta. **Verificação automática: OK.**

9 das 13 respostas mudaram em relação à execução das 11h51 (Q01, Q02, Q03, Q06,
Q07, Q08, Q10, Q11, Q13). A planilha [`revisao_humana_rag.md`](revisao_humana_rag.md)
passa a cobrir esta execução, que substitui as anteriores ainda não revisadas.

## Respostas mais rápidas e citações na tela (13/11/2026)

Medição de uma resposta da pesquisa de dúvidas no Mac M4: ler os 5 trechos
(~3.600 tokens) levava ~42 s e escrever a resposta, 26 a 73 s. As respostas
batiam no limite de 400 tokens e o JSON vinha cortado, o que forçava novas
tentativas: as instruções pediam frases sem citação e, ao mesmo tempo,
"cite os documentos como [F1]".

Mudanças:

- `geracao.py`: no modo estruturado, o pedido não manda mais citar no texto;
  cada frase tem até 25 palavras e no máximo 220 caracteres (no esquema JSON).
- `configuracao.py`: 4 trechos por pergunta em vez de 5 (~900 tokens a menos).
- `recuperacao.py`: bônus quando a pergunta cita o nome da seção do trecho
  ("faltas graves" e "7.3 Falta Grave"). Sem ele, perguntas reformuladas
  deixavam o trecho certo em 6º ou 10º lugar e o modelo tentava 3 vezes.
- `geracao.py` e `avaliacao.py`: uma letra sozinha com ponto ("V. Telebrasília")
  não encerra a frase; o avaliador usa a mesma regra do gerador.
- `avaliacao.py` (métrica): endereços do DF com número ("SQN 103", "EQN 112/113")
  contam como um termo. Antes eram descartados por terem partes curtas, e uma
  frase correta só com endereços era reprovada. A regra também torna a métrica
  mais rigorosa: um endereço citado na fonte errada não coincide.
- Site: as citações [F1]…[F5] aparecem como números sobrescritos (¹ ²) na ordem
  da lista "Fontes" abaixo da resposta.

Execuções:

| Execução | Portão | Afirmações sem suporte | Tempo médio |
|---|---|---:|---:|
| [`15h08`](historico/avaliacao_20261113_150836_gemma4_12b_respostas_rapidas.md) | falhou | 2 (Q12: frase partida em "V." e endereços não contados) | 56 s |
| 15h24 | falhou | 1 (Q12: o avaliador ainda partia a frase em "V.") | 63 s |
| [`15h43`](historico/avaliacao_20261113_154315_gemma4_12b_respostas_rapidas_v3.md) | **OK** | 0 | 63 s |

Na execução aprovada: recall médio@4 de 0,96 (a Q01 traz 1 das 2 fontes
esperadas; a resposta vem completa da Carta de Serviços), acerto de fonte de
1,00, cobertura de citações e suporte factual de 1,00, 5 abstenções corretas e
uma tentativa por resposta (antes, 76 s em média). A planilha
[`revisao_humana_rag.md`](revisao_humana_rag.md) passa a cobrir esta execução.
