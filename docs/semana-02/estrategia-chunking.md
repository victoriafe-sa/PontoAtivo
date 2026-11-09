# Estratégia de chunking

Chunking é a divisão de cada documento-fonte em trechos menores (*chunks*), que são indexados no banco vetorial e recuperados quando combinam com a pergunta. Este documento descreve como o PontoAtivo faz essa divisão, por quê, e o que foi testado.

Código: `src/ingestao/chunking.py`. Testes: `tests/teste_chunking.py`.

## Resumo

| Item | Definição |
|---|---|
| Entrada | 25 documentos de `dados/fontes/texto/` (arquivos `F###`, `N##`, `R##`) |
| Saída | **599 chunks**: 243 de texto corrido e 356 de registros de cadastro |
| Tamanho (texto corrido) | até 800 caracteres (média 665, mínimo 122) |
| Sobreposição (texto corrido) | 120 caracteres |
| Tamanho (cadastros) | até 1.000 caracteres, incluindo o cabeçalho de colunas (média 937) |
| Onde corta | No fim de frase; se a frase for maior que o limite, em espaço |
| Idioma | Português |

## Ponto de partida e por que 800/120

A configuração inicial (800 caracteres, sobreposição de 120, preferência por fim de frase) vem da proposta de chunking da equipe. Ela se mantém porque 800 caracteres equivalem a cerca de 200 tokens, bem abaixo do limite de 512 do modelo de embeddings `intfloat/multilingual-e5-base` (ver `estrategia-embeddings.md`), e porque trechos curtos tendem a tratar de um único assunto. A estimativa de tokens não foi medida com o tokenizer do modelo.

Antes de adotar a proposta, a função original foi executada nos 25 documentos reais. Ela gerou 610 chunks e revelou quatro problemas, corrigidos na versão atual:

| Problema encontrado | Efeito | Correção |
|---|---|---|
| O `id` reiniciava em 1 a cada documento (361 repetidos) | O banco vetorial exige id único; os chunks se sobrescreveriam | Id global: `ID da fonte` + número, como `F028-003` |
| A sobreposição começava 120 caracteres antes do corte, no meio de palavras (cerca de 48% dos chunks começavam em letra minúscula) | Embedding e citação piores | A sobreposição começa em início de frase ou de palavra. Teste automático confirma que nenhum chunk de texto começa no meio de palavra |
| Todo ponto seguido de espaço era fim de frase (`Art.`, `Inc.`, `1.`, `Art. 97.`) | Chunks terminavam em `Art.` nas normas (F064, N01, N05) | Abreviações e numeração não encerram frase; o corte forçado também não separa `Art.` do número |
| Todas as quebras de linha eram apagadas | Os cadastros R01 a R04 (lista de registros) eram cortados no meio de um registro | Cadastros são divididos por registro, sem cortar nenhum, e cada chunk repete o cabeçalho de colunas |

## Dois tipos de documento

**Texto corrido** (notícias, páginas de órgãos, manual, decreto, portaria, lei): as linhas do original são preservadas como parágrafos. As frases são agrupadas até 800 caracteres. Cada novo chunk repete os últimos 120 caracteres do anterior, para que uma informação na fronteira apareça inteira em pelo menos um deles.

**Cadastros oficiais da SEDUH (R01 a R04)**: são listas de registros no formato `tipo | região | endereço | ...`. Cada registro é uma unidade que não pode ser cortada. Os registros são agrupados até 1.000 caracteres e cada chunk começa com duas linhas repetidas: a linha que descreve o conjunto (por exemplo, "REGISTROS DO TIPO PEC...") e a linha de colunas. Sem isso, um chunk com registros soltos não diria o que cada campo significa. Não há sobreposição, porque os registros são independentes.

Nos cadastros, 3 registros do R03 sem nenhuma informação (todos os campos vazios ou "—", só com data) foram descartados. Nenhum outro conteúdo foi removido ou reescrito.

## Dois textos por chunk

| Campo | Conteúdo | Para que serve |
|---|---|---|
| `texto` | O trecho exatamente como está na fonte | Mostrar a evidência e citar |
| `texto_indexado` | O mesmo trecho precedido do título do documento (e da região, nos cadastros) | Gerar o embedding |

O título e a região no começo ajudam a busca: um chunk com registros soltos não diz de que cadastro nem de que região ele é.

## Metadados de cada chunk

Todos vêm do cabeçalho do próprio arquivo de texto, para a rastreabilidade não depender de preenchimento manual.

| Campo | Origem | Uso |
|---|---|---|
| `id_fonte`, `titulo`, `orgao`, `link` | Cabeçalho | Citação da fonte |
| `data_publicacao`, `data_coleta` | Cabeçalho | Mostrar a data da informação |
| `validacao` | Estado de validação (hoje, "Pendente de validação humana" em todos) | Avisar o usuário |
| `comprova_funcionamento`, `ressalvas` | Cabeçalho | Avisar que a fonte não prova que o espaço funciona ou é acessível |
| `abrangencia`, `tema`, `tipo_evidencia`, `recorte` | Cabeçalho | Filtros e contexto |
| `indice_chunk`, `total_chunks`, `tipo_chunk` | Gerado | Posição no documento e tipo (`texto` ou `registros`) |
| `regioes` | Gerado, só nos cadastros com coluna de região | Filtrar por região administrativa |

## Chunks por fonte

| Fonte | Título | Chunks | Tipo |
|---|---|---|---|
| F003 | Manual de Uso dos Centros Olímpicos e Paralímpicos do DF | 14 | texto |
| F006 | Sesc Ceilândia | 4 | texto |
| F007 | Sesc Taguatinga Norte (Unidade Francisco Valdenir Machado Elia | 6 | texto |
| F009 | Parque Urbano do Setor O se solidifica como espaço de lazer, s | 9 | texto |
| F016 | Praça Linear, na Avenida Hélio Prates, oferece lazer e esporte | 11 | texto |
| F028 | Centros Olímpicos e Paralímpicos | 9 | texto |
| F029 | Parque da Cidade Dona Sarah Kubitschek (SEL) | 4 | texto |
| F056 | Parques Distritais e Ecológicos sob gestão do Brasília Ambient | 10 | texto |
| F058 | Conjunto Aquático Cláudio Coutinho | 14 | texto |
| F059 | Estádio Bezerrão | 1 | texto |
| F060 | Estádio Joaquim Domingos Roriz (Rorizão) | 1 | texto |
| F061 | Estádio Abadião (Estádio Maria de Lourdes Abadia) | 1 | texto |
| F062 | Espaços Esportivos (SEL) | 4 | texto |
| F064 | Decreto nº 45.269, de 08/12/2023 | 6 | texto |
| F065 | PEC construído no GDF na Sua Porta promove saúde e lazer para  | 7 | texto |
| F066 | Governo do DF amplia acessibilidade e entrega novo PEC para os | 7 | texto |
| N01 | Portaria SEL nº 99, de 02/06/2022: Programa Centros Olímpicos  | 50 | texto |
| N02 | Centros olímpicos e paralímpicos abrem mais de 12 mil vagas no | 6 | texto |
| N03 | Centros Olímpicos e Paralímpicos do DF oferecem mais de 10 mil | 4 | texto |
| N04 | Academia pública do Parque da Cidade vira ponto de encontro e  | 8 | texto |
| N05 | Lei nº 6.637/2020 (Estatuto da Pessoa com Deficiência do DF):  | 42 | texto |
| R01 | Espaços comunitários (cadastro oficial SEDUH-DF) | 35 | registros |
| R02 | Mobiliário Esporte e Lazer: Pontos de Encontro Comunitário (ca | 73 | registros |
| R03 | Mobiliário Esporte e Lazer: quadras, campos, skate e ginástica | 255 | registros |
| R04 | Campos e Quadras Poliesportivas (cadastro oficial SEDUH-DF) | 18 | registros |

Os quatro cadastros (R01 a R04) concentram a maior parte dos chunks. Isso deve ser considerado ao avaliar a recuperação: perguntas sobre localização tendem a recuperar registros de cadastro, e perguntas sobre regras ou modalidades, os documentos de texto.

## Como foi testado

`tests/teste_chunking.py` roda na base real e verifica:

- 25 fontes lidas e todos os ids únicos;
- nenhum chunk acima do limite (800 para texto, 1.000 para cadastros);
- todos os campos de rastreabilidade preenchidos em todos os chunks;
- nenhum chunk terminando em `Art.`, `Inc.` ou outra abreviação;
- todo chunk de texto é um trecho contíguo da fonte e começa em início de palavra;
- todo chunk de cadastro tem o cabeçalho de colunas e nenhum registro cortado.

Estes testes verificam a **forma** dos chunks. Se a recuperação encontra os documentos certos é avaliado na demonstração (`demonstracao.md`).

## Limitações

- **Texto da fonte mantido como está.** Os `.txt` têm defeitos de extração, como palavras coladas no manual F003 ("DOSCENTROS EPARALÍMPICOS") e títulos colados no início de artigos na lei N05 ("...SOCIALArt. 97."). Eles não foram corrigidos para não alterar a fonte, e podem piorar a recuperação desses trechos.
- **Texto corrido e legislação.** Em N01, N05 e F064 o corte é por frase e tamanho, não por artigo; um artigo longo pode ser dividido em vários chunks.
- **Região e modalidade.** A proposta original previa campos de região administrativa e modalidade. Os cabeçalhos não trazem esses dados, então foram usados `abrangencia` (para todas as fontes) e `regioes` (nos cadastros). A modalidade não é extraída automaticamente.
- **Valores iniciais.** 800, 120 e 1.000 são pontos de partida. Se a avaliação da recuperação mostrar chunks perdendo sentido, eles devem ser ajustados e a base reindexada.
- **Horários.** A busca vetorial encontra regras, descrições e localização, mas não confirma horários disponíveis. Isso exigiria uma agenda ou base estruturada atualizada pelos responsáveis.

## Como rodar

```bash
python src/ingestao/chunking.py                          # mostra o resumo
python src/ingestao/chunking.py --saida dados/chunks.jsonl   # grava os chunks
python tests/teste_chunking.py                           # roda os testes
```

O módulo usa apenas a biblioteca padrão do Python. O JSONL gerado tem um chunk por linha, com `id`, `texto`, `texto_indexado` e `metadados`, pronto para a etapa de embeddings e carga no banco vetorial.
