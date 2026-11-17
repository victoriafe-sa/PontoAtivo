# Protótipo de consulta (semanas 1 e 2)

Primeira versão do RAG do PontoAtivo, entregue nas semanas 1 e 2. É um fluxo de
linha de comando: 25 documentos em texto, chunking por caracteres, embeddings E5,
Chroma e resposta do Gemma com citações.

**Ele continua aqui porque os experimentos com e sem RAG e o
[site de resultados](../docs/index.html) foram feitos com ele.** O sistema
principal do projeto (mapa, chat e encontros) é outro e fica em
[`src/pontoativo_rag/`](../src/pontoativo_rag/); veja o [README da raiz](../README.md).

| Pasta | Conteúdo |
|---|---|
| `src/` | `main.py` (consulta), `ingestao/`, `recuperacao/`, `geracao/` e `agentes/` |
| `dados/fontes/texto/` | Os 25 documentos-fonte em texto, com a [auditoria](dados/fontes/texto/AUDITORIA.md) |
| `dados/catalogo.csv` | Catálogo das fontes (IDs F, N e R) |
| `dados/chunks.jsonl` | Trechos gerados, lidos pelo `scripts/gerar_site.py` |
| `dados/vetorial/` | Banco Chroma local (fora do Git) |
| `tests/` | Verificações manuais (`teste_*.py`) |

Todos os comandos abaixo são executados **a partir da raiz do repositório**, com o
ambiente instalado conforme o [README da raiz](../README.md#instalação).

## Como funciona

```text
25 documentos previamente extraídos e limpos
    → leitura do texto e dos metadados
    → divisão em 599 chunks
    → embeddings E5 dos trechos
    → persistência no Chroma

Pergunta do usuário
    → embedding da pergunta com o mesmo E5
    → recuperação dos 5 chunks mais próximos por cosseno
    → exibição do ranking e das fontes
    → síntese pelo gemma4:12b com citações
```

1. **Chunking:** textos corridos são divididos em até 800 caracteres, com sobreposição alvo de 120 e cortes preferenciais por frase ou palavra. Cadastros são agrupados por registros inteiros até 1.000 caracteres, com cabeçalho repetido e sem sobreposição.
2. **Embeddings:** `intfloat/multilingual-e5-base`, via `sentence-transformers`, produz vetores normalizados de 768 dimensões. Os textos indexados recebem `passage: ` e as perguntas recebem `query: `.
3. **Banco vetorial:** o Chroma guarda IDs, embeddings, textos originais e metadados na coleção `pontoativo_fontes`, usando distância de cosseno.
4. **Recuperação:** a consulta retorna os `k` chunks mais próximos; o padrão é 5. A similaridade apresentada é `1 - distância de cosseno`.
5. **Resposta e fontes:** o sistema reproduz até três trechos, com ID, título, URL, publicação, coleta, validação e ressalvas. O JSON exportado conserva todos os resultados recuperados e a resposta integral.

**Similaridade não é probabilidade de acerto.** O sistema ainda não detecta automaticamente quando as evidências são insuficientes: essa avaliação depende de revisão humana.

## Preparar o banco vetorial do protótipo

Se `prototipo/dados/vetorial/` já estiver preenchido e atualizado, siga diretamente para a consulta. O banco local não é versionado: depois de clonar o repositório, normalmente será necessário gerá-lo.

```bash
.venv/bin/python prototipo/src/ingestao/carga.py
```

A carga lê os textos de `prototipo/dados/fontes/texto/`, faz o chunking, gera os embeddings e grava o banco em `prototipo/dados/vetorial/`, em lotes de 256. A configuração atual produz 25 fontes e 599 chunks.

**Executar a carga recria a coleção e substitui os dados anteriores.** Refaça essa etapa quando alterar as fontes, o chunking ou o modelo. A carga usa textos já extraídos e limpos; não baixa páginas nem reextrai PDFs.

## Fazer uma consulta

Instale o Ollama e abra o aplicativo (ou inicie o serviço com `ollama serve`). Na primeira configuração, baixe o modelo com `ollama pull gemma4:12b`. O comando de consulta chama esse modelo automaticamente.

```bash
.venv/bin/python prototipo/src/main.py "A academia pública do Parque da Cidade é gratuita e como utilizar?" -k 5
```

A saída mostra:

- a pergunta submetida;
- os chunks recuperados, ordenados por similaridade;
- o documento de origem, URL, data de coleta e um recorte de cada resultado;
- a resposta do Gemma com referências aos chunks.

Para outra pergunta, basta substituir o texto entre aspas. `-k` controla quantos chunks enviar ao Gemma.

```bash
.venv/bin/python prototipo/src/main.py "Quais modalidades esportivas são oferecidas pelos Centros Olímpicos e Paralímpicos do DF?" -k 5
```

### Salvar a demonstração e suas evidências

```bash
.venv/bin/python prototipo/src/main.py "A academia pública do Parque da Cidade é gratuita e como utilizar?" -k 5 --json consulta-demo.json
```

Esse comando grava `consulta-demo.json` na raiz, com pergunta, ranking, IDs, textos integrais, metadados, distâncias, scores de similaridade e resposta. O arquivo pode ser usado para conferir a fundamentação e a rastreabilidade sem executar a consulta novamente.

O caminho de saída deve apontar para uma pasta que já exista. O comando acima não precisa da pasta temporária de entrega nem do LEIA-ME.

### Mostrar somente a recuperação

```bash
.venv/bin/python prototipo/src/recuperacao/buscar.py "Onde praticar natação?" -k 5
```

### Usar o modelo já baixado sem acesso ao Hub

Depois de uma primeira execução com download concluído:

```bash
export HF_HUB_OFFLINE=1
.venv/bin/python prototipo/src/main.py "Qual é o endereço do Estádio Bezerrão no Gama?" -k 5
```

Para permitir acesso ao Hub novamente na mesma sessão do Terminal:

```bash
unset HF_HUB_OFFLINE
```

No Windows (PowerShell), use `$env:HF_HUB_OFFLINE = "1"` para ativar e `Remove-Item Env:HF_HUB_OFFLINE -ErrorAction SilentlyContinue` para desativar. O modo offline exige que o modelo já esteja no cache e que o banco tenha sido gerado.

## Conferir o funcionamento

```bash
.venv/bin/python prototipo/tests/teste_chunking.py
.venv/bin/python prototipo/tests/teste_banco.py
.venv/bin/python prototipo/tests/teste_embeddings.py
.venv/bin/python prototipo/tests/teste_resposta.py
.venv/bin/python tests/test_registros_rag.py
```

| Teste | O que verifica |
|---|---|
| `teste_chunking.py` | IDs únicos, limites de tamanho, metadados e preservação de textos e registros |
| `teste_banco.py` | Carga, persistência, cosseno, ordenação e filtro por fonte, usando vetores sintéticos em banco temporário |
| `teste_embeddings.py` | Recuperação com E5 real em cinco exemplos pequenos |
| `tests/test_registros_rag.py` | Persistência das rodadas e registro de métricas com chamadas simuladas |
| `teste_resposta.py` | Preservação dos trechos, IDs, fontes, datas, ressalvas e limite da resposta |

O teste de embeddings carrega o modelo E5 real e pode baixá-lo na primeira execução. Os demais testes não precisam desse download; o teste de banco usa um diretório temporário e não substitui o banco do projeto.

O teste de banco não mede qualidade semântica. Os exemplos de embeddings também não representam uma avaliação geral de precisão do sistema.

## Limites atuais

- Não há confirmação de disponibilidade, vagas, horários ou acessibilidade em tempo real.
- As fontes incluem documentos antigos e camadas cadastrais obsoletas, identificados nas ressalvas.
- O E5 aceita até 512 tokens. Na medição dos 599 textos indexados, dois chegaram a ultrapassar esse limite, com máximo de 520. Seus embeddings são truncados; o texto original permanece integral no banco.
- A resposta exibe evidências candidatas. Trechos semelhantes podem não responder à pergunta, mesmo com score alto.
- A proposta mais ampla de encontrar parceiros e comparar espaços permanece como evolução futura.
