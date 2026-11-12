# Análise qualitativa do piloto

Rodada: `rodadas/20261112-092351-979787`. Cenário em 12/11/2026, com solicitações operacionais para 13/11/2026. Leitura documental das respostas; não é uma verificação da situação atual dos espaços. Esta análise não representa avaliação cega nem concordância entre avaliadores. A planilha de avaliação formal permanece disponível para preenchimento humano.

## Llama — teste 1

| Caso | Sem RAG | RAG curto |
|---|---|---|
| 01a: idade COPs | Não informa idade. | Recupera 4 anos; acrescenta ressalva confusa sobre não confirmar faixa etária ampla, explícita no trecho. |
| 01b: idade Semear | Reconhece desconhecimento. | Não transfere 4 anos; distingue explicitamente COPs e Semear. |
| 02a: modalidades COPs | Recusa por ausência de informação atual. | Lista as 12 modalidades; reconhece lista exemplificativa, mas omite ID e variação por unidade. |
| 02b: modalidades Escola Paralímpica | Reconhece desconhecimento específico; acrescenta generalização externa não verificada neste conjunto. | Não transfere a lista para a escola; contextualiza COPs. |
| 03a: academia pública | Afirma necessidade de taxa/cartão e depois diz não saber se é gratuita. Contradiz a gratuidade documental, sem comprovar mudança atual. | Informa gratuidade e aplicativo/cadastro/agendamento; omite condição de presença de profissional. Chama o período histórico “2024/2025”, presente nos metadados, de data de referência; o cenário é de 2026. |
| 03b: academia privada | Não responde; acrescenta descrição inadequada do Lago Sul como espaço esportivo. | Não transfere gratuidade; reconhece falta de informação, mas não identifica a evidência examinada. |

Nos três casos `b`, não houve transferência direta do fato da entidade errada no RAG curto. Isso não demonstra robustez geral: são três controles e uma execução. O contraste com falhas históricas não isola uma causa, pois contexto e configuração podem diferir.

## Llama — teste 2

| Caso | Sem RAG | RAG curto |
|---|---|---|
| 01: Bezerrão | Não informa endereço nem capacidade; não confirma reserva. | Informa endereço e capacidade estimada, reconhece falta de agenda. Atribui indevidamente a capacidade a dados de 2019: essa data se refere à competição citada, não à estimativa. |
| 02: academia | Reconhece falta de informação e de agenda. | Recupera gratuidade e não confirma horário; omite aplicativo, cadastro, agendamento e condição de profissional, disponíveis no trecho. |
| 03: COPs | Expande COPs como “Copa do Pará” e associa a torneio/CBF, desviando da entidade solicitada; não confirma vaga. | Informa 4 anos, mas nega poder confirmar inclusão de PcD enquanto cita o trecho que a explicita. Também contradiz a própria resposta ao dizer que o trecho não informa idade mínima e afirma inacessibilidade do site sem ter ferramenta de navegação. |

O RAG curto melhora o aproveitamento de alguns fatos, mas não elimina contradições, omissões ou afirmações sem suporte. Não confirmar vagas foi adequado; a recusa sobre PcD, no caso 03, foi indevida.

## Llama — teste 3

| Pergunta | Sem RAG | Curto | Alvo no início | Alvo no meio | Alvo no fim |
|---|---|---|---|---|---|
| Endereço Bezerrão | Não fornece endereço. | Altera “St. Central” para “Rua Central”; cita F059 em vez de F059-001. | Mesma alteração e reprodução extensa do JSON de fonte. | Trata CEP como número de imóvel e acrescenta “Rua”. | Reproduz corretamente o endereço e cita F059-001. |
| Uso da academia | Afirma taxa/cartão sem base documental. | Gratuidade e procedimento, sem condição do profissional. | Gratuidade e procedimento, sem condição do profissional. | Gratuidade e procedimento, sem condição do profissional. | Inclui também a presença do profissional; faltam ressalvas temporais. |
| Idade COPs | Não informa idade. | Informa 4 anos e cita F028-001. | Informa 4 anos, sem fonte ou limites. | Informa 4 anos, sem fonte ou limites. | Informa 4 anos, mas atribui suporte a N01-049 e N03-003, que não estabelecem idade no contexto. |

A posição altera a forma e a fidelidade de algumas respostas nesta rodada. Não há evidência suficiente para uma regra geral de que o fim seja melhor: ele ajuda no endereço, mas piora a atribuição da idade. O acerto factual isolado esconderia erros de citação.

## Qwen — teste 1

| Caso | Sem RAG | RAG curto |
|---|---|---|
| 01a: idade COPs | Não informa idade; alega ausência de fontes públicas confiáveis, embora o snapshot contenha informação institucional. | Informa 4 anos e cita F028-001. |
| 01b: idade Semear | Afirma 12 anos sem fonte verificável neste conjunto; não é possível validar esse valor com o gabarito documental. | Não transfere idade dos COPs; reconhece falta de evidência sobre Semear. |
| 02a: modalidades COPs | Lista modalidades sem referência verificável; várias não aparecem no trecho de referência, que também não é exaustivo. | Lista as 12 modalidades documentadas, preservando variação por unidade, caráter exemplificativo e limite temporal. |
| 02b: modalidades Escola Paralímpica | Lista modalidades sem referência verificável no conjunto. | Transfere as 12 modalidades dos COPs para a escola. A ressalva posterior de que não pode confirmar a oferta específica não desfaz a afirmação inicial. |
| 03a: academia pública | Afirma acesso sem cadastro, em conflito com o procedimento documental, sem evidência de mudança atual. | Recupera gratuidade, aplicativo, cadastro, agendamento e presença de profissional, com fonte e limite temporal. |
| 03b: academia privada | Oferece generalizações sobre academias privadas sem identificar um estabelecimento. | Distingue a academia pública da privada e reconhece falta de dados específicos. |

Neste controle, houve transferência direta da entidade em um dos três casos `b` com RAG (Escola Paralímpica). Os outros dois preservaram o limite. Não se trata de taxa geral de erro do modelo. No caso da escola, a presença de citação dá rastreabilidade, mas não torna correta a atribuição.

## Qwen — teste 2

| Caso | Sem RAG | RAG curto |
|---|---|---|
| 01: Bezerrão | Não fornece endereço nem capacidade; alega ausência de registros oficiais, extrapolando seu desconhecimento. | Fornece endereço e capacidade estimada; não confirma reserva. Chama a capacidade de “não confirmada oficialmente”, embora o trecho seja institucional: o correto é preservar a condição de estimativa da fonte. |
| 02: academia | Informa gratuidade e possível agendamento, sem o procedimento específico; não confirma vaga. | Informa gratuidade e agendamento no Mude; não confirma horário. Omite cadastro e presença de profissional, portanto não cobre integralmente o gabarito. |
| 03: COPs | Expande COPs como “Caminhadas Olímpicas Populares” e sugere participação a partir de 5 anos sem suporte verificável; não confirma vaga. | Informa 4 anos, inclusão de PcD e ausência de confirmação de vaga específica, com F028-001. |

O RAG melhora a resposta parcial nesses exemplos, mas completude e ressalvas ainda precisam ser avaliadas separadamente. Nenhuma das três respostas com RAG confirmou disponibilidade para a data solicitada.

## Qwen — teste 3

| Pergunta | Sem RAG | Curto | Alvo no início | Alvo no meio | Alvo no fim |
|---|---|---|---|---|---|
| Endereço Bezerrão | Afirma “Avenida das Américas, 1000”, divergente da referência, sem evidência de alteração. | Endereço documental correto e F059-001. | Endereço correto, datas da página e F059-001. | Endereço correto e F059-001. | Endereço correto e F059-001. |
| Uso da academia | Diz que não precisa de cadastro, divergindo da referência. | Recupera gratuidade e procedimento completo, com condição de profissional. | Mantém os fatos e cita N04-008. | Mantém os fatos e cita N04-008. | Mantém os fatos e cita N04-008; acrescenta hipótese não sustentada de influência da parceria privada sobre a operação. |
| Idade COPs | Não informa idade e alega ausência de fonte pública. | Informa 4 anos e F028-001. | Informa 4 anos e F028-001; alega ausência de documentos mais recentes sem delimitar a busca ao contexto recebido. | Informa 4 anos e F028-001, com ressalva de atualidade. | Informa 4 anos e F028-001. |

O Qwen preservou os fatos centrais e os IDs corretos nas três posições desta rodada. Isso não significa respostas integralmente corretas: há ressalvas excessivas e hipóteses adicionais sem suporte. O ruído não produziu a degradação central observada no Llama nesses três exemplos.

## Integridade e métricas

Foram concluídas **66 respostas**, 33 por modelo, sem registros ausentes ou falhas. Todas retornaram `done_reason=stop`; nenhuma ultrapassou 200 palavras pelo critério de separação por espaços, incluindo fontes. O maior número de tokens de entrada foi 3.054 no Llama e 3.180 no Qwen. Isso é compatível com a janela solicitada de 8.192, mas não comprova por si só ausência de truncamento.

A mediana do tempo de cliente foi 4,85 s no Llama e 17,99 s no Qwen. Esses valores agregam condições com tamanhos diferentes, incluem carga quando presente e não constituem benchmark isolado. As contagens por chamada, digest e quantização estão em `metricas.csv` e nos JSONs. Verificação: `rodadas/20261112-092351-979787/verificacao.md`.

As respostas das perguntas repetidas entre os testes 1 e 3, tanto sem RAG quanto com contexto curto, foram idênticas byte a byte em cada modelo. Isso reforça que não devem ser contadas como replicações independentes.

Gemini não foi executado neste piloto. O executor está preparado para uma rodada adicional com esse modelo; não há resultados ou métricas estimados para ele.

## Limites da comparação

- Sem RAG não recebe o gabarito nem documentos; a ausência de ID não é erro nesse cenário.
- “Não sei” não equivale a provar que uma informação não foi publicada. É preciso separar desconhecimento de alegações sobre inexistência de fontes.
- Os controles não demonstram o que a busca automática recuperaria para as novas perguntas.
- As perguntas de idade e uso da academia reaparecem em testes diferentes; respostas repetidas não são evidência independente.
- A pergunta t2-03 usa apenas a sigla COPs. Sem RAG, ambos os modelos a expandem incorretamente; portanto, esse caso mistura desambiguação da entidade com resposta parcial. Uma próxima rodada deve incluir uma versão com o nome por extenso para separar esses fatores.
- Uma repetição por condição não estima variabilidade. Não foram calculados testes de significância, ranking geral ou porcentagem agregada de qualidade.
- O limite de 200 palavras é verificado à parte; boa formatação não implica resposta correta.
