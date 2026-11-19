# Registro da verificação — 19/11/2026

## Demonstração real concluída

Execução registrada às 10:16:54, horário de São Paulo, usando o índice local, embeddings `intfloat/multilingual-e5-base` e Ollama `gemma4:12b`. Não foram usadas respostas simuladas.

| Medida | Resultado |
|---|---|
| Pergunta | Quais são as faltas graves nos Centros Olímpicos? |
| Modo final | `rag` |
| Trechos entregues à Análise | 4 |
| Tentativas de geração | 1 |
| Recuperação | Aproximadamente 3,99 s |
| Análise/geração | 77,74 s |
| Validação | Formato e passagens aprovados |
| Referência citada | DOC-003, Manual de Uso dos Centros Olímpicos e Paralímpicos, p. 4, seção 7.3 |

Evidências: [mensagens e saída estruturada](evidencias/demo.json) e [saída legível do terminal](evidencias/demo.txt).

O registro mostra a ação entregue à Pesquisa, os quatro trechos entregues à Análise, o prompt e o resultado real do modelo. A conclusão lista condutas e limites de faltas que correspondem aos itens 7.3.1 a 7.3.7 do trecho recuperado. É uma síntese, não transcrição integral: não reproduz o item 7.3.8 nem a penalidade de desligamento que também aparecem no trecho. Na apresentação, não descrevê-la como reprodução exaustiva do manual.

A intenção deste exemplo foi `intencao_nao_identificada`, pois as regras da Interpretação não incluem “faltas graves”. Isso não interrompe a colaboração: a pergunta original foi preservada e a Pesquisa encontrou a seção relevante. O campo de intenção não modifica a busca atual.

## Ambiente e testes

O diagnóstico confirmou Python 3.13.18, dependências instaladas, diretórios presentes e serviço Ollama ativo com o modelo configurado. A recuperação real confirmou que o índice e o embedding em cache estavam utilizáveis.

A suíte específica dos agentes passou: **26 testes e 8 subtestes**, em 0,38 s. Ela usa substitutos controlados para busca/modelo e não substitui a demonstração real acima.

A suíte geral sem testes marcados como `integration` passou: **322 testes e 10 subtestes**, em 21,71 s. O resultado está em [testes.txt](evidencias/testes.txt). Essa suíte também contém testes HTTP locais e testes com componentes simulados.

Na primeira execução restrita ao sandbox, o acesso ao Ollama e a abertura de portas pelos testes HTTP foram bloqueados com `Operation not permitted`. A demonstração foi repetida com acesso local permitido e concluiu em modo `rag`; a suíte geral foi repetida nas mesmas condições de permissão. O bloqueio inicial era do ambiente de execução, não evidência de ausência dos agentes.

## Escopo do que está comprovado

- Implementação e encadeamento dos três papéis especializados.
- Uso de contratos de dados e transferência de fontes entre Pesquisa e Análise.
- Execução de uma pergunta real até uma resposta com citação válida.
- Existência de tratamento para ausência de evidência, saída inválida e indisponibilidade, coberto pelos testes específicos.

Não foi feita uma avaliação estatística da qualidade semântica do coordenador, nem uma gravação de vídeo ou demonstração pelo navegador. A execução comprovada foi pelo script que usa o coordenador real compartilhado com a aplicação web. Nenhum artefato foi enviado ao Teams.
