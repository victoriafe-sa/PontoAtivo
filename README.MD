# PontoAtivo

Protótipo de recuperação de informações sobre espaços esportivos e prática inclusiva de atividades físicas no Distrito Federal. Projeto do **Challenge 2 (CBL), Big Idea "Qualidade de Vida"**.

Este README é o guia atual de funcionamento e execução do projeto. Todos os comandos abaixo devem ser executados a partir da raiz do repositório, onde estão `src/`, `dados/` e `requirements.txt`.

## Estado atual

O projeto possui uma base selecionada e limpa com **25 documentos-fonte**, divididos em **599 chunks**, embeddings multilíngues E5 e banco vetorial Chroma. A consulta funciona pela linha de comando.

A resposta automática é **extrativa**: apresenta os próprios trechos recuperados, com identificação das fontes, datas e ressalvas. Ainda não há interface web, geração de sínteses por LLM, agenda em tempo real ou busca de parceiros implementada.

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
    → resposta extrativa com até 3 chunks citados
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
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

Se `.venv/bin/python` já existir e funcionar, pule a criação do ambiente. Neste checkout foi encontrado Python **3.14.6 em Apple Silicon (arm64)**; a instalação completa e a execução do modelo devem ser verificadas com os testes abaixo antes de considerar o ambiente validado.

No macOS, o executável fica em `.venv/bin/python`. O caminho `.venv/Scripts/python.exe` pertence ao Windows. Use `-m pip`, e não `-m pip3`: esse é o nome do módulo, independentemente do sistema operacional.

O `requirements.txt` já inclui `torch`, portanto não é necessário instalá-lo separadamente. No Mac, use o índice padrão do pip, conforme a [documentação do PyTorch](https://pytorch.org/get-started/locally/); o índice `https://download.pytorch.org/whl/cpu` do exemplo Windows não é necessário.

Não é necessário ativar o ambiente virtual: todos os comandos de execução abaixo chamam diretamente o Python de `.venv`. Execute cada etapa somente se a anterior terminar sem erros. Se aparecer `No matching distribution found`, confira qual dependência falhou e sua compatibilidade com a versão do Python e a arquitetura do Mac antes de recriar o ambiente.

### Windows (PowerShell)

```powershell
python -m venv .venv
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

```bash
.venv/bin/python src/main.py "A academia pública do Parque da Cidade é gratuita e como utilizar?" -k 5
```

A saída mostra:

- a pergunta submetida;
- os chunks recuperados, ordenados por similaridade;
- o documento de origem, URL, data de coleta e um recorte de cada resultado;
- a resposta extrativa, com até três chunks completos e suas fontes.

Para outra pergunta, basta substituir o texto entre aspas. `-k` controla quantos chunks recuperar; a resposta continua limitada aos três primeiros.

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
.venv/bin/python tests/teste_chunking.py
.venv/bin/python tests/teste_banco.py
.venv/bin/python tests/teste_embeddings.py
.venv/bin/python tests/teste_resposta.py
```

| Teste | O que verifica |
|---|---|
| `teste_chunking.py` | IDs únicos, limites de tamanho, metadados e preservação de textos e registros |
| `teste_banco.py` | Carga, persistência, cosseno, ordenação e filtro por fonte, usando vetores sintéticos em banco temporário |
| `teste_embeddings.py` | Recuperação com E5 real em cinco exemplos pequenos |
| `teste_resposta.py` | Preservação dos trechos, IDs, fontes, datas, ressalvas e limite da resposta |

O teste de embeddings carrega o modelo E5 real e pode baixá-lo na primeira execução. Os demais testes não precisam desse download; o teste de banco usa um diretório temporário e não substitui o banco do projeto.

O teste de banco não mede qualidade semântica. Os exemplos de embeddings também não representam uma avaliação geral de precisão do sistema.

## Estrutura do repositório

```text
PontoAtivo/
├── README.MD
├── requirements.txt
├── src/
│   ├── ingestao/          # chunking, embeddings, banco e carga
│   ├── recuperacao/       # busca semântica
│   ├── geracao/           # resposta extrativa
│   └── main.py            # consulta e exportação JSON
├── dados/
│   ├── catalogo.csv       # inventário das fontes
│   ├── fontes/texto/      # 25 textos, PDF original e curadoria
│   └── vetorial/          # banco gerado localmente, fora do Git
├── dados_oficiais_seduh/  # coleta original; não é entrada direta da carga
├── docs/
│   ├── semana-01/
│   └── semana-02/
└── tests/
```

A pasta temporária `Semana 2` não faz parte da execução atual e já não está presente neste checkout. Código, fontes e comandos deste README são suficientes para instalar as dependências, gerar o banco e fazer consultas.

## Documentação e fontes

- [Catálogo das fontes](dados/catalogo.csv).
- [Histórico de curadoria e limitações das fontes](dados/fontes/texto/AUDITORIA.md).
- [Arquitetura](docs/semana-02/arquitetura.md).
- [Pipeline de ingestão](docs/semana-02/pipeline-ingestao.md).
- [Estratégia de chunking](docs/semana-02/estrategia-chunking.md).
- [Estratégia de embeddings](docs/semana-02/estrategia-embeddings.md).
- [Demonstração documentada anteriormente](docs/semana-02/demonstracao.md).

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
