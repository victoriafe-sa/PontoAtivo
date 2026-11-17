# Estratégia de chunking

O PontoAtivo usa duas granularidades porque a unidade boa para leitura humana
não é necessariamente a unidade aceita integralmente pelo modelo de embeddings.

## Chunks-pai

Os documentos são divididos inicialmente em trechos de aproximadamente 450
tokens, com sobreposição de 50. Nesta implementação inicial, um token é
aproximado por uma palavra separada por espaço. A aproximação é determinística,
simples de auditar e não exige carregar o tokenizador do modelo durante a
extração. Páginas de PDF não são misturadas, preservando a referência.

Esses chunks são apresentados ao usuário, enviados ao gerador e citados nas
respostas. A sobreposição reduz a chance de uma informação situada na fronteira
entre dois chunks perder o contexto anterior.

## Segmentos de embedding

Cada chunk-pai é subdividido em segmentos de no máximo 120 tokens. Os modelos de
embedding têm janela limitada (o E5 lê até 512 tokens, e o MiniLM usado antes, bem
menos); enviar 450 palavras de uma vez diluiria o sentido ou seria truncado em
silêncio. Somente os segmentos
curtos são vetorizados. Depois da busca, os resultados são agrupados pelo
identificador do chunk-pai e o texto completo volta a ser a unidade citável.

## Rastreabilidade

IDs são derivados do documento, checksum, posição e conteúdo. Assim, o mesmo
arquivo processado com a mesma configuração produz IDs estáveis, enquanto uma
alteração real de conteúdo gera novos identificadores.
