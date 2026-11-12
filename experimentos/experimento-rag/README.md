# Experimento de LLM com RAG

O experimento reúne 20 perguntas, cinco trechos recuperados por pergunta e 60 respostas distribuídas entre Gemini, Qwen e Llama. Os prompts pedem respostas em português, com até 200 palavras, citações por ID e reconhecimento dos limites das evidências. A avaliação está em [analise-respostas.md](analise-respostas.md).

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `prompts/q1.txt` a `q20.txt` | Pergunta, instruções e evidências locais de referência. |
| `evidencias/q1-evidencias.json` a `q20-evidencias.json` | Resultados do pipeline usados como referência documental. |
| `respostas-gemini/`, `respostas-qwen/`, `respostas-llama/` | Textos das respostas preservados. |
| `brutos/<modelo>-qN.json` | Registros documentais importados dos TXT existentes, com origem e campos ausentes explícitos. **Não estão versionados** (ver abaixo). |
| `metricas.csv` | Uma linha por pergunta e grupo de modelo, com referências aos arquivos e situação das métricas. |
| `analise-respostas.md` | Avaliação qualitativa das respostas e limitações. |

## Origem e limites dos registros históricos

> **Registros ausentes no repositório:** os 60 JSONs históricos `brutos/<modelo>-qN.json` nunca foram incluídos no Git, embora sejam citados na coluna `arquivo_bruto` do `metricas.csv`. Também faltam os JSONs de duas rodadas do Gemini com falha (`rodada-20261112-084429-326726/q1.json` e `rodada-20261112-084513-664720/q1.json`) e os de Q14–Q20 da `rodada-20261112-084720-482124`. As linhas do CSV foram mantidas como estão; as respostas em TXT continuam disponíveis. Se os arquivos forem recuperados, basta adicioná-los nos caminhos indicados.

Os 60 JSONs de `brutos/` foram organizados posteriormente a partir dos arquivos locais. **Não são respostas brutas de API nem logs recuperados da execução original.** Cada registro preserva o TXT integral em `conteudo_arquivo_original`, sua assinatura SHA-256 e o texto da resposta separado dos cabeçalhos. Os TXT originais não foram alterados.

O campo `modelo` reproduz a identificação explícita no conteúdo original quando ela existe. Quando ausente, fica nulo; `grupo_modelo` identifica somente a pasta. Uma anotação no TXT não confirma a versão efetivamente utilizada. O canal de execução também não pode ser deduzido da família do modelo.

Prompts, evidências e hash do prompt indicam referências locais atuais. Não comprovam a entrada efetivamente enviada, seu processamento integral ou a ausência de truncamento.

Datas de execução, tokens, tempos, configuração, provedor e demais informações não disponíveis ficam nulos nos JSONs ou vazios no CSV. **Vazio não significa zero.** Todas as 60 linhas históricas do CSV têm `status_metricas=nao_registradas`. Não é possível reconstruir tokens e latência reais apenas a partir dos TXT, nem usar a data dos arquivos como data da execução.

As colunas básicas do CSV seguem o experimento sem RAG. Foram acrescentadas `status_metricas`, `origem_modelo`, `arquivo_resposta` e `arquivo_bruto` para explicar a ausência de medidas e permitir rastrear cada linha.

## Correspondência com o experimento sem RAG

| ID nos dois experimentos | Tema |
|---|---|
| Q1 | Gratuidade e uso da academia do Parque da Cidade |
| Q2 | Modalidades dos Centros Olímpicos e Paralímpicos |
| Q3 | Endereço do Bezerrão |
| Q4 | Disponibilidade de quadra e acessibilidade |

O [experimento sem RAG](../experimento-sem-rag/README.md) contém somente Q1–Q4. As perguntas Q5–Q20 ainda não possuem correspondentes sem RAG. No cenário sem RAG, os documentos em `cenario-referencia/` servem à avaliação e não são enviados aos modelos.

## Novas execuções

O script [rodar_experimentos_rag.py](../../scripts/rodar_experimentos_rag.py) permite executar novas rodadas separadamente. Para conferir os prompts sem chamar serviços:

```bash
python3 scripts/rodar_experimentos_rag.py --modelo llama --inicio 1 --fim 20 --simular
```

Com o Ollama em execução e o modelo instalado, remova `--simular`. Para Qwen, use `--modelo qwen`. Para Gemini, use `--modelo gemini`, com a dependência `google-genai` instalada e a chave informada por `GEMINI_API_KEY` ou pelo prompt oculto do script.

O script atual solicita `llama3.2:3b`, `qwen3:8b` ou `gemini-3.5-flash-lite`. Para Ollama usa `/api/chat`, temperatura 0, seed 42, contexto 8.192 e limite de saída 4.096; no Qwen desativa o raciocínio. Para Gemini solicita temperatura 0 e limite de saída 4.096. **Essas configurações descrevem o script atual e não comprovam as configurações dos resultados históricos.**

Novas rodadas são salvas automaticamente nestes caminhos:

```text
brutos/<modelo>/rodada-<data-hora>/ambiente.json
brutos/<modelo>/rodada-<data-hora>/qN.json
respostas-<modelo>/rodada-<data-hora>/qN.txt
metricas.csv
```

Cada JSON contém a entrada enviada, saída completa da API, identificação da rodada, referências aos arquivos e métricas extraídas. Após cada chamada, o CSV recebe uma nova linha, sem substituir as 60 linhas históricas nem rodadas anteriores. Os caminhos `arquivo_bruto` e `arquivo_resposta` identificam a rodada. Em falhas, o JSON e a linha com `status_metricas=falha` são preservados, e o lote é interrompido. Métricas não retornadas permanecem vazias; `parciais` indica falta de contagem de entrada ou saída. Os registros históricos continuam com `nao_registradas`.

No Ollama, os tempos retornados em nanossegundos são convertidos para segundos, e tokens/s usa apenas o tempo de geração. O tempo total pode incluir carregamento do modelo. No Gemini, o CSV registra tempo de ponta a ponta, incluindo rede e eventuais tentativas; não estima tempo de geração nem tokens/s. Tokens totais vêm da API e podem incluir raciocínio, cuja contagem detalhada permanece na saída bruta. Portanto, não se deve comparar diretamente a latência do serviço remoto com a geração local.

Para comparar o efeito do RAG, padronize os parâmetros dos dois cenários e use as mesmas perguntas e versões de modelo. As métricas da rodada sem RAG não devem preencher lacunas da rodada com RAG.
