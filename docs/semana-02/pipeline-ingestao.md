# Pipeline de ingestão de dados

## Entrada e curadoria

A entrada efetiva é o conjunto de 25 arquivos F###, N## e R## em dados/fontes/texto/. O PDF F003_original.pdf é o original de uma dessas fontes, não um 26º documento. Listas, README e auditoria não são ingeridos. Os cadastros SEDUH são quatro documentos-fonte compostos por registros; registros individuais não foram contados como documentos extras.

A seleção cobre espaços esportivos do DF, modalidades, regras e acessibilidade. Houve remoção de ruído, substituição de fontes redundantes ou inadequadas, correção de metadados e identificação de fontes antigas. O histórico e as limitações por fonte estão em dados/fontes/texto/AUDITORIA.md. Essa é curadoria documental, com validação humana das informações ainda pendente. Não houve nova verificação online nesta finalização.

## Transformação e carga

1. **Inventário:** o catálogo dados/catalogo.csv registra os cabeçalhos dos 25 textos e o SHA-256 dos arquivos entregues. O catálogo suplementar lista_fontes.csv preserva o histórico anterior; o catálogo principal é o inventário do corpus atual. A carga lê metadados dos textos, sem depender do CSV.
2. **Leitura:** extrair título, órgão, URL, datas, abrangência, evidência, validação, ressalvas e corpo. Fontes já estão extraídas e limpas; o pipeline atual não baixa páginas nem reextrai PDFs.
3. **Chunking de texto:** até 800 caracteres, com sobreposição alvo de 120, respeitando frases e palavras; abreviações legais recebem tratamento específico.
4. **Chunking de cadastros:** agrupar registros inteiros até 1.000 caracteres, repetindo o cabeçalho, sem sobreposição. Três registros vazios de R03 são descartados.
5. **Rastreabilidade:** ID global (ex.: N03-003), índice do chunk, fonte e metadados. Preservar texto original em texto; título e região enriquecem texto_indexado.
6. **Embeddings:** prefixar texto_indexado com passage:; codificar com intfloat/multilingual-e5-base; normalizar; produzir 768 números por chunk. Não são usadas chaves de API.
7. **Persistência:** recriar a coleção pontoativo_fontes do Chroma em dados/vetorial/, com cosseno; gravar IDs, vetores, textos e metadados em lotes de 256.
8. **Verificação:** conferir contagem do banco contra os chunks; rodar os testes de forma, banco e embeddings; conferir todos os textos/metadados contra as fontes e registrar consultas reais.

**Atenção operacional:** executar a carga substitui a coleção anterior. Ao modificar fontes, chunking ou modelo, refazer a ingestão e a demonstração. O JSONL é uma exportação para inspeção; a carga lê os arquivos-fonte diretamente.

## Como reproduzir no Windows (PowerShell)

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe src/ingestao/chunking.py --saida dados/chunks.jsonl
.venv/Scripts/python.exe src/ingestao/carga.py
.venv/Scripts/python.exe tests/teste_chunking.py
.venv/Scripts/python.exe tests/teste_banco.py
.venv/Scripts/python.exe tests/teste_embeddings.py
.venv/Scripts/python.exe src/main.py "Qual é o endereço do Estádio Bezerrão no Gama?" -k 5
```

Se usar o banco pronto do pacote, pode pular a carga. O modelo (~1 GB) precisa ser baixado na primeira consulta; depois do cache local é possível usar $env:HF_HUB_OFFLINE='1'. Os requisitos indicam intervalos de versão, não um ambiente travado. No Artefatos.zip, as fontes estão em base_conhecimento/fontes/ e a implementação em implementacao/; executar a carga a partir de implementacao/ usa esse caminho de fontes adaptado.

## Saídas e limites

- dados/chunks.jsonl: chunks legíveis, texto indexado e metadados.
- dados/vetorial/: banco persistente, incluído no ZIP do Teams.
- demonstracao/resultado.json: execução sobre o Artefatos.zip, com consulta, ranking completo, textos, scores, metadados e resposta extrativa. Também registra a conferência dos 599 textos e metadados do banco contra as fontes.
- demonstracao/Demonstracao_PontoAtivo.pdf: demonstração da consulta, da recuperação, da resposta automática e de suas fontes.

O pipeline não atualiza dados automaticamente, não confirma acessibilidade e não consulta uma agenda. Notícias antigas e camadas cadastrais obsoletas permanecem identificadas pelas ressalvas. O corpus é uma base para demonstração acadêmica; a presença de uma informação no índice não a transforma em informação verificada hoje.
