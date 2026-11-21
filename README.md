# PontoAtivo

Mapa esportivo e inclusivo do Distrito Federal com um assistente que responde
perguntas a partir de fontes oficiais (RAG). Projeto do **Challenge 2 (CBL),
Big Idea "Qualidade de Vida"**.

- **Mapa:** 3.898 locais (PECs, quadras, campos, parques, 798 parquinhos, Centros Olímpicos e
  espaços comunitários), com filtros e informações de acessibilidade.
- **Assistente:** busca em 25 documentos oficiais com embeddings
  multilingual-E5 no Chroma e responde com o Gemma 4 pelo Ollama, citando as
  fontes e dizendo "não sei" quando elas não bastam.
- **Encontros:** contas, preferências e agenda para marcar atividades e
  encontrar parceiros.

As informações das fontes não confirmam vagas, horários ou acessibilidade em
tempo real.

## Onde está cada coisa

| Pasta | O que tem |
|---|---|
| [`src/pontoativo_rag/`](src/pontoativo_rag/) | **Sistema principal:** RAG, servidor web, chat, contas e encontros |
| [`site/`](site/) | O mapa web (HTML, JavaScript, estilos e a base `data/locais.js`) |
| [`curadoria/`](curadoria/) | Ferramentas e dados que montam e validam a base de locais do mapa |
| [`dados/rag/`](dados/rag/) | Fontes do assistente, [catálogo](dados/rag/catalogo.csv) e perguntas de avaliação |
| [`dados/mapa/seduh/`](dados/mapa/seduh/) | Cadastro geográfico da SEDUH usado no mapa |
| [`tests/`](tests/) | Testes automáticos do sistema principal e dos scripts de experimentos |
| [`docs/agentes/`](docs/agentes/) | Documentação de cada agente (interpretação, pesquisa, análise e validação) e dos contratos entre eles |
| [`docs/rag/`](docs/rag/) | Documentação do assistente: [como rodar](docs/rag/como-rodar.md), pipeline, chunking, embeddings e fontes |
| [`docs/entregas/`](docs/entregas/) | Entregas das semanas 1 e 2 e [sistema multiagentes — 20/11](docs/entregas/semana-04/README.md) (arquitetura, auditoria e demonstração) |
| [`docs/index.html`](docs/index.html) | Site de resultados dos experimentos (GitHub Pages) |
| [`experimentos/`](experimentos/) | Experimentos com e sem RAG, piloto e [avaliação do assistente](experimentos/avaliacao-rag/) |
| [`scripts/`](scripts/) | Rodar os experimentos e gerar o site de resultados |
| [`prototipo/`](prototipo/) | Primeira versão do RAG (semanas 1 e 2), usada nos experimentos |

## Instalação

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

## Abrir o mapa com o assistente

Com o [Ollama](https://ollama.com) aberto e o modelo baixado (`ollama pull gemma4:12b`):

```bash
cp .env.example .env
.venv/bin/python -m pontoativo_rag.ingestao
.venv/bin/python -m pontoativo_rag.web
```

Depois abra http://127.0.0.1:8766/. A primeira ingestão baixa o modelo E5 e
monta o índice em `dados/rag/vetorial/`. Detalhes, avaliação e opções em
[docs/rag/como-rodar.md](docs/rag/como-rodar.md).

## Serviços externos do mapa

O servidor consulta três serviços públicos, com cache, e o site fala só com o
servidor. A chave do openrouteservice fica no servidor, e os pontos consultados
precisam estar no DF.

| Serviço | Para quê | Chave |
|---|---|---|
| [Open-Meteo](https://open-meteo.com/) | Previsão do tempo, índice UV e qualidade do ar na hora de cada encontro (até 15 dias antes) | Não precisa |
| [BrasilAPI](https://brasilapi.com.br/) | Aviso de feriado nacional nos encontros; o feriado distrital de 30/11 é somado pelo PontoAtivo | Não precisa |
| [openrouteservice](https://openrouteservice.org/) | Rota a pé e para cadeira de rodas a partir da localização da pessoa, nos balões do mapa | Gratuita, em `PONTOATIVO_ORS_API_KEY` |

A localização da pessoa só é usada para a rota, depois que ela permite, e vai
para o servidor no corpo da requisição, não na URL.

## Testes

```bash
.venv/bin/python -m pytest -q -m "not integration"
cd curadoria && ../.venv/bin/python -B -m unittest discover -s ferramentas/tests
```

A suíte padrão inclui os [testes dos agentes](tests/pontoativo_rag/agentes/),
os [testes automatizados do protótipo](tests/prototipo/) e os
[testes dos registros de experimentos](tests/experimentos/). A CI também
executa a suíte da curadoria e confere o JavaScript do mapa.

O [portão de qualidade](experimentos/avaliacao-rag/) usa o gerador anterior
como referência histórica. Os testes do coordenador usam um modelo simulado.
A comparação entre os dois fluxos precisa de uma avaliação com Ollama e o índice local.

## Site de resultados (GitHub Pages)

A página do projeto fica em [docs/index.html](docs/index.html) e lê os dados de `docs/dados.json`. Depois de alterar fontes, chunks, perguntas, respostas ou análises dos experimentos, regenere os dados (só biblioteca padrão):

```bash
python3 scripts/gerar_site.py
```

Para ver localmente: `python3 -m http.server -d docs` e acesse http://localhost:8000. Para publicar, ative em **Settings → Pages → Deploy from a branch → `main` / `/docs`**.


## Como contribuir

1. Novas fontes do assistente entram em `dados/rag/fontes/` e no
   [catálogo](dados/rag/catalogo.csv), com origem, URL e data de coleta.
2. Depois de mudar fontes, chunking ou modelo, rode a ingestão de novo e o
   portão de qualidade antes de abrir o Pull Request.
3. Abra um Pull Request para revisão pela equipe.

Não versione nomes, contatos, áudios ou termos assinados de participantes de
pesquisa. Mantenha esses materiais fora do repositório.

## Equipe

- Victoria Ferreira
- Pedro Alvim
- Cibelly Lourenço
- Marcos Bittar
- Rebeca Vitória
