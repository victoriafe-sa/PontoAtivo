# PontoAtivo

Plataforma esportiva inclusiva para o Distrito Federal. Projeto do **Challenge 2 (CBL), Big Idea "Qualidade de Vida"**.

> **Status:** Semana 2, construção da base de conhecimento e do primeiro protótipo de RAG (recuperação aumentada por geração). Ainda não há interface, entrevistas concluídas nem resultados medidos com usuários.

## O que é o projeto

Praticar esporte nem sempre depende só de vontade. Muitas vezes é preciso achar pessoas com horários parecidos, descobrir quais espaços existem, saber quanto custam e se atendem a quem tem deficiência.

O PontoAtivo investiga se uma plataforma com apoio de inteligência artificial pode ajudar moradores do DF a:

- encontrar **parceiros** para praticar uma modalidade;
- encontrar **espaços esportivos** (públicos e privados) adequados;
- consultar **informações de acessibilidade** confiáveis, com fonte e data de verificação.

A acessibilidade orienta a busca e a forma como os resultados são mostrados, e não é só um filtro extra. A IA entra como apoio à decisão, nunca como substituta de informação verificada.

### Pergunta central (Essential Question)

> Como uma solução baseada em inteligência artificial pode apoiar moradores do Distrito Federal na escolha de parceiros e espaços para a prática inclusiva de atividades físicas, considerando interesses, horários, localização, custos, acessibilidade e informações confiáveis?

### Princípios do projeto

- Nenhum espaço é marcado como acessível sem verificação.
- Toda informação sobre locais tem **fonte** e **data de verificação**.
- Quando faltarem dados, o sistema deve dizer isso em vez de inventar.
- Coleta mínima de dados pessoais (LGPD).

## Foco da Semana 2: base de conhecimento + RAG

Nesta etapa o foco é a **qualidade da recuperação de informação**, a **fundamentação das respostas** e a **rastreabilidade das fontes**. A interface e a experiência do usuário ficam para depois.

### Como o sistema funciona

```
Documentos-fonte (dados/fontes/)
        │
        ▼
   Ingestão ──► limpeza ──► chunking ──► embeddings ──► banco vetorial
                                                              │
Consulta do usuário ──► embedding da consulta ──► busca dos chunks mais relevantes
                                                              │
                                                              ▼
                                  Resposta fundamentada nos chunks + fontes citadas
```

1. **Ingestão:** os documentos-fonte são lidos, limpos e divididos em trechos (chunks).
2. **Embeddings:** cada chunk é convertido em vetor e guardado no banco vetorial.
3. **Recuperação:** a consulta também vira vetor, e o sistema busca os chunks mais próximos.
4. **Geração:** a resposta é escrita com base apenas no que foi recuperado, citando as fontes. Se não houver dados suficientes, o sistema diz isso.

### Checklist da entrega

- [ ] Base de conhecimento curada, com no mínimo 20 documentos-fonte
- [ ] Descrição da estratégia de chunking
- [ ] Descrição da estratégia de embeddings
- [ ] Banco vetorial implementado
- [ ] Demonstração: consulta, chunks recuperados, resposta fundamentada e fontes usadas
- [ ] Diagrama de arquitetura
- [ ] Pipeline de ingestão de dados

**Prazo:** segunda-feira, 09/11, às 8h. A entrega é feita na pasta da equipe no Teams (canal *Segundo Desafio*), e não pelo GitHub.

## Como o repositório está organizado

```
pontoativo/
├── README.md
├── docs/
│   ├── semana-01/                  # definição do problema e plano de pesquisa
│   └── semana-02/
│       ├── arquitetura.md
│       ├── pipeline-ingestao.md
│       ├── estrategia-chunking.md
│       ├── estrategia-embeddings.md
│       └── demonstracao.md
├── dados/
│   ├── catalogo.csv                # lista de todas as fontes
│   ├── fontes/                     # documentos-fonte (mín. 20)
│   └── vetorial/                   # banco vetorial gerado (fora do git)
├── src/
│   ├── ingestao/                   # leitura, limpeza, chunking, embeddings, carga
│   ├── recuperacao/                # busca dos chunks mais relevantes
│   ├── geracao/                    # resposta fundamentada com citação de fontes
│   └── main.py                     # ponto de entrada
├── tests/
│   └── consultas-demo.md           # consultas de teste e resultados esperados
├── pesquisa/                       # roteiros e síntese das entrevistas (anonimizada)
└── .gitignore
```

| Pasta | O que vai aqui |
|---|---|
| `docs/semana-01/` | Documento da Semana 1: problema, partes interessadas, hipóteses, riscos e métricas |
| `docs/semana-02/` | Documentação do RAG: arquitetura, pipeline, chunking, embeddings e demonstração |
| `dados/fontes/` | Os documentos que alimentam a base de conhecimento |
| `dados/catalogo.csv` | Uma linha por fonte: id, título, origem, link, data de acesso, tipo e observações |
| `dados/vetorial/` | Banco vetorial local. É gerado pela ingestão e não é versionado |
| `src/` | Código do pipeline: ingestão, recuperação e geração |
| `tests/` | Consultas de teste usadas na demonstração |
| `pesquisa/` | Roteiros de entrevista, modelo de termo de consentimento e síntese anonimizada |

> **Privacidade:** não versionar nomes, contatos, áudios ou termos assinados dos participantes. Esses materiais ficam fora do git, em local privado da equipe.

## Como rodar

> A stack ainda será definida pela equipe e registrada em `docs/semana-02/arquitetura.md`.

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd pontoativo

# 2. Configurar variáveis de ambiente
cp .env.example .env      # preencher chaves de API, se necessário

# 3. Instalar dependências
# (comando a definir conforme a stack)

# 4. Rodar a ingestão para gerar o banco vetorial
# (comando a definir)

# 5. Fazer uma consulta
# (comando a definir, ex.: python src/main.py "pergunta")
```

## Roadmap

| Etapa | Foco | Situação |
|---|---|---|
| Semana 1 | Problema, partes interessadas, riscos, métricas e plano de pesquisa | Concluída |
| Semana 2 | Base de conhecimento e primeiro mecanismo de RAG | Em andamento |
| Semanas seguintes | Protótipo de consulta e comparação com os meios atuais de busca | A fazer |

Ideias como reservas, pagamento compartilhado, gamificação e eventos comerciais ficam como **possibilidades futuras** e não fazem parte do compromisso atual.

## Como contribuir

1. Crie uma branch a partir da `main` (`docs/...`, `dados/...`, `feat/...`).
2. Use commits curtos com prefixo: `docs:`, `pesquisa:`, `dados:`, `feat:`, `fix:`.
3. Toda fonte nova entra no `dados/catalogo.csv`, com origem, link e data de acesso.
4. Abra um Pull Request e peça revisão de outro integrante.

## Equipe

- Victoria Ferreira
- Pedro Alvim
- Cibelly Lourenço 
- Marcos Bittar 
- Rebeca Vitória