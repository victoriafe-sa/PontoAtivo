# Documentação do assistente (RAG)

O assistente do PontoAtivo responde perguntas sobre esporte e acessibilidade no
DF a partir de 25 documentos oficiais. Ele busca os trechos mais próximos da
pergunta (embeddings multilingual-E5 no Chroma), gera a resposta com o Gemma 4
pelo Ollama e cita as fontes; quando os trechos não bastam, diz que não sabe.

## Por onde começar

1. [Como rodar](como-rodar.md): configuração, ingestão, chat no mapa, avaliação e diagnóstico.
2. [Pipeline](pipeline.md): o caminho de um documento até a resposta.
3. [Chunking](chunking.md) e [embeddings](embeddings.md): como os textos são divididos e
   representados, e por que o limiar de abstenção é 0,12 com o E5.
4. [Fontes](fontes.md): revisão das 25 fontes, datas e ressalvas.

## Onde ficam as coisas

| O quê | Onde |
|---|---|
| Código | [`src/pontoativo_rag/`](../../src/pontoativo_rag/) |
| Documentos-fonte e catálogo | [`dados/rag/fontes/`](../../dados/rag/fontes/) e [`dados/rag/catalogo.csv`](../../dados/rag/catalogo.csv) |
| Perguntas de avaliação | [`dados/rag/perguntas/`](../../dados/rag/perguntas/) |
| Arquivos gerados pela ingestão e índice | `dados/rag/gerado/` e `dados/rag/vetorial/` (fora do Git) |
| Resultado oficial, relatórios e histórico | [`experimentos/avaliacao-rag/`](../../experimentos/avaliacao-rag/) |
