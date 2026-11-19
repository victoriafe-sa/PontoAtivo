# Agente de Validação

**Código:** [`src/pontoativo_rag/agentes/validacao.py`](../../src/pontoativo_rag/agentes/validacao.py)
· **Testes:** [`tests/pontoativo_rag/agentes/test_validacao.py`](../../tests/pontoativo_rag/agentes/test_validacao.py)
· **Demonstração:** [`scripts/demonstrar_validacao.py`](../../scripts/demonstrar_validacao.py)

## Responsabilidade

Comparar o **rascunho da Análise** com os **trechos da Pesquisa** antes de qualquer
publicação. Quando uma afirmação não tem apoio nas fontes, a Validação devolve
à Análise **o trecho do rascunho que precisa de correção**, com o motivo. Se faltar
evidência que uma busca mais específica possa trazer, ela pede à Pesquisa uma
consulta complementar (no máximo uma). O agente não escreve a resposta final.

```text
Interpretação ──ação──▶ Pesquisa ──trechos──▶ Análise ──rascunho──▶ Validação ──aprovado──▶ Comunicação
                           ▲                    ▲                      │
                           │                    └──trechos a corrigir──┤
                           └──────────consulta complementar────────────┘
```

## Como decide

1. **Contrato (sempre):** repete a checagem da Análise. Os IDs precisam existir e
   as passagens citadas precisam ser literais.
2. **Regras (sempre):** em cada item `sustentada` ou `divergencia`, cada frase da
   conclusão é comparada com os trechos citados (e com o título e o órgão da
   fonte). Uma palavra com conteúdo que não aparece nas fontes é tratada como
   afirmação sem apoio. Variações de gênero e número são aceitas ("gratuito" e
   "gratuita", "acessível" e "acessíveis"). Números precisam bater exatamente.
   Itens `lacuna` não passam por essa regra. A regra é conservadora: um sinônimo
   também é apontado, e a Análise corrige usando as palavras da fonte.
3. **Modelo (quando há cliente):** um segundo papel revisa cinco critérios
   (`sustentacao`, `condicoes`, `completude`, `temporalidade`, `lacunas_conflitos`).
   O parecer é conferido em Python: cada problema precisa apontar um item
   existente e copiar literalmente um trecho da conclusão desse item. Um parecer
   inválido tem uma segunda chance; se falhar de novo, **não autoriza publicar**.
   A regra prevalece: o modelo não aprova uma frase que a regra reprovou.

## Mensagens

**Saída (parecer):**

```json
{
  "agente": "validacao",
  "aprovado": false,
  "revisao": "regras",
  "criterios": {"sustentacao": false, "condicoes": true, "completude": true,
                "temporalidade": true, "lacunas_conflitos": true},
  "problemas": [{
    "item": 3,
    "trecho_rascunho": "O trajeto até os banheiros também é acessível para quem usa cadeira de rodas",
    "criterio": "sustentacao",
    "correcao": "Os trechos citados (T1) não mencionam: cadeira, rodas, trajeto. Remova a afirmação ou marque a dúvida como lacuna, dizendo o que a fonte não informa; use as palavras da fonte."
  }],
  "consulta_complementar": ""
}
```

**Para a Análise** (`feedback_para_analise`), cada problema vira uma linha em
`feedback_validacao`, enviada junto com o `rascunho_anterior`:

```text
Item 3 ("O caminho até eles também é acessível?"): o trecho "O trajeto até os banheiros também é acessível para quem usa cadeira de rodas" precisa de correção (sustentacao). Os trechos citados (T1) não mencionam: cadeira, rodas, trajeto. ...
```

## Integração no coordenador

`criar_fluxo_documental` (terminal, web e avaliação) cria a Validação com o mesmo
modelo da Análise. Para desligar, use `validar=False`. Em `FluxoDocumental`:

- `validacao=AgenteValidacao(cliente)` usa regras e modelo; `AgenteValidacao()` usa só regras;
- `max_correcoes` (padrão 1) limita as voltas Validação → Análise;
- `registrar=lista.append` guarda as mensagens entre os agentes; cada parecer inclui os trechos consolidados com os IDs usados na revisão, inclusive após busca complementar.
- `generation_attempts` conta cada chamada à Análise e ao revisor, incluindo as repetições de formato ou parecer inválido.

A Validação divide o orçamento de tempo da consulta com a Análise. Se o rascunho
continuar reprovado depois das correções, ou se o revisor falhar, a resposta cai
em `recuperacao_sem_geracao` e mostra só os trechos. Cada consulta passa a fazer
ao menos uma chamada a mais ao modelo.

## Exemplos preparados à mão

Os dois usam a pergunta da demonstração e o trecho F029-003 (Parque da Cidade, SEL-DF):

| Exemplo | Resultado esperado (testado) |
|---|---|
| [Rascunho correto](exemplos/validacao_rascunho_correto.json): entrada gratuita e banheiros acessíveis confirmados; caminho como lacuna | aprovado |
| [Rascunho com etapa inventada](exemplos/validacao_rascunho_etapa_inventada.json): afirma que o trajeto até os banheiros é acessível | reprovado no item 3, com o trecho a corrigir |

Trecho usado: [`validacao_trechos_f029.json`](exemplos/validacao_trechos_f029.json).

## Demonstração de uma correção (19/11/2026)

```bash
PYTHONPATH=src .venv/bin/python scripts/demonstrar_validacao.py --modelo qwen3:8b --so-regras
```

Pergunta: *"Uso cadeira de rodas e quero visitar o Parque da Cidade Dona Sarah
Kubitschek. Preciso pagar para entrar? Há banheiros acessíveis? O caminho até eles
também é acessível?"*

1. **Interpretação:** separa as três dúvidas.
2. **Pesquisa:** recupera o trecho F029-003 (busca lexical no corpus do protótipo,
   porque o índice vetorial principal não contém a F029).
3. **Análise, 1º rascunho:** é o exemplo com a etapa inventada, injetado de propósito
   para que haja algo a corrigir.
4. **Validação:** reprova o item 3 e devolve à Análise o trecho "O trajeto até os
   banheiros também é acessível para quem usa cadeira de rodas".
5. **Análise, correção** (`qwen3:8b`, real): o item 3 vira lacuna, "A fonte não informa
   se o trajeto até os banheiros é acessível para quem usa cadeira de rodas".
6. **Validação:** aprova.
7. **Comunicação** (provisória no script): junta as conclusões e a fonte F029 · SEL-DF.

Registro completo: [`validacao-parque-da-cidade-20261119.json`](../../experimentos/agentes/validacao-parque-da-cidade-20261119.json)
(resumo em [`.txt`](../../experimentos/agentes/validacao-parque-da-cidade-20261119.txt)).

## Limites observados

- **Revisor semântico com modelos de 8B:** na mesma demonstração, com revisão pelo
  modelo, o `qwen3:8b` e o `llama3.1:8b` reprovaram até uma declaração honesta de
  lacuna. O `llama3.1:8b` também levou a Análise a trocar "é gratuita" por "era
  gratuita em 2026, mas pode ter mudado". Registro:
  [`validacao-parque-da-cidade-revisor-llama-20261119.json`](../../experimentos/agentes/validacao-parque-da-cidade-revisor-llama-20261119.json).
  O modelo do projeto (`gemma4:12b`) não estava instalado nesta máquina; é preciso
  repetir a rodada com ele antes de concluir sobre a revisão semântica.
- A regra só vê palavras: ela não percebe uma afirmação inventada escrita apenas
  com palavras da fonte (por exemplo, trocar um atributo de lugar). Esse caso
  depende do revisor semântico.
- Os testes usam um modelo simulado: verificam o contrato e o fluxo, não a
  qualidade de um modelo real.
