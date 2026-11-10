# Rodar perguntas em lote

Os prompts q5.txt a q20.txt estão em `prompts/`. Usam as mesmas instruções dos testes iniciais e os cinco resultados completos dos respectivos JSONs em `evidencias/`, sem incluir resposta extrativa ou gabarito. Q1–Q4 foram preservados. As limitações de cobertura documental identificadas nas novas perguntas continuam válidas; gerar o prompt não corrige o gabarito do conjunto.

Execute da raiz do projeto, com o Ollama aberto e os modelos baixados:

```bash
python3 scripts/rodar_experimentos_rag.py --modelo qwen --inicio 5 --fim 9
python3 scripts/rodar_experimentos_rag.py --modelo llama --inicio 5 --fim 9
```

Troque os intervalos por 10–14 e 15–20, ou use 5–20 para todas as novas perguntas. Execute um modelo de cada vez. Cada pergunta gera uma chamada independente, sem histórico de outras perguntas. Não é necessário colar todos os prompts em uma conversa.

As respostas são salvas em `respostas-qwen/rodada-DATA-HORA/` ou `respostas-llama/rodada-DATA-HORA/`. Cada pasta contém respostas qN.txt, registros qN.json com entrada completa, saída e métricas disponíveis e ambiente.json com coleta do servidor local. Rodadas anteriores não são sobrescritas. Na primeira falha, o lote para; corrija a causa e reinicie pelo número que falhou. Uma interrupção manual não deve ser tratada como resposta completa.

Configurações explícitas desta rodada local: num_ctx=8192, temperature=0, seed=42, num_predict=4096; Qwen com think=false. O limite de geração é em tokens; a instrução do prompt continua sendo até 200 palavras. Isso não comprova as configurações dos testes antigos. Contagens e motivo de término não comprovam ausência de truncamento da entrada. Duração local inclui componentes de execução distintos da API remota e não mede recuperação, pois as evidências já estão congeladas.

## Gemini

Para uso manual no AI Studio, abra cada qN.txt e envie separadamente em conversa nova. Para lote automatizado, é necessário acesso à Gemini API; a assinatura do aplicativo não substitui esse acesso. Confira previamente a faixa gratuita e as cotas do modelo na sua conta.

Instale a dependência opcional no ambiente do projeto:

```bash
.venv/bin/python -m pip install google-genai
```

No Terminal do Mac com zsh, leia a chave sem mostrá-la nem gravá-la no histórico:

```bash
read -s 'GEMINI_API_KEY?Cole sua chave Gemini: '
export GEMINI_API_KEY
```

Execute:

```bash
.venv/bin/python scripts/rodar_experimentos_rag.py --modelo gemini --inicio 5 --fim 9
```

O script solicita `gemini-3.5-flash-lite`, temperature=0 e max_output_tokens=4096, sem habilitar ferramentas externas nem histórico entre perguntas. O nível de raciocínio não é explicitamente configurado; a saída completa disponível é preservada. As respostas e os registros vão para `respostas-gemini/rodada-DATA-HORA/`. O script não habilita faturamento nem verifica sua cota gratuita; executar chamadas está sujeito às condições do projeto de API usado. Não substitui automaticamente o modelo se ele estiver indisponível. Não compartilhe nem versione a chave.

Ao terminar:

```bash
unset GEMINI_API_KEY
```

## Simular antes

```bash
python3 scripts/rodar_experimentos_rag.py --modelo qwen --inicio 5 --fim 20 --simular
```

A simulação confere a leitura dos prompts sem chamar serviços nem criar respostas.

Documentação dos provedores: https://docs.ollama.com/api/chat e https://googleapis.github.io/python-genai/.
