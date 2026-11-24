# Demonstração de Processamento de PDF e Markdown — PontoAtivo

## 1. Objetivo

Demonstrar o processamento de documentos em diferentes formatos utilizando o pipeline de carregamento e processamento do PontoAtivo.

O experimento utiliza um documento PDF e um documento Markdown para verificar a extração de texto, a criação de chunks e a divisão desses chunks em segmentos menores.

## 2. Fontes utilizadas

| ID | Documento | Formato | Situação |
|---|---|---|---|
| DOC-003 | Manual de Uso dos Centros Olímpicos e Paralímpicos | PDF | Aprovada |
| DOC-025 | Guia dos Espaços Públicos de Lazer do Distrito Federal | Markdown | Aprovada com ressalvas |

**Observação sobre DOC-025:** trata-se de uma pesquisa acadêmica que utiliza dados do GeoPortal-DF referentes ao período de 2015 a 2020. Não deve ser apresentada como fonte oficial ou como retrato necessariamente atualizado dos espaços públicos.

## 3. Tecnologias e recursos utilizados

- Python;
- Pipeline de carregamento do PontoAtivo;
- Extração de texto de PDF;
- Leitura de documentos Markdown;
- Criação de chunks com `create_parent_chunks`;
- Criação de segmentos com `create_embedding_segments`;
- Exportação dos resultados em JSONL e JSON.

## 4. Etapas do processamento

1. Leitura do catálogo de fontes.
2. Seleção dos documentos DOC-003 e DOC-025.
3. Carregamento dos arquivos conforme seus formatos.
4. Extração e normalização do conteúdo textual.
5. Divisão do conteúdo em chunks.
6. Divisão dos chunks em segmentos menores.
7. Geração dos arquivos de resultados e do relatório JSON.

## 5. Resultados obtidos

| Indicador | DOC-003 | DOC-025 | Total |
|---|---:|---:|---:|
| Caracteres extraídos | 7.943 | 18.496 | 26.439 |
| Chunks | 5 | 17 | 22 |
| Segmentos | 12 | 31 | 43 |

O PDF apresentou quatro páginas com texto extraível. O documento Markdown foi processado como texto, por isso não possui contagem de páginas.

Não foram identificadas páginas sem texto nem páginas com imagens nos resultados desta execução.

## 6. Arquivos gerados

A pasta `resultados/` contém:

- `documentos_normalizados.jsonl`: documentos após o carregamento e a normalização.
- `chunks.jsonl`: blocos de texto criados.
- `segmentos.jsonl`: segmentos menores derivados dos chunks.
- `relatorio.json`: resumo da execução e indicadores por documento.

## 7. Como executar

Na raiz do repositório, com o ambiente virtual ativado, execute:

```bash
python docs/entregas/semana-06/multimodalidade-pdf-texto/demonstrar_pdf_texto.py
```

Os resultados serão gravados na pasta `resultados/` desta demonstração.

## 8. Limitações e escopo

Esta demonstração comprova o processamento de documentos em formatos diferentes, mas não representa, isoladamente, uma implementação completa de inteligência multimodal.

O experimento:

- Extrai texto de PDF e Markdown.
- Identifica páginas com imagens quando aplicável ao PDF.
- Não executa OCR.
- Não interpreta visualmente imagens, fotografias, gráficos ou diagramas.
- Não gera embeddings nem realiza busca vetorial nesta execução.

A identificação de uma página com imagens não significa que seu conteúdo visual tenha sido compreendido pelo sistema.

## 9. Conclusão

O experimento demonstrou que o pipeline do PontoAtivo consegue processar documentos PDF e Markdown, normalizar seus conteúdos e organizá-los em chunks e segmentos menores.

Foram processadas duas fontes, com 22 chunks e 43 segmentos gerados. Os resultados foram salvos em arquivos estruturados para facilitar a inspeção e o uso em etapas posteriores do projeto.

Esta etapa estabelece uma base para futuras evoluções, como OCR, interpretação de imagens e integração com embeddings e recuperação semântica.