# Agentes do PontoAtivo

O fluxo documental tem três agentes especializados, encadeados pelo coordenador
(`FluxoDocumental`). A visão geral da entrega — arquitetura, responsabilidades,
fluxo e limites — está em [docs/entregas/semana-04](../entregas/semana-04/README.md),
com o [diagrama da arquitetura](../entregas/semana-04/arquitetura-agentes.png).

| Agente | O que faz | Documentação | Código |
|---|---|---|---|
| 1 · Interpretação | Classifica a intenção da pergunta e monta a ação de busca | [interpretacao.md](interpretacao.md) | [interpretacao.py](../../src/pontoativo_rag/agentes/interpretacao.py) |
| 2 · Pesquisa | Busca nas fontes e entrega só os trechos que servem de evidência | [pesquisa.md](pesquisa.md) | [pesquisa.py](../../src/pontoativo_rag/agentes/pesquisa.py) |
| 3 · Análise | Monta as conclusões com passagens literais e valida as citações | [entrega da semana 4](../entregas/semana-04/README.md#responsabilidades-e-contratos) | [analise.py](../../src/pontoativo_rag/agentes/analise.py) |

Contratos das mensagens: [contratos.py](../../src/pontoativo_rag/agentes/contratos.py).
Coordenador: [coordenador.py](../../src/pontoativo_rag/agentes/coordenador.py).
Testes: [`tests/pontoativo_rag/agentes/`](../../tests/pontoativo_rag/agentes/).
Execuções registradas: [`experimentos/agentes/`](../../experimentos/agentes/).
