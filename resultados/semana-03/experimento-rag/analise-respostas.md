# Análise das respostas — LLM com RAG

Avaliação documental dos 12 arquivos de resposta, confrontados com os quatro JSONs de evidências e os quatro prompts locais. Não houve nova execução dos modelos nem verificação da situação atual dos espaços. A referência desta análise são as evidências fornecidas ao experimento.

## Modelos registrados

- Gemini 3.5 Flash-Lite: `gemini-3.5-flash-lite`, modelo escolhido para o experimento e identificado nos quatro arquivos de resposta.
- Qwen: `qwen3:8b`.
- Llama: `llama3.2:3b`.

Essas identificações são as anotadas nos arquivos, sem logs de API que as confirmem. Os prompts locais contêm as respectivas perguntas e os cinco textos integrais de cada JSON. Isso não comprova que a mesma entrada foi efetivamente enviada ou integralmente processada em cada execução.

## Resultado por pergunta

| Pergunta | Gemini 3.5 Flash-Lite | Qwen3 8B | Llama 3.2 3B |
|---|---|---|---|
| Q1 — gratuidade e uso da academia | Correta e fundamentada | Correta e fundamentada | Recusa indevida: dados explícitos não utilizados |
| Q2 — modalidades dos COPs | Correta, com ressalvas | Parcial: omite quatro modalidades e apresenta URL corrompida | Lista correta; ressalvas temporais e por unidade incompletas |
| Q3 — endereço do Bezerrão | Correta e fundamentada | Endereço correto; ressalva temporal imprecisa | Recusa indevida: endereço explícito não utilizado |
| Q4 — vaga amanhã e acessibilidade verificada | Abstenção adequada e bem justificada | Abstenção adequada; mistura sentidos de vaga e não detalha limite da acessibilidade | Abstenção adequada; menos detalhada e com citações concentradas no final |

## Q1 — academia pública do Parque da Cidade

O trecho N04-008 afirma explicitamente que musculação e aulas são gratuitas e que o uso exige baixar o aplicativo Mude – Yoga e Fitness, concluir o cadastro e agendar horário. Também condiciona o funcionamento à presença de profissional de educação física.

Gemini e Qwen preservam essas informações e apresentam ressalvas temporais. A afirmação do Qwen sobre parceria privada é sustentada nos metadados de N04-002, embora o corpo desse trecho não descreva a parceria.

O Llama afirma que as evidências não informam gratuidade nem uso, contradizendo diretamente N04-008. Trata-se de abstenção indevida, e não de ausência de evidência recuperada. Também não cita IDs junto às afirmações e repete a mesma notícia três vezes nas fontes.

## Q2 — modalidades dos COPs

N03-003 lista atletismo, basquete, futsal, futebol society, ginástica localizada, pilates, vôlei, jiu-jitsu, judô, taekwondo, karatê e capoterapia. A relação é exemplificativa e a oferta varia por unidade.

O Gemini reproduz as 12 modalidades, cita o trecho adequado e preserva o caráter exemplificativo, as diferenças por unidade e o ano da lista. As informações adicionais sobre idade e público estão sustentadas em N02-002 e F028-001. A abertura “dados de setembro de 2025” deve ser entendida como referente à lista: as fontes adicionais também incluem documentos de 2026.

O Qwen registra apenas oito das 12 modalidades, omitindo atletismo, basquete, futsal e futebol society. Não inventa modalidades, mas entrega uma síntese incompleta. O arquivo começa diretamente por “Ginástica Localizada”, sem a abertura “Resposta”; é necessário conferir se a cópia foi cortada antes de atribuir toda a omissão ao modelo. A URL de N02-002 contém dois endereços concatenados e não reproduz o link original. A expressão “já encerrou” deve ficar restrita ao prazo de 2025: N02-002 traz calendário até 11/12/2026, e o arquivo não registra a data de execução. O próprio metadado diz apenas “pode já ter se encerrado”.

O Llama reproduz as 12 modalidades e reconhece que a lista é exemplificativa. Não explicita a variação por unidade nem a impossibilidade de confirmar a oferta atual. Lista os cinco trechos como fontes, mas a lista de modalidades está sustentada especificamente em N03-003; listar todas as fontes não comprova o uso de cada uma.

## Q3 — endereço do Bezerrão

F059-001 contém explicitamente “St. Central – Gama, Brasília – DF, 72405-610” e uma atualização em 20/02/2026.

Gemini e Qwen apresentam o endereço correto com referência ao trecho certo. O Gemini também preserva a data de atualização. O Qwen afirma que não existem detalhes sobre a atualidade, embora o texto informe a data de atualização; essa data não comprova a situação atual do estádio, mas deveria ser reconhecida. A observação sobre capacidade estimada é sustentada, porém dispensável para a pergunta sobre endereço.

O Llama afirma que o endereço não consta das evidências. Isso contradiz F059-001, recuperado na primeira posição. Nos arquivos locais, a falha está no aproveitamento da evidência, sem que seja possível determinar a causa técnica a partir das respostas isoladas.

## Q4 — disponibilidade amanhã e acessibilidade

Nenhum dos cinco trechos informa agenda de quadras ou verificação operacional de acessibilidade para o horário solicitado. R04-005 alerta que constar no cadastro não comprova existência, abertura ou funcionamento. F066 refere-se a PEC e calçadas; a ressalva distingue acessibilidade das calçadas da acessibilidade do PEC.

Os três modelos evitam indicar uma quadra sem comprovação. O Gemini explica melhor a diferença entre normas gerais, cadastro e notícias de obras e a ausência de dados operacionais.

O Qwen chega à conclusão adequada, mas aproxima “vaga para praticar esporte” de “vaga de estacionamento para pessoa com deficiência”, assunto de N05-024. A justificativa deveria distinguir esses sentidos e mencionar explicitamente a falta de verificação de acessibilidade da quadra. O Llama também se abstém adequadamente, porém resume menos as limitações das fontes. “Não é possível confirmar” é mais preciso do que sugerir que nenhuma quadra existe.

## Conclusão

Nos quatro casos observados, o Gemini 3.5 Flash-Lite apresentou a melhor combinação de correção, completude, citações e reconhecimento de limites. O Qwen3 8B foi útil, com problemas localizados de completude, URL e precisão das ressalvas. O Llama 3.2 3B deixou de utilizar evidências explícitas em duas das três perguntas respondíveis; acertou a lista de modalidades e a abstenção no caso sem dados suficientes.

A amostra é pequena e não permite estabelecer superioridade geral, efeito causal do RAG, custo ou desempenho de velocidade. Para concluir sobre ganho do RAG, é necessário comparar com os resultados sem RAG da outra pessoa da equipe, mantendo os modelos efetivamente usados e as perguntas equivalentes.

## Próximas verificações

1. Conferir se Q2 do Qwen foi copiada integralmente; preservar o original e salvar eventual repetição separadamente.
2. Repetir Q1 e Q3 do Llama registrando entrada enviada, contexto configurado, versão do modelo, truncamento, configurações e saída completa. Contexto insuficiente, formato e execução são hipóteses, não causas comprovadas.
3. Acrescentar data de execução a todos os registros e resolver “amanhã” em uma data explícita em futuras rodadas.
4. Preservar os resultados desta rodada. Ampliar o conjunto e registrar repetições, sem escolher apenas a melhor saída de cada modelo.
5. Montar URLs a partir dos metadados na aplicação, em vez de depender de sua reprodução pela LLM.
