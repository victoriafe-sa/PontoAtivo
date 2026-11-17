# PontoAtivo

Protótipo de recuperação de informações sobre espaços esportivos e prática inclusiva de atividades físicas no Distrito Federal. Projeto do **Challenge 2 (CBL), Big Idea "Qualidade de Vida"**.

Este README é o guia atual de funcionamento e execução do projeto. Todos os comandos abaixo devem ser executados a partir da raiz do repositório, onde estão `src/`, `dados/` e `requirements.txt`.

## Abrir no navegador

Na raiz, com as dependências instaladas, execute `.venv/bin/python -m pontoativo_rag.web` e abra o [mapa com chat e encontros](http://127.0.0.1:8766/). As instruções para preparar o índice e o modelo estão no [guia RAG](docs/guia-rag.md).

Para ver a apresentação e os resultados dos experimentos, execute `python3 -m http.server 8000 --bind 127.0.0.1 --directory docs` e abra a [página de resultados](http://127.0.0.1:8000/).

## Estado atual

O projeto possui uma base selecionada e limpa com **25 documentos-fonte**, divididos em **599 chunks**, embeddings multilíngues E5 e banco vetorial Chroma. A consulta funciona pela linha de comando.

O Gemma 4 12B gera uma resposta local pelo Ollama usando os trechos recuperados, com citações das fontes.

As informações das fontes permanecem pendentes de validação humana quanto à situação atual dos locais. Um documento que menciona acessibilidade ou funcionamento não comprova essas condições hoje.

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

## Requisitos e instalação

A verificação original foi feita com **Python 3.13 no Windows**. Para executar no **macOS (Terminal com zsh ou bash)**, use as instruções abaixo. As dependências estão em [requirements.txt](requirements.txt): PyTorch, sentence-transformers e Chroma.

### macOS

Na raiz do repositório:

```bash
python3.11 --version
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

O pacote aceita Python 3.11 a 3.13. A integração contínua usa a versão 3.11 indicada em `.python-version`.

No macOS, o executável fica em `.venv/bin/python`. O caminho `.venv/Scripts/python.exe` pertence ao Windows. Use `-m pip`, e não `-m pip3`: esse é o nome do módulo, independentemente do sistema operacional.

O `requirements.txt` já inclui `torch`, portanto não é necessário instalá-lo separadamente. No Mac, use o índice padrão do pip, conforme a [documentação do PyTorch](https://pytorch.org/get-started/locally/); o índice `https://download.pytorch.org/whl/cpu` do exemplo Windows não é necessário.

Não é necessário ativar o ambiente virtual: todos os comandos de execução abaixo chamam diretamente o Python de `.venv`. Execute cada etapa somente se a anterior terminar sem erros. Se aparecer `No matching distribution found`, confira qual dependência falhou e sua compatibilidade com a versão do Python e a arquitetura do Mac antes de recriar o ambiente.

### Windows (PowerShell)

```powershell
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

Os exemplos seguintes são para **macOS**. No Windows, substitua `.venv/bin/python` por `.venv/Scripts/python.exe`; as variáveis do modo offline têm comandos próprios, indicados naquela seção.

Não são necessárias chaves de API. A instalação das bibliotecas e o primeiro uso do E5 exigem internet. O modelo ocupa aproximadamente **1,1 GB**, é baixado automaticamente e reutilizado do cache nas próximas execuções.

## Preparar o banco vetorial

Se `dados/vetorial/` já estiver preenchido e atualizado, siga diretamente para a consulta. O banco local não é versionado: depois de clonar o repositório, normalmente será necessário gerá-lo.

```bash
.venv/bin/python src/ingestao/carga.py
```

A carga lê os textos de `dados/fontes/texto/`, faz o chunking, gera os embeddings e grava o banco em `dados/vetorial/`, em lotes de 256. A configuração atual produz 25 fontes e 599 chunks.

**Executar a carga recria a coleção e substitui os dados anteriores.** Refaça essa etapa quando alterar as fontes, o chunking ou o modelo. A carga usa textos já extraídos e limpos; não baixa páginas nem reextrai PDFs.

## Fazer uma consulta

Instale o Ollama e abra o aplicativo (ou inicie o serviço com `ollama serve`). Na primeira configuração, baixe o modelo com `ollama pull gemma4:12b`. O comando de consulta chama esse modelo automaticamente.

```bash
.venv/bin/python src/main.py "A academia pública do Parque da Cidade é gratuita e como utilizar?" -k 5
```

A saída mostra:

- a pergunta submetida;
- os chunks recuperados, ordenados por similaridade;
- o documento de origem, URL, data de coleta e um recorte de cada resultado;
- a resposta do Gemma com referências aos chunks.

Para outra pergunta, basta substituir o texto entre aspas. `-k` controla quantos chunks enviar ao Gemma.

```bash
.venv/bin/python src/main.py "Quais modalidades esportivas são oferecidas pelos Centros Olímpicos e Paralímpicos do DF?" -k 5
```

### Salvar a demonstração e suas evidências

```bash
.venv/bin/python src/main.py "A academia pública do Parque da Cidade é gratuita e como utilizar?" -k 5 --json consulta-demo.json
```

Esse comando grava `consulta-demo.json` na raiz, com pergunta, ranking, IDs, textos integrais, metadados, distâncias, scores de similaridade e resposta. O arquivo pode ser usado para conferir a fundamentação e a rastreabilidade sem executar a consulta novamente.

O caminho de saída deve apontar para uma pasta que já exista. O comando acima não precisa da pasta temporária de entrega nem do LEIA-ME.

### Mostrar somente a recuperação

```bash
.venv/bin/python src/recuperacao/buscar.py "Onde praticar natação?" -k 5
```

### Usar o modelo já baixado sem acesso ao Hub

Depois de uma primeira execução com download concluído:

```bash
export HF_HUB_OFFLINE=1
.venv/bin/python src/main.py "Qual é o endereço do Estádio Bezerrão no Gama?" -k 5
```

Para permitir acesso ao Hub novamente na mesma sessão do Terminal:

```bash
unset HF_HUB_OFFLINE
```

No Windows (PowerShell), use `$env:HF_HUB_OFFLINE = "1"` para ativar e `Remove-Item Env:HF_HUB_OFFLINE -ErrorAction SilentlyContinue` para desativar. O modo offline exige que o modelo já esteja no cache e que o banco tenha sido gerado.

## Conferir o funcionamento

```bash
.venv/bin/python tests/pipeline/teste_chunking.py
.venv/bin/python tests/pipeline/teste_banco.py
.venv/bin/python tests/pipeline/teste_embeddings.py
.venv/bin/python tests/pipeline/teste_resposta.py
.venv/bin/python tests/pipeline/test_registros_rag.py
```

| Teste | O que verifica |
|---|---|
| `teste_chunking.py` | IDs únicos, limites de tamanho, metadados e preservação de textos e registros |
| `teste_banco.py` | Carga, persistência, cosseno, ordenação e filtro por fonte, usando vetores sintéticos em banco temporário |
| `teste_embeddings.py` | Recuperação com E5 real em cinco exemplos pequenos |
| `test_registros_rag.py` | Persistência das rodadas e registro de métricas com chamadas simuladas |
| `teste_resposta.py` | Preservação dos trechos, IDs, fontes, datas, ressalvas e limite da resposta |

O teste de embeddings carrega o modelo E5 real e pode baixá-lo na primeira execução. Os demais testes não precisam desse download; o teste de banco usa um diretório temporário e não substitui o banco do projeto.

O teste de banco não mede qualidade semântica. Os exemplos de embeddings também não representam uma avaliação geral de precisão do sistema.

## Estrutura do repositório

Execute ambos os fluxos a partir da raiz.

| Fluxo | Código | Entradas e saídas |
|---|---|---|
| Consulta e site | `src/main.py`, `src/ingestao/`, `src/recuperacao/`, `src/geracao/` | Usa `dados/catalogo.csv`, os textos em `dados/fontes/texto/` e o índice `dados/vetorial/`. O site lê `dados/chunks.jsonl`. |
| Chat e mapa | `src/pontoativo_rag/` e [curadoria](curadoria/) | Usa `dados/catalogo_fontes.csv` e [fontes originais](dados/fontes_originais/). Gera chunks e índice próprios em `dados/rag/`. Veja o [guia de execução](docs/guia-rag.md). |

A [coleta da SEDUH](dados/seduh/) conserva os dados geográficos e sua origem. Os [documentos de engenharia](docs/engenharia/) descrevem o pacote RAG. Em `tests/pipeline/` ficam as verificações do fluxo de consulta, incluindo os scripts manuais `teste_*.py`. A suíte do pacote fica em `tests/pontoativo_rag/`.

## Documentação e fontes

- [Índice dos experimentos e resultados](experimentos/README.md).
- [Catálogo das fontes](dados/catalogo.csv).
- [Histórico de curadoria e limitações das fontes](dados/fontes/texto/AUDITORIA.md).
- [Arquitetura](docs/semana-02/arquitetura.md).
- [Pipeline de ingestão](docs/semana-02/pipeline-ingestao.md).
- [Estratégia de chunking](docs/semana-02/estrategia-chunking.md).
- [Estratégia de embeddings](docs/semana-02/estrategia-embeddings.md).
- [Demonstração documentada anteriormente](docs/semana-02/demonstracao.md).

### Site (GitHub Pages)

A página do projeto fica em [docs/index.html](docs/index.html) e lê os dados de `docs/dados.json`. Depois de alterar fontes, chunks, perguntas, respostas ou análises dos experimentos, regenere os dados (só biblioteca padrão):

```bash
python3 scripts/gerar_site.py
```

Para ver localmente: `python3 -m http.server -d docs` e acesse http://localhost:8000. Para publicar, ative em **Settings → Pages → Deploy from a branch → `main` / `/docs`**.

Esses documentos preservam o histórico de desenvolvimento e podem mencionar materiais temporários de entrega removidos. Para executar o código atual, utilize os comandos deste README.

## Limites atuais

- Não há confirmação de disponibilidade, vagas, horários ou acessibilidade em tempo real.
- As fontes incluem documentos antigos e camadas cadastrais obsoletas, identificados nas ressalvas.
- O E5 aceita até 512 tokens. Na medição dos 599 textos indexados, dois chegaram a ultrapassar esse limite, com máximo de 520. Seus embeddings são truncados; o texto original permanece integral no banco.
- A resposta exibe evidências candidatas. Trechos semelhantes podem não responder à pergunta, mesmo com score alto.
- A proposta mais ampla de encontrar parceiros e comparar espaços permanece como evolução futura.

## Como contribuir

1. Registre novas fontes em `dados/catalogo.csv`, com origem, URL e data de coleta.
2. Preserve os metadados e as ressalvas nos cabeçalhos dos textos-fonte.
3. Refaça a ingestão e confira as consultas após alterações que afetem o índice.
4. Abra um Pull Request para revisão pela equipe.

Não versione nomes, contatos, áudios ou termos assinados de participantes de pesquisa. Mantenha esses materiais fora do repositório.

## Equipe

- Victoria Ferreira
- Pedro Alvim
- Cibelly Lourenço
- Marcos Bittar
- Rebeca Vitória
