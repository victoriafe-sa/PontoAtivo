# PontoAtivo RAG

[![Testes](https://github.com/PedroAlvimm/PontoAtivo/actions/workflows/ci.yml/badge.svg)](https://github.com/PedroAlvimm/PontoAtivo/actions/workflows/ci.yml)

Protótipo acadêmico de recuperação aumentada por geração (RAG) para consultar
fontes verificáveis sobre atividade física e espaços esportivos no Distrito
Federal. A implementação está sendo construída em etapas; funcionalidades
planejadas não são apresentadas como concluídas.

## Estado atual

O protótipo já possui o fluxo principal executável: catálogo e coleta de fontes,
extração de PDF/HTML/Markdown, normalização, chunking hierárquico, embeddings,
persistência no ChromaDB, recuperação com filtros, geração fundamentada via
Ollama, abstenção quando não há evidência suficiente e avaliação reproduzível.
As suítes automatizadas cobrem os módulos locais; a geração textual ainda
depende de um Ollama disponível e a fidelidade das respostas geradas requer
revisão humana.

## Por que Python 3.11?

O computador também possui Python 3.14, mas bibliotecas de aprendizado de
máquina e bancos vetoriais nem sempre oferecem suporte imediato a versões tão
recentes. Python 3.11 é estável e amplamente compatível com PyTorch, Sentence
Transformers e ChromaDB.

## Preparação no Windows com PowerShell

Execute os comandos a partir da raiz do repositório (a pasta `PontoAtivo`, que
contém `pyproject.toml`):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pontoativo_rag.diagnostico
python -m pytest
```

Se o PowerShell bloquear a ativação, execute uma vez na mesma janela:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Preparação no macOS ou Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pontoativo_rag.diagnostico
python -m pytest
```

O ambiente virtual isola as bibliotecas deste projeto das demais instalações
do computador. `requirements.txt` instala o pacote em modo editável: alterações
em `src/` ficam disponíveis sem reinstalação.

## Configuração

Copie `.env.example` para `.env` somente se precisar alterar algum padrão. O
arquivo `.env` é ignorado pelo Git para impedir o versionamento de credenciais.
Embora o protótipo local não precise de chave de API, essa regra preserva uma
troca segura de provedor no futuro.

## Executar o pipeline

Depois de preparar o ambiente, sincronize a base vetorial:

```bash
python -m pontoativo_rag.coleta
python -m pontoativo_rag.ingestao
python -m pontoativo_rag.consulta --pergunta "Onde há atividades para pessoas com deficiência?" --sem-geracao
```

Para executar as perguntas de avaliação sem depender do Ollama:

```bash
python -m pontoativo_rag.avaliacao --sem-geracao --verificar-qualidade
```

Para comparar o mesmo modelo respondendo com e sem a base (precisa do Ollama):

```bash
python -m pontoativo_rag.comparacao
```

Ela roda as 18 perguntas de avaliação e mais 2 de
`dados/perguntas_comparacao_extras.jsonl`, sem RAG (com instrução simples e
com instrução cautelosa) e com RAG, e grava as respostas lado a lado em
`evidencias/`. A análise da última rodada está em
[`evidencias/relatorio_comparacao_sem_rag.md`](evidencias/relatorio_comparacao_sem_rag.md).

O relatório é salvo em `evidencias/` com as fontes recuperadas, distâncias,
abstenções e citações. Não trate distância vetorial como probabilidade de
acerto; a fidelidade da resposta deve ser revisada contra os documentos.

Relatórios temporários com data no nome e arquivos intermediários de ingestão
são reproduzíveis e ficam ignorados pelo Git. Depois que uma execução passar
no portão e for revisada, copie somente o relatório aprovado para
`evidencias/avaliacao_atual.md`. As fontes originais e o catálogo permanecem
versionáveis para preservar a auditoria.

Com `--verificar-qualidade`, o comando retorna código de erro quando ocorrer
uma regressão abaixo dos limites atuais: Recall@k de 0,90, acerto de pelo
menos uma fonte de 0,95, zero falsas abstenções e zero citações inválidas.
O portão também exige cobertura de citações e suporte factual mínimos e não
permite afirmações sem suporte. O sistema nunca acrescenta citações depois da
resposta do modelo: uma resposta parcialmente sem fontes é regenerada e, se o
problema persistir, a avaliação falha de forma visível.

A métrica de suporte factual exige pelo menos dois termos substantivos
coincidentes entre a afirmação e o texto citado, além de ignorar termos
genéricos de metadados. Uma única palavra compartilhada não é considerada
prova de suporte.

O modelo padrão é `gemma4:26b`, que nos testes locais seguiu o contrato de
citação com mais consistência que `llama3.2:3b`. Ele exige mais memória e é mais
lento.

Em computadores com pouca memória de GPU, use `gemma4:12b` (8 GB) no `.env`. O
`gemma4:26b` (18 GB) não cabe nos cerca de 16 GB de GPU de um Mac M4 de 24 GB e
roda em grande parte na CPU. Nesse Mac, em 12/11/2026, o `gemma4:12b` passou no
portão completo com cobertura de citações de 1,00 (contra 0,50 do `llama3.2:3b`),
levando em média 70 s por resposta. Veja `evidencias/relatorio_fase4_qualidade.md`.

Os modelos com raciocínio (gemma4, qwen3) rodam com `"think": false`; sem isso, o
raciocínio consome o limite de saída e a resposta volta vazia.

### Um modelo para o mapa e outro para as dúvidas

A barra do mapa só classifica a pergunta (mapa, documentos, dúvidas, fora do
escopo ou esclarecer), uma tarefa curta que um modelo menor faz mais rápido. As
respostas com documentos continuam com `PONTOATIVO_OLLAMA_MODEL`. Para separar:

```
PONTOATIVO_OLLAMA_MODEL=gemma4:12b        # respostas com documentos (aba Dúvidas)
PONTOATIVO_OLLAMA_MODEL_MAPA=<modelo>     # só a barra do mapa; vazio = o mesmo de cima
```

Para escolher o modelo do mapa, compare os candidatos no computador da
demonstração com as 22 perguntas de `dados/perguntas_rotas.jsonl`:

```
python -m pontoativo_rag.rotas --modelos gemma4:12b <outro-modelo>
```

O comando mostra acertos e tempo médio por modelo e salva o relatório em
`evidencias/rotas_<data>.md`. Use o modelo menor só se ele acertar tantas rotas
quanto o atual. Os dois modelos ficam carregados juntos no Ollama, então a soma
dos tamanhos precisa caber na memória de GPU.

É possível escolher outro modelo por `PONTOATIVO_OLLAMA_MODEL`, mas uma
troca só deve ser aceita depois de executar novamente o portão completo. Se o
modelo não produzir uma resposta integralmente citada após as tentativas de
revisão, o sistema falha fechado e mostra apenas os trechos recuperados.

Por padrão, a geração usa resposta estruturada: o Ollama recebe um esquema JSON
em que cada frase precisa listar pelo menos uma fonte, e só são aceitos os
identificadores presentes no contexto (`F1`, `F2`...). O texto final com as
citações é montado a partir dessas escolhas do próprio modelo. Nenhuma fonte é
associada por semelhança de palavras. Isso torna o contrato de citação
verificável também em modelos menores, como `llama3.2:3b`. A métrica de suporte
factual continua valendo: citar a fonte errada ainda reprova a avaliação. Use
`PONTOATIVO_RESPOSTA_ESTRUTURADA=0` para voltar ao texto livre e comparar.

Ajustes de tempo, todos em `.env.example`:

- `PONTOATIVO_OLLAMA_NUM_PREDICT` (padrão 400) limita o tamanho da resposta;
- `PONTOATIVO_OLLAMA_NUM_CTX` (padrão 8192) define o contexto. Reduza só se os
  trechos enviados couberem, pois o Ollama descarta silenciosamente o excesso;
- `PONTOATIVO_OLLAMA_KEEP_ALIVE` (padrão `10m`) mantém o modelo carregado entre
  perguntas;
- `PONTOATIVO_TENTATIVAS_GERACAO` (padrão 3) é o total de chamadas por pergunta,
  incluindo revisões.

O relatório da avaliação registra as tentativas por pergunta, a média de
tentativas e o tempo total de geração, para mostrar onde o tempo é gasto.

Páginas PDF sem texto são separadas no relatório entre candidatas a OCR
(sem texto nem imagem identificável) e páginas gráficas (por exemplo, capa ou
contracapa). Páginas gráficas não são indexadas, mas continuam preservadas no
arquivo original.

Cada fonte também recebe uma classificação temporal derivada da data de
publicação e do tipo de informação: `atual`, `em_revisao`, `antiga` ou
`desconhecida`. Informações voláteis (horários, vagas, turmas e funcionamento)
usam uma janela de revisão menor que leis e normas. Essa classificação é um
alerta de atualidade, não substitui a verificação humana.

O catálogo também é avaliado separadamente por autoridade, atualidade e
completude. Esses atributos não são equivalentes: uma fonte oficial pode estar
antiga ou não conter todos os campos necessários para responder a uma pergunta.

A recuperação oferece filtros explícitos por região, tipo de documento, fonte e
atualidade. O chunking preserva listas, identifica estruturas tabulares simples
e registra uma `entity_key` derivada da seção mais específica, mantendo o local
ou entidade associado ao trecho. O reranking pode ser comparado com
`--reranker hibrido` (padrão) e `--reranker vetorial`.

## Abrir o chat no mapa

Após instalar as dependências, execute a ingestão para preparar o índice e
inicie o servidor na raiz do projeto. O Ollama deve estar em execução com
o modelo configurado em `PONTOATIVO_OLLAMA_MODEL`.

```powershell
python -m pontoativo_rag.ingestao
python -m pontoativo_rag.web
```

Abra http://127.0.0.1:8766/. Use `--porta 8767` se a porta padrão estiver
ocupada. Se você tiver apenas o modelo `llama3.2:3b` instalado, execute
`$env:PONTOATIVO_OLLAMA_MODEL = 'llama3.2:3b'` antes de iniciar o servidor. O servidor interpreta a pergunta completa no Ollama. Pedidos de
localização consultam o mapa. Perguntas sobre documentos usam o RAG e exibem
as fontes encontradas.

## Testes automáticos

Cada pull request e cada envio para a `main` rodam o workflow
[`.github/workflows/ci.yml`](.github/workflows/ci.yml) no GitHub Actions:

- `pytest` com os testes do RAG, do chat, da moderação e dos encontros;
- os testes da curadoria em `PontoAtivo-CURADORIA/ferramentas/tests`;
- a sintaxe de `app.js`, `encontros.js` e `data/locais.js`;
- a conferência de que `data/locais-encontros.json` está em dia com
  `data/locais.js`.

O CI não usa o Ollama nem baixa o modelo de embeddings. A geração completa
continua sendo verificada localmente com `python -m pontoativo_rag.avaliacao`.

Para rodar os testes da curadoria no Windows, ative o modo UTF-8 do Python,
porque alguns arquivos são abertos sem codificação explícita:

```powershell
cd PontoAtivo-CURADORIA; $env:PYTHONUTF8 = '1'; python -B -m unittest discover -s ferramentas/tests
```

## Diagnóstico

```bash
python -m pontoativo_rag.diagnostico
```

O comando cria os diretórios operacionais e informa separadamente:

- versão do Python;
- diretórios de fontes, dados, banco vetorial, documentação e evidências;
- presença das dependências;
- disponibilidade do serviço e do modelo configurado no Ollama.

Uma pendência do Ollama não impede as futuras etapas de ingestão e recuperação;
ela apenas impedirá a geração textual até que o serviço e o modelo estejam
disponíveis.

## Documentação de engenharia

- [Projeto técnico](docs/superpowers/specs/2026-11-05-pontoativo-rag-design.md)
- [Plano de implementação](docs/superpowers/plans/2026-11-05-pontoativo-rag.md)

## Encontros esportivos

A etapa **Encontros** está disponível no mapa servido por `python -m pontoativo_rag.web`.
É possível criar conta com usuário, senha e apelido, publicar encontros em dupla,
trio ou grupo, filtrar encontros futuros e acompanhar **Minha agenda**. A faixa
etária é autodeclarada e começa em 18 anos. Dupla tem duas vagas totais, trio tem
três, e grupo aceita de quatro a vinte pessoas, incluindo quem organiza.

O horário do formulário e dos cartões é o de Brasília. Participar ocupa uma vaga,
sair libera a vaga e cancelar preserva o encontro na agenda dos participantes.
Uma nova tentativa da mesma publicação usa uma identificação própria para evitar
duplicação após falha de conexão.

As contas, sessões e inscrições persistem em `dados/encontros.sqlite3`, fora da pasta
pública e ignorado pelo Git. A senha usa scrypt com salt e a sessão usa cookie
HttpOnly. Para escolher outro banco local, configure `PONTOATIVO_ENCONTROS_DB`.
O catálogo da agenda deriva dos mesmos locais do mapa. Ao alterar essa base, rode
`node PontoAtivo-CURADORIA/ferramentas/exportar-locais-encontros.mjs`.

No mapa, os locais com encontros futuros ganham um pino destacado com o número
de encontros e ficam fora dos agrupamentos. O balão do pino lista os próximos
encontros com o botão **Participar**, e **Ver local no mapa**, nos cartões da
agenda, abre esse balão. `encontros.js` publica os encontros para o mapa pelo
evento `pa:encontros`, e `app.js` atualiza só os pinos que mudaram.

Para uma demonstração pronta, com o servidor aberto, rode
`python -m pontoativo_rag.persona_demo --porta 8766`. O script cria a persona
**Jeferson** (usuário `jeferson.corrida`, atleta amador de corrida, 25–34 anos,
preferências Corrida e Gama) e marca uma corrida em grupo de seis pessoas às 18h
no PEC do Setor Leste EQ 4/6, no Gama, a cerca de 2 km da UnB Gama. Se as 18h de
hoje já passaram, a corrida fica para amanhã. A senha é gerada na primeira vez e
fica só em `dados/persona_jeferson.txt`, ignorado pelo Git; rodar de novo
reaproveita a conta e não duplica a corrida do dia. Depois, crie outra conta
e clique em **Participar** para fazer o papel de um parceiro de corrida.

Para entrar sem cadastro, abra o site no próprio computador do servidor
(`http://127.0.0.1:8766` ou `http://localhost:8766`) e clique em **Entrar como
admin**, na seção Encontros. A conta `admin` (apelido "Admin") é criada na primeira
vez, não tem senha e não aceita login por senha nem cadastro com esse nome. O botão
não aparece, e a rota `/api/sessao/admin` responde 403, para quem acessa de outro
aparelho, com `PONTOATIVO_PUBLIC_ORIGIN` ou `PONTOATIVO_PROXY_CONFIAVEL` definidos,
ou com cabeçalhos de proxy (`X-Forwarded-For`, `Forwarded`).

Para testar o compartilhamento local, use dois navegadores com contas distintas.
Crie uma dupla no primeiro e participe pelo segundo. A vaga restante deve zerar.
Saia no segundo, confira a liberação e volte a entrar. Cancele no primeiro e
confira o cancelamento na agenda do segundo. Os testes automatizados também
verificam disputa simultânea pela última vaga, sessão expirada, origem de
requisições, filtros, horário de Brasília e repetição de publicação.

O servidor fornecido escuta em 127.0.0.1, para uso neste computador. A validação
com pessoas em redes distintas depende de uma implantação compartilhada HTTPS
com armazenamento persistente. Nessa implantação, configure
`PONTOATIVO_PUBLIC_ORIGIN` com a origem HTTPS para validar requisições e emitir
cookies Secure. Se o servidor ficar atrás de um proxy HTTPS no mesmo computador,
configure também `PONTOATIVO_PROXY_CONFIAVEL=1` e faça o proxy sobrescrever o
cabeçalho `X-Forwarded-For` com o IP de quem acessa. Sem isso, todas as pessoas
chegam com o IP do proxy, e cinco senhas erradas para uma conta bloqueariam o
acesso de todo mundo a ela por 15 minutos. Não ative essa opção sem o proxy:
qualquer pessoa poderia escolher o próprio IP e escapar do limite de tentativas.
Essa validação externa continua pendente.

O servidor publica apenas os arquivos do site (`index.html`, `styles.css`,
`app.js`, `encontros.js`, `assets/` e `data/`). Ferramentas, documentos internos,
pastas ocultas e listagens de pasta respondem 404.
