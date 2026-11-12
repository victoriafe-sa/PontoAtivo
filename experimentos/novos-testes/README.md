# Testes 1, 2 e 3 — piloto controlado com e sem RAG

Este pacote é independente dos experimentos anteriores. Usa cópias integrais de trechos e metadados locais, sem consultar a situação atual dos equipamentos. O cenário tem data fixa de **12/11/2026**.

## Piloto executado

Rodada `20261112-092351-979787`: **66 respostas completas**, 33 no Llama e 33 no Qwen, uma repetição por condição. Gemini não executado. A [análise qualitativa](analise-piloto.md) compara os três testes. A [verificação de execução](rodadas/20261112-092351-979787/verificacao.md) confirma completude; `avaliacao.csv` nessa rodada contém 66 linhas para avaliação humana, com campos de julgamento ainda em branco. Nenhuma nota automática de qualidade foi atribuída.

## Desenho

São 12 perguntas e 33 chamadas por modelo/repetição:

| Teste | Perguntas | Condições | Chamadas |
|---|---:|---|---:|
| 1 — entidade errada | 6 (3 pares) | Sem RAG; RAG curto | 12 |
| 2 — resposta parcial | 3 | Sem RAG; RAG curto | 6 |
| 3 — contexto com ruído e posição | 3 | Sem RAG; RAG curto; ruído com alvo no início/meio/fim | 15 |

Llama e Qwen totalizam 66 respostas. Gemini acrescenta 33. Este é um piloto menor que a proposta inicial de seis casos em cada teste. Algumas perguntas são compartilhadas entre testes 1 e 3; não são observações independentes e não devem ser somadas para sustentar significância estatística.

**RAG controlado:** as evidências foram selecionadas manualmente a partir dos resultados históricos. Não há nova recuperação automática. O estudo mede uso, atribuição e posição das evidências na geração; não mede recall do buscador nem o desempenho do pipeline completo. O contexto curto é um controle, não uma estimativa do comportamento do RAG em produção.

### Teste 1: entidade errada

Cada par recebe o mesmo trecho, trocando a entidade na pergunta:

- Idade: COPs versus Semear; evidência dos COPs.
- Modalidades: COPs versus Escola Paralímpica; evidência dos COPs.
- Gratuidade e acesso: academia pública do Parque da Cidade versus academia particular do Lago Sul; evidência da academia pública.

O lado `a` possui suporte; o lado `b` não tem suporte específico no contexto. Não basta citar: a fonte precisa tratar da entidade correta. O caso da academia particular também exige reconhecer que nenhum estabelecimento foi identificado. A formulação dos pares preserva o sentido, com adaptações gramaticais.

### Teste 2: resposta parcial

- Endereço e capacidade do Bezerrão versus disponibilidade para reserva.
- Gratuidade e agendamento da academia pública versus horário livre.
- Idade e inclusão de PcD nos COPs versus vaga específica no Gama.

O modelo deve aproveitar o que está documentado e reconhecer a lacuna operacional. Ausência de evidência não significa ausência de vaga.

### Teste 3: ruído e posição

Três perguntas factuais (endereço, uso da academia e idade nos COPs). O alvo é idêntico em todas as condições com RAG. As condições com ruído têm os mesmos quatro distratores, na mesma ordem relativa; somente a posição do alvo muda. Todos os trechos e metadados são integrais. Não se deve atribuir causalmente ao tamanho do contexto o que também pode decorrer do conteúdo dos distratores; curto versus ruído altera ambos. Início/meio/fim controla esse conteúdo e tamanho.

## Organização

- `renumeracao.json`: registro da migração dos identificadores e dos hashes anteriores dos snapshots; conteúdo das chamadas preservado.
- `preparar.py`: gera os casos e snapshots de evidências dos arquivos históricos.
- `executar.py`: executa o piloto, com registros independentes por chamada.
- `resumir.py`: confere completude da rodada e cria `avaliacao.csv` em branco para avaliação humana, sem substituir uma avaliação existente.
- `verificar.py`: valida isolamento do gabarito e invariantes experimentais, sem API.
- `tarefas.json`: pergunta, condição e IDs de contexto de cada chamada.
- `evidencias.json`: textos e metadados congelados; sem scores de busca que poderiam sugerir ranking experimental.
- `gabarito.json`: fatos esperados e limites, **nunca enviado ao modelo**.
- `rodadas/<data-hora>/`: snapshots, ambiente, métricas e respostas integrais por modelo.
- `analise-piloto.md`: leitura qualitativa da rodada, quando disponível.

## Execução

Na raiz do projeto:

```bash
python3 experimentos/novos-testes/verificar.py
python3 experimentos/novos-testes/executar.py --simular
python3 experimentos/novos-testes/executar.py --modelos llama qwen
```

Para selecionar um teste ou ampliar repetições:

```bash
python3 experimentos/novos-testes/executar.py --modelos llama --testes 3 --repeticoes 3
```

Gemini requer a dependência `google-genai`. Copie somente a chave da API para a área de transferência do Mac e execute:

```bash
.venv/bin/python experimentos/novos-testes/executar.py --modelos gemini --chave-area-transferencia
```

Não é necessário regenerar os casos para executar. `preparar.py` atualiza os três arquivos de configuração do pacote; as rodadas preservam seus próprios snapshots e hashes. Os registros anteriores nunca são sobrescritos. Em falha, o executor salva o erro e interrompe o lote; não há retomada automática, e nova execução cria outra rodada.

As chamadas são sequenciais para evitar disputa entre os dois modelos desta execução. Não há garantia de ausência de outros processos locais. A ordem de condições é embaralhada com seed fixa e idêntica entre modelos dentro de cada repetição. Cada chamada começa sem histórico. Temperatura 0, seed de geração 42, contexto Ollama 8.192 e saída máxima 4.096; Qwen sem raciocínio. Repetições mantêm a seed de geração e não equivalem a amostras independentes; servem para observar estabilidade e latência. Gemini usa temperatura 0 e saída máxima 4.096, sem garantia de equivalência de amostragem com Ollama.

## Rubrica antes de avaliar

Avaliar por pergunta e condição, preservando os erros e as ressalvas no texto. Não usar correspondência de palavras como julgamento automático de acerto.

| Dimensão | Registro |
|---|---|
| Fatos esperados cobertos | Quantidade de itens do gabarito atendidos / total aplicável; verificar todos os componentes de cada item |
| Atribuição errada | Sim/não: fato transferido para outra entidade |
| Afirmação sem suporte | Sim/não, com transcrição da afirmação e justificativa |
| Limite reconhecido | Sim/parcial/não, para cada limite do gabarito |
| Recusa indevida | Sim/não: rejeita informação explicitamente disponível |
| Citação fiel (só RAG) | Sim/parcial/não/não aplicável: ID existente que sustenta a afirmação e a entidade |
| Temporalidade | Correta/parcial/incorreta/não aplicável |
| Formato | Até 200 palavras; estrutura solicitada; registrar separadamente da qualidade |

A ausência de suporte no snapshot não prova falsidade no mundo. Para **sem RAG**, classificar fatos adicionais como `não verificáveis neste conjunto` se não houver referência; não penalizar automaticamente a ausência de IDs que nunca foram fornecidos. O gabarito é documental e não uma pesquisa exaustiva sobre Semear, Escola Paralímpica ou academias privadas. Nos controles RAG, usar informação de fora dos trechos contraria a instrução mesmo que possa ser verdadeira.

Comparar condições dentro do mesmo modelo: teste 1, transferência de entidade nos três casos `b`, junto do aproveitamento nos três `a`; teste 2, cobertura dos fatos junto do reconhecimento de limites; teste 3, acerto e recusa por posição, comparados ao contexto curto e sem RAG. Não criar nota geral que esconda essas diferenças. Para uma avaliação formal, usar dois avaliadores independentes, ocultando modelo quando possível, e registrar divergências.

Tokens e tempos são retornados pelas APIs quando disponíveis. O tempo local inclui carga; Gemini mede também rede. Não interpretar ausências como zero, não comparar velocidade local e remota diretamente e não presumir ausência de truncamento. Conferir `motivo_fim` e contagens antes de interpretar respostas incompletas. A primeira chamada pode carregar o modelo; reportar custo de carga separadamente.

Após concluir uma rodada:

```bash
python3 experimentos/novos-testes/resumir.py NOME-DA-RODADA
```
