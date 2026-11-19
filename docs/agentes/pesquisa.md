# Agente de Pesquisa

**Responsável:** Pedro · **Código:** [`src/pontoativo_rag/agentes/pesquisa.py`](../../src/pontoativo_rag/agentes/pesquisa.py)
· **Testes:** [`tests/pontoativo_rag/agentes/test_pesquisa.py`](../../tests/pontoativo_rag/agentes/test_pesquisa.py)

## Responsabilidade

Receber uma **ação** (o que o usuário quer saber, já identificado pelo agente de
Interpretação) e devolver os **trechos das fontes oficiais** que servem de
evidência, cada um com a sua origem. O agente não escreve resposta: só busca,
filtra e entrega o material para a Análise e a Validação.

```text
Interpretação ──ação──▶ Pesquisa ──trechos + fontes──▶ Análise ──rascunho──▶ Validação
                                   └───────────trechos + fontes─────────────▶ Validação
```

## Como decide o que entregar

1. Busca na base do assistente (25 fontes, embeddings multilingual-E5 no Chroma,
   busca híbrida com as palavras da consulta), pegando os 4 trechos mais próximos.
2. Mantém só os que passam na **mesma regra de evidência do gerador**
   (`geracao.trecho_relevante`): distância cosseno até 0,12 ou, perto disso,
   trechos com muitas palavras da consulta ou da mesma região.
3. Se nenhum passar, responde `sem_evidencia` e explica o motivo. Assim os outros
   agentes sabem que não devem afirmar nada, em vez de receber trechos fracos.

## Mensagens

**Entrada (ação):**

```json
{
  "pergunta_original": "O que pode fazer um aluno ser desligado do Centro Olímpico?",
  "tipo": "buscar_regra",
  "consulta": "faltas graves que levam ao desligamento do aluno nos Centros Olímpicos e Paralímpicos",
  "regiao": "Ceilândia"
}
```

Só `consulta` é obrigatória. `regiao` filtra pela região administrativa; os
outros campos são repassados sem mudança.

**Saída:**

```json
{
  "agente": "pesquisa",
  "acao": { "...": "a ação recebida" },
  "status": "encontrado",
  "trechos": [
    {
      "id": "T1",
      "texto": "7.3 Falta Grave ...",
      "distancia": 0.1235,
      "fonte": {
        "id": "DOC-003",
        "titulo": "Manual de Uso dos Centros Olimpicos e Paralimpicos",
        "instituicao": "Secretaria de Estado de Esporte e Lazer do Distrito Federal",
        "url": "https://www.esporte.df.gov.br/documents/d/esporte/manual-de-uso-do-cop",
        "paginas": "4",
        "secao": "7. Do descumprimento do Termo de Compromisso ...",
        "regiao": "",
        "atualidade": "..."
      }
    }
  ],
  "limiar": 0.12,
  "descartados": 3,
  "segundos": 8.2
}
```

Quando não há evidência: `"status": "sem_evidencia"`, `"trechos": []` e um
`"motivo"` com a melhor distância encontrada. Os IDs `T1`, `T2`… são os que a
Análise deve citar e a Validação deve conferir.

## Como rodar

Com o índice pronto (`python -m pontoativo_rag.ingestao`), na raiz do repositório:

```bash
.venv/bin/python -m pontoativo_rag.agentes.pesquisa "faltas graves nos Centros Olímpicos"
.venv/bin/python -m pontoativo_rag.agentes.pesquisa --acao docs/agentes/exemplos/acao_faltas_graves.json --saida resultado.json
```

Em Python, para conectar aos outros agentes:

```python
from pontoativo_rag.agentes.pesquisa import criar_agente

pesquisa = criar_agente()
resultado = pesquisa.executar({"consulta": "faltas graves nos Centros Olímpicos"})
```

## Exemplos com dados reais (17/11)

| Ação | Resultado |
|---|---|
| [Faltas graves nos COPs](exemplos/acao_faltas_graves.json) | [encontrado](exemplos/pesquisa_faltas_graves.json): 1 trecho do Manual de Uso dos COPs (DOC-003, p. 4, item 7.3 Falta Grave); 3 trechos descartados |
| [Previsão do tempo](exemplos/acao_sem_resultado.json) | [sem evidência](exemplos/pesquisa_sem_resultado.json): melhor distância 0,172, acima do limiar 0,12 |

## Integração com a Análise

O terminal e o chat documental usam o mesmo coordenador. O [agente de
Interpretação](interpretacao.md) prepara a ação. A Pesquisa seleciona
evidências e repassa fonte, entidade, identificador do trecho e avisos à Análise.
O coordenador mantém as referências de exibição no formato `[F1]`, `[F2]` e
mostra os trechos em modo diagnóstico quando a geração falha. Sem evidência,
a consulta termina antes de chamar o modelo.

Os testes dos agentes ficam em `tests/pontoativo_rag/agentes/`.
Os [JSONs de rodadas anteriores](../../experimentos/agentes/) são registros
históricos e podem conter o formato de saída do protótipo.

## Comparar a qualidade dos fluxos

Use o mesmo índice, modelo e arquivo de perguntas nas duas rodadas:

```bash
.venv/bin/python -m pontoativo_rag.avaliacao --fluxo anterior --rotulo referencia
.venv/bin/python -m pontoativo_rag.avaliacao --fluxo agentes --rotulo agentes
```

A avaliação registra tempos de recuperação e geração, tentativas e fontes.
Revise as respostas por entidade e por condição da pergunta. A presença de
uma citação válida não comprova que ela sustenta a conclusão.

## Limites de execução e validação (19/11/2026)

O coordenador compartilha `PONTOATIVO_OLLAMA_TIMEOUT` entre a busca e as
até duas tentativas de análise. Antes de cada chamada, verifica o orçamento
restante e o repassa ao cliente HTTP sem alterar o cliente compartilhado.
O timeout HTTP limita inatividade de rede: não é um cancelamento rígido da
consulta inteira, não interrompe a busca e não garante que o Ollama pare uma
inferência já iniciada.

A validação local rejeita campos inesperados e referências duplicadas, além
de verificar IDs e passagens literais. Esses controles não comprovam suporte
semântico nem atribuição correta de entidade; a avaliação humana continua
necessária. Os testes com modelo simulado verificam o contrato e o fluxo,
não a qualidade de um modelo real.

A suíte padrão passou em Python 3.13.18: 322 testes e 10 subtestes. Os testes
HTTP precisam de permissão para abrir portas de loopback. O ambiente `.venv`
foi preparado com dependências do `pyproject.toml`; o interpretador gerenciado
está em `/private/tmp/pontoativo-python` e deve ser reinstalado ou substituído
por uma instalação persistente caso essa pasta temporária seja removida.

### Verificação com índice real

A ingestão local de 19/11/2026 carregou 25 documentos sem erro, gerando 528
chunks e 1.431 vetores. A avaliação sem geração usou 18 perguntas e `top_k=4`.
Tanto o fluxo anterior quanto o integrado obtiveram recall médio de 0,94,
acerto de ao menos uma fonte de 1,00, cinco abstenções corretas e nenhuma
falsa abstenção. Isso verifica preservação da recuperação neste conjunto,
sem certificar qualidade da geração nem melhoria de latência.

Registros locais: `experimentos/avaliacao-rag/avaliacao_20261119_095701_integracao_20261119.md`
e `experimentos/avaliacao-rag/avaliacao_20261119_095731_referencia_integracao_20261119.md`.

A consulta real sobre idade mínima nos COPs respondeu quatro anos, com
referências `[F3]` e `[F4]`, incluindo o edital DOC-002. Recuperação: 4,49 s;
geração com `gemma4:12b`: 117,1 s. Saída preservada em
[consulta-integrada-20261119.txt](../../experimentos/agentes/consulta-integrada-20261119.txt).
É uma verificação de ponta a ponta, não um benchmark: uma observação não
estima p95, estabilidade, ganho sobre o gerador anterior ou qualidade geral.
A calibração de tokens, contexto e concorrência e a comparação completa com
geração permanecem pendentes.
