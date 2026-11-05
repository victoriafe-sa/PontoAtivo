# PontoAtivo

Plataforma esportiva inclusiva para o Distrito Federal. Projeto do **Challenge 2 (CBL), Big Idea "Qualidade de Vida"**.

> **Status:** Semana 1 (definição do problema e plano de pesquisa). Ainda não há protótipo, base de dados completa, entrevistas concluídas nem resultados medidos.

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

## Como o repositório está organizado

```
pontoativo/
├── README.md
├── docs/       # definições do projeto e entregas de cada semana
├── pesquisa/   # roteiros de entrevista e síntese das evidências
├── dados/      # fontes e cadastro de espaços esportivos
├── src/        # código (a partir da Semana 2)
└── .gitignore
```

| Pasta | O que vai aqui |
|---|---|
| `docs/` | Documento da Semana 1 e das semanas seguintes; problema, hipóteses, requisitos, riscos e métricas |
| `pesquisa/` | Roteiros (praticantes e gestores), modelo de termo de consentimento e síntese das entrevistas **já anonimizada** |
| `dados/` | Lista de fontes e responsáveis, e o cadastro de espaços. Cada registro precisa de `fonte` e `data_verificacao` |
| `src/` | Base de conhecimento, mecanismo de recuperação (RAG) e protótipo, a partir da Semana 2 |

> **Privacidade:** não versionar nomes, contatos, áudios ou termos assinados dos participantes. Esses materiais ficam fora do git, em local privado da equipe.

## Roadmap

| Etapa | Foco |
|---|---|
| Semana 1 | Problema, partes interessadas, riscos, métricas e plano de pesquisa |
| Semana 2 | Base de conhecimento e primeiro mecanismo de recuperação (RAG) |
| Semanas seguintes | Protótipo de consulta e comparação com os meios atuais de busca |

Ideias como reservas, pagamento compartilhado, gamificação e eventos comerciais ficam como **possibilidades futuras** e não fazem parte do compromisso atual.

## Como contribuir

1. Crie uma branch a partir da `main` (`docs/...`, `dados/...`, `feat/...`).
2. Use commits curtos com prefixo: `docs:`, `pesquisa:`, `dados:`, `feat:`, `fix:`.
3. Abra um Pull Request e peça revisão de outro integrante.

## Equipe

- Victoria Ferreira
- Pedro Alvim
- Cibelly Lourenço 
- Marcos Bittar 
- Rebeca Vitória