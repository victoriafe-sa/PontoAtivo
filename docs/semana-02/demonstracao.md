# Demonstração e avaliação da recuperação

Execução real: **2026-11-08T19:54:53.461178-03:00** (São Paulo). Modelo: intfloat/multilingual-e5-base; 768 dimensões. Banco: 25 fontes e 599 chunks. Sem filtro por fonte e sem reranking; top-5 por cosseno.

## Como interpretar

O sistema retorna uma resposta extrativa com os três primeiros chunks e suas fontes. As sínteses abaixo são **redigidas e revisadas manualmente para a demonstração**, a partir dos trechos da execução; não são saída de um LLM nem de um gerador automático de sínteses. A saída automática completa está em evidencias/consultas.json. A seleção semântica é feita pelo modelo real E5, não pelo embedding sintético usado no teste de banco.

As fontes esperadas foram definidas nos casos do script antes da consulta. O caso Q4 foi incluído para avaliar insuficiência. O sistema ainda não se abstém automaticamente: ele devolve evidências candidatas com ressalvas; a conclusão de insuficiência é humana.

## Resultado dos casos

| Caso | Fonte esperada | Posição encontrada | Avaliação |
|---|---|---|---|
| Q1 | N03 | 1 | Fonte-alvo recuperada |
| Q2 | F059 | 1 | Fonte-alvo recuperada |
| Q3 | N04 | 1 | Fonte-alvo recuperada |
| Q4 | Sem fonte suficiente | Não se aplica | Insuficiência identificada em revisão humana |

**Hit@5: 3/3; MRR@5: 1.00.** São métricas de presença/posição da fonte-alvo em três casos selecionados, não precisão de todos os chunks nem avaliação ampla. Não há conjunto exaustivo de relevância para medir Recall@5. Q4 não entra no cálculo.

## Q1 — consulta submetida

Quais modalidades esportivas são oferecidas pelos Centros Olímpicos e Paralímpicos do DF?

### Ranking real dos chunks

| Posição | Chunk | Similaridade | Fonte |
|---|---|---|---|
| 1 | N03-003 | 0.9092 | [N03](https://www.esporte.df.gov.br/w/centros-olimpicos-e-paralimpicos-do-df-oferecem-mais-de-10-mil-vagas-remanescentes) |
| 2 | N02-002 | 0.8945 | [N02](https://www.agenciabrasilia.df.gov.br/w/centros-olimpicos-e-paralimpicos-abrem-mais-de-12-mil-vagas-no-df-com-estrutura-reforcada) |
| 3 | F028-001 | 0.8940 | [F028](https://www.esporte.df.gov.br/cops) |
| 4 | N02-003 | 0.8903 | [N02](https://www.agenciabrasilia.df.gov.br/w/centros-olimpicos-e-paralimpicos-abrem-mais-de-12-mil-vagas-no-df-com-estrutura-reforcada) |
| 5 | N03-004 | 0.8901 | [N03](https://www.esporte.df.gov.br/w/centros-olimpicos-e-paralimpicos-do-df-oferecem-mais-de-10-mil-vagas-remanescentes) |

### Resposta fundamentada — síntese humana

Segundo a notícia da SEL-DF de 07/09/2025, a oferta inclui atletismo, basquete, futsal, futebol society, ginástica localizada, pilates, vôlei, jiu-jitsu, judô, taekwondo, karatê e capoterapia, entre outras. Modalidades, faixas etárias e horários variam por unidade. A notícia não confirma vagas abertas hoje. [N03-003]

### Evidência textual recuperada

**N03-003 — Centros Olímpicos e Paralímpicos do DF oferecem mais de 10 mil vagas remanescentes**

```text
Modalidades esportivas
As vagas estão distribuídas em modalidades como:
* Atletismo
* Basquete
* Futsal
* Futebol Society
* Ginástica Localizada
* Pilates
* Vôlei
* Jiu-Jitsu
* Judô
* Taekwondo
* Karatê
* Capoterapia
* Entre outras
O quantitativo de vagas, modalidades, faixa etária e horários variam de acordo com cada unidade e podem ser consultados diretamente nas secretarias dos Centros Olímpicos e Paralímpicos ou no site da SEL-DF.
Esporte para todos
De acordo com o secretário de Esporte e Lazer do DF, Renato Junqueira, a abertura das vagas remanescentes reforça o papel dos COPs como espaços de inclusão e transformação social:
“Os Centros Olímpicos e Paralímpicos oferecem oportunidades para todas as idades e são ambientes de convivência, saúde e cidadania.
```

Fonte: [Secretaria de Esporte e Lazer do DF (SEL-DF)](https://www.esporte.df.gov.br/w/centros-olimpicos-e-paralimpicos-do-df-oferecem-mais-de-10-mil-vagas-remanescentes). Publicação: 07/09/2025. Coleta: 2026-11-07.

Validação: Pendente de validação humana. Ressalvas: Prazo de inscrição (até 30/11/2025) já encerrado. A lista de modalidades é exemplificativa ('entre outras'); quantitativo, modalidades e horários variam por unidade. AVISO: texto da fonte, com limpeza de ruído de interface descrita em AUDITORIA.md. Confira no link antes de usar como informação oficial..

## Q2 — consulta submetida

Qual é o endereço do Estádio Bezerrão no Gama?

### Ranking real dos chunks

| Posição | Chunk | Similaridade | Fonte |
|---|---|---|---|
| 1 | F059-001 | 0.9015 | [F059](https://www.esporte.df.gov.br/estadio-bezerrao) |
| 2 | F062-002 | 0.8212 | [F062](https://www.esporte.df.gov.br/espacos-esportivos/) |
| 3 | F062-001 | 0.8211 | [F062](https://www.esporte.df.gov.br/espacos-esportivos/) |
| 4 | F064-002 | 0.8192 | [F064](https://www.sinj.df.gov.br/sinj/Norma/1b5ab145e1984280b7142d0324f013aa/Decreto_45269_08_12_2023.html) |
| 5 | F060-001 | 0.8117 | [F060](https://www.esporte.df.gov.br/estadio-rorizao) |

### Resposta fundamentada — síntese humana

O endereço informado pela SEL-DF é St. Central – Gama, Brasília – DF, 72405-610. A informação de endereço não comprova que o estádio esteja aberto para uso agora. [F059-001]

### Evidência textual recuperada

**F059-001 — Estádio Bezerrão**

```text
### Estádio Popularmente Conhecido Como “bezerrão”
17/02/25 às 15h59 - Atualizado em 20/02/26 às 16h13
## Estádio popularmente conhecido como “Bezerrão”
Estádio Bezerrão:
REGÃO: GAMA
Inaugurado em 1977, o espaço passou por uma grande reforma há 15 anos para sediar partidas de futebol profissional. Foi palco do amistoso entre Brasil e Portugal na reinauguração em 2008, com a presença do jogador Cristiano Ronaldo, e da Copa do Mundo Fifa Sub-17, em 2019, capacidade atual estimada para 20.310 espectadores.
Endereço
St. Central – Gama, Brasília – DF, 72405-610
```

Fonte: [Secretaria de Esporte e Lazer do DF (SEL-DF)](https://www.esporte.df.gov.br/estadio-bezerrao). Publicação: 17/02/2025 (atualizada em outra data; ver texto). Coleta: 2026-11-05.

Validação: Pendente de validação humana. Ressalvas: Página curta (cerca de 500 caracteres); capacidade 'estimada' segundo a página. AVISO: texto da fonte, com limpeza de ruído de interface descrita em AUDITORIA.md. Confira no link antes de usar como informação oficial..

**Análise de relevância:** o primeiro chunk responde ao endereço. Os demais incluem outros espaços e normas; o top-5 não é integralmente pertinente. Não se deve misturar o endereço de outro estádio na resposta.

## Q3 — consulta submetida

A academia pública do Parque da Cidade é gratuita e como utilizar?

### Ranking real dos chunks

| Posição | Chunk | Similaridade | Fonte |
|---|---|---|---|
| 1 | N04-008 | 0.9090 | [N04](https://www.agenciabrasilia.df.gov.br/w/academia-publica-do-parque-da-cidade-vira-ponto-de-encontro-e-saude-para-brasilienses) |
| 2 | N04-002 | 0.9007 | [N04](https://www.agenciabrasilia.df.gov.br/w/academia-publica-do-parque-da-cidade-vira-ponto-de-encontro-e-saude-para-brasilienses) |
| 3 | N04-001 | 0.8935 | [N04](https://www.agenciabrasilia.df.gov.br/w/academia-publica-do-parque-da-cidade-vira-ponto-de-encontro-e-saude-para-brasilienses) |
| 4 | N04-007 | 0.8826 | [N04](https://www.agenciabrasilia.df.gov.br/w/academia-publica-do-parque-da-cidade-vira-ponto-de-encontro-e-saude-para-brasilienses) |
| 5 | N04-006 | 0.8796 | [N04](https://www.agenciabrasilia.df.gov.br/w/academia-publica-do-parque-da-cidade-vira-ponto-de-encontro-e-saude-para-brasilienses) |

### Resposta fundamentada — síntese humana

Segundo a reportagem de 11/01/2025, musculação e aulas coletivas são gratuitas. Para usar, é necessário baixar o aplicativo Mude – Yoga e Fitness, concluir o cadastro e agendar o horário. O funcionamento depende da presença de profissional de educação física. Essa fonte histórica não confirma a agenda atual. [N04-008]

### Evidência textual recuperada

**N04-008 — Academia pública do Parque da Cidade vira ponto de encontro e saúde para brasilienses**

```text
parcerias entre a iniciativa privada e a gestão pública podem criar soluções potentes e que beneficiam toda a população. Juntos, conseguimos oferecer um espaço que vai além da prática esportiva, promovendo qualidade de vida e reforçando nosso propósito de transformar cidades em ecossistemas de saúde e bem-estar”, defende o CEO da Mude, Marcus Moraes.
Como utilizar
A população pode usufruir da sala completa de musculação e aulas coletivas de diversas modalidades gratuitamente. Para realizar as atividades, é necessário baixar o aplicativo Mude – Yoga e Fitness, concluir o cadastro e agendar o horário. O funcionamento dos espaços está condicionado à presença de um profissional de educação física, conforme exigência do Conselho Regional da categoria.
```

Fonte: [Agência Brasília (GDF)](https://www.agenciabrasilia.df.gov.br/w/academia-publica-do-parque-da-cidade-vira-ponto-de-encontro-e-saude-para-brasilienses). Publicação: 11/01/2025. Coleta: 2026-11-07.

Validação: Pendente de validação humana. Ressalvas: Horários e perfil de uso referem-se a 2024/2025: confirmar atualidade. Espaço mantido em parceria com empresas privadas. AVISO: texto da fonte, com limpeza de ruído de interface descrita em AUDITORIA.md. Confira no link antes de usar como informação oficial..

## Q4 — consulta submetida

Qual quadra tem vaga disponível amanhã às 19h e acessibilidade verificada para cadeirantes?

### Ranking real dos chunks

| Posição | Chunk | Similaridade | Fonte |
|---|---|---|---|
| 1 | N05-024 | 0.8563 | [N05](https://www.sinj.df.gov.br/sinj/Norma/f82224a2df8f4c5aba3f200f1941c6a0/Lei_6637_20_07_2020.html) |
| 2 | R04-005 | 0.8546 | [R04](https://metadados.seduh.df.gov.br/geonetwork/srv/por/catalog.search#/metadata/22fe3be6-795b-458a-abc6-14c024d04ab8) |
| 3 | N05-016 | 0.8502 | [N05](https://www.sinj.df.gov.br/sinj/Norma/f82224a2df8f4c5aba3f200f1941c6a0/Lei_6637_20_07_2020.html) |
| 4 | F066-005 | 0.8500 | [F066](https://www.ceilandia.df.gov.br/w/governo-do-df-amplia-acessibilidade-e-entrega-novo-pec-para-os-moradores-de-ceilandia) |
| 5 | F066-001 | 0.8485 | [F066](https://www.ceilandia.df.gov.br/w/governo-do-df-amplia-acessibilidade-e-entrega-novo-pec-para-os-moradores-de-ceilandia) |

### Resposta fundamentada — síntese humana

Não é possível confirmar uma quadra com vaga em 09/11/2026 às 19h e acessibilidade verificada. Os resultados recuperados tratam de normas, cadastros e notícias; não trazem agenda em tempo real nem laudo de acessibilidade do local. Não há base suficiente para indicar um espaço que cumpra esses requisitos.

### Evidência textual recuperada

**N05-024 — Lei nº 6.637/2020 (Estatuto da Pessoa com Deficiência do DF): recorte do Cap. VIII e do Cap. IX (Seções I a III)**

```text
tecnicamente possível.Art. 112. O projeto e o traçado dos elementos de urbanização públicos e privados de uso comunitário, compreendidos os itinerários e as passagens de pedestres, os percursos de entrada e saída de veículos, as escadas e as rampas, devem observar os parâmetros estabelecidos pelas normas técnicas de acessibilidade em vigor.Art. 113. Os parques, praças, jardins e espaços livres públicos devem dispor de pelo menos 2 instalações sanitárias acessíveis, sendo uma masculina e uma feminina, em conformidade com as normas técnicas de acessibilidade em vigor, incluindo identificação e rota acessível.Art. 114. Em todas as áreas de estacionamento de veículos localizadas em vias ou em espaços públicos, devem ser reservadas vagas próximas dos acessos de circulação de pedestres,
```

Fonte: [Governo do Distrito Federal (lei distrital; texto no SINJ-DF)](https://www.sinj.df.gov.br/sinj/Norma/f82224a2df8f4c5aba3f200f1941c6a0/Lei_6637_20_07_2020.html). Publicação: 20/07/2020. Coleta: 2026-11-07.

Validação: Pendente de validação humana. Ressalvas: RECORTE de uma lei de 148 mil caracteres (texto integral no link). O próprio texto indica dispositivos vetados pelo Governador e mantidos pela Câmara Legislativa; conferir vigência e redação consolidada..

**Análise de insuficiência:** o melhor score foi alto mesmo sem resposta suficiente. Norma de acessibilidade não comprova acessibilidade de uma quadra específica; cadastro não comprova disponibilidade. Este caso evidencia o limite do ranking semântico.

## Roteiro de apresentação (3 a 5 minutos)

1. Mostrar o catálogo com 25 fontes e explicar a curadoria e a validação humana pendente.
2. Mostrar o diagrama e resumir o fluxo: fontes → chunks → embeddings → Chroma → consulta → evidências.
3. Executar python src/main.py com a pergunta Q1 ou abrir o registro pronto; mostrar N03-003 em primeiro lugar e conferir a lista de modalidades no trecho.
4. Mostrar a resposta extrativa, o ID, a URL e as datas. Explicar que a síntese deste documento foi revisada por pessoa.
5. Mostrar Q4: score alto não prova agenda ou acessibilidade. A conclusão correta na revisão é evidência insuficiente.

## Evidências e reprodução

OK: todos os chunks conferidos. OK: 5 vetores recalculados com o E5 e comparados ao banco (tolerância 0,0001).

O JSON conserva todos os 20 chunks retornados, sem truncar texto, além de distâncias, similaridades, metadados e respostas automáticas. O relatório pode ser conferido sem executar o modelo. Para repetir, seguir pipeline-ingestao.md; resultados podem variar ligeiramente entre versões e plataformas.
