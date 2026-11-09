# Documentos-fonte em texto (25)

Pasta com 25 documentos-fonte em texto copiável (.txt), o PDF original do manual (F003), a lista com título, órgão, link e tema, e a auditoria.

- [`LISTA_FONTES.md`](LISTA_FONTES.md) e [`lista_fontes.csv`](lista_fontes.csv): título, órgão, link, tema (e abrangência, datas, ressalvas, hash).
- [`AUDITORIA.md`](AUDITORIA.md): situação individual, o que foi corrigido, substituído e excluído, e o que ainda está pendente.

## Como ler os documentos

Cada .txt começa com um cabeçalho (título, órgão, link, tema, abrangência, tipo de evidência, **se comprova funcionamento atual**, datas, ressalvas) seguido do texto da fonte.
**Estado de todos: pendente de validação humana.** Constar de notícia ou de cadastro não prova que o espaço esteja aberto ou acessível.

Prefixos de ID: `F` = fonte já presente na base do projeto; `N` = fonte nova da auditoria; `R` = cadastro oficial de localização da SEDUH-DF (4 documentos).

O pacote foi originalmente extraído no projeto PontoAtivo RAG. Neste repositório, o pipeline atual ingere todos os 25 textos (F, N e R). Para a entrega atual, consulte `dados/catalogo.csv`, `docs/semana-02/pipeline-ingestao.md` e as evidências da demonstração. A auditoria e `lista_fontes.csv` preservam observações históricas da seleção anterior, inclusive referências à antiga base do RAG; essas referências não descrevem a composição do índice atual.
