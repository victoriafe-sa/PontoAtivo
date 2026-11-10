# Análise das respostas — LLM sem RAG

Esta análise avalia as 12 respostas geradas em 10/11/2026 por três modelos: Gemini 3.5 Flash-Lite, Qwen3 8B e Llama 3.2 3B. As respostas são comparadas com as evidências dos JSONs de referência e com a [análise do experimento com RAG](../experimento-rag/analise-respostas.md).

A referência são as **fontes do projeto**, como no experimento com RAG. Não houve nova verificação da situação atual dos locais. "Não sustentado pelas fontes" significa que a afirmação não aparece nos textos de `dados/fontes/texto/`, e não necessariamente que seja falsa no mundo real.

A numeração segue esta rodada. A Q1 daqui corresponde à Q3 com RAG, e a Q3 daqui corresponde à Q1 com RAG (ver tabela no [README](README.md)).

## Resultado por pergunta

| Pergunta | Gemini 3.5 Flash-Lite sem RAG | Qwen3 8B sem RAG | Llama 3.2 3B sem RAG |
|---|---|---|---|
| Q1 — endereço do Bezerrão | **Contraditória**: "Setor Central" e, em seguida, "endereço específico: Setor Leste, Área Especial" | **Alucinação**: endereço "exato" inventado | Abstenção (não sabe) |
| Q2 — modalidades dos COPs | **Parcial**: mistura modalidades sustentadas e não sustentadas | **Parcial**: mistura modalidades sustentadas e não sustentadas | Abstenção (diz desconhecer os COPs) |
| Q3 — gratuidade e uso da academia | **Gratuidade certa, uso errado**: "basta comparecer, sem cadastro" | **Gratuidade certa, uso errado**, com fonte falsa ("PontoAtivo") | Resposta vaga e especulativa |
| Q4 — vaga amanhã e acessibilidade | Abstenção adequada e bem justificada | Abstenção adequada, com uma afirmação não sustentada | Abstenção adequada |

## Q1 — endereço do Estádio Bezerrão

Referência: F059-001, "St. Central – Gama, Brasília – DF, 72405-610", atualizado em 20/02/2026.

- **Gemini**: começa corretamente com "Setor Central do Gama". Na mesma frase, porém, apresenta como "endereço específico" o "Setor Leste, Área Especial", que contradiz a referência e não aparece nas fontes. Também usa o nome "Estádio Walmir Campelo Bezerra", que não consta nas fontes do projeto. A ressalva sobre possíveis mudanças é adequada, mas o leitor fica com dois endereços diferentes, e o "específico" é o errado.
- **Qwen**: responde "Av. das Forças Armadas, 1000 – Gama". O endereço não aparece em nenhuma fonte do projeto e contradiz F059-001. O raciocínio salvo (`respostas-qwen/q1-raciocinio.txt`) diz que "the precise address isn't in my knowledge base", mas a resposta final o apresenta como "endereço exato". Foi o caso mais claro de alucinação desta rodada: o modelo sabia que não sabia e, mesmo assim, inventou. As limitações que ele declara não alertam para isso.
- **Llama**: diz não ter a informação. A resposta é segura, mas inútil, não segue o formato pedido (sem as seções "Resposta / Limitações / Fontes") e escreve "estúdio" no lugar de "estádio".

## Q2 — modalidades dos COPs

Referência: N03-003 lista 12 modalidades, de forma exemplificativa e com variação por unidade: atletismo, basquete, futsal, futebol society, ginástica localizada, pilates, vôlei, jiu-jitsu, judô, taekwondo, karatê e capoterapia.

- **Gemini**: acerta atletismo, futsal, basquete e vôlei. "Futebol", "ginástica" e "lutas" são genéricos e só correspondem à referência de forma aproximada. Natação, hidroginástica e handebol **não são sustentados** pelas fontes dos COPs consultadas (N02, N03, F003 e F028). Preserva a ressalva de que a oferta varia por unidade e declara não conhecer a origem da lista.
- **Qwen**: acerta atletismo, voleibol, judô e taekwondo. "Futebol" também é genérico: as fontes falam de futsal e futebol society. Natação, ginástica artística, ciclismo, esgrima, futebol de 5 e esgrima adaptada **não são sustentados** pelas fontes. Omite 8 das 12 modalidades da referência. Reconhece que não tem uma lista exata, mas apresenta as modalidades em tom afirmativo.
- **Llama**: afirma não ter conhecimento sobre a existência dos COPs. Não segue o formato.

## Q3 — academia pública do Parque da Cidade

Referência: N04-008, notícia de 11/01/2025. A academia é gratuita. Para usá-la, é preciso baixar o app Mude – Yoga e Fitness, fazer o cadastro e agendar horário. O funcionamento depende da presença de um profissional de educação física.

- **Gemini**: acerta que é gratuita, mas trata o espaço como uma das "academias ao ar livre" comuns do DF e afirma que "não é necessário realizar cadastro prévio ou agendamento; basta comparecer". Isso **contradiz diretamente** a referência. É uma generalização plausível que leva o usuário a um procedimento errado. As ressalvas temporais estão presentes.
- **Qwen**: acerta que é gratuita, mas atribui a informação ao "projeto PontoAtivo", uma **fonte inventada** a partir da persona do prompt. O raciocínio mostra a origem do erro: "The PontoAtivo project is mentioned, so maybe that's the source". O modo de uso que ele indica, "comparecer ao local com documento de identidade", não é sustentado e contradiz a referência (app e agendamento).
- **Llama**: chama a academia de "instituição de ensino físico", diz que "é possível que seja gratuita" e não informa como utilizá-la. Não inventa um procedimento, mas também não responde. Não segue o formato.

## Q4 — vaga amanhã (11/11/2026) às 19h e acessibilidade

Referência: nenhuma fonte tem agenda de quadras nem verificação operacional de acessibilidade. Abster-se é a resposta correta, tanto com RAG quanto sem.

- **Gemini**: abstém-se e explica que não tem acesso a reservas em tempo real nem a vistorias de acessibilidade. Não faz afirmações sem base. É a melhor resposta desta pergunta.
- **Qwen**: abstém-se e diz que não há dados em tempo real, o que é adequado. Porém afirma que "acessibilidade é garantida por padrões de projeto". Isso não é sustentado e é o tipo de afirmação que a regra 5 pede para evitar. Também trata o PontoAtivo como se tivesse dados de quadras.
- **Llama**: abstém-se e recomenda contato com o órgão responsável, o que é adequado.

## Comparação com o experimento com RAG

| Pergunta | Gemini com → sem RAG | Qwen com → sem RAG | Llama com → sem RAG |
|---|---|---|---|
| Q1 Bezerrão | Correto e citado → **dois endereços, o "específico" errado** | Correto → **alucinação** | Recusa indevida → abstenção |
| Q2 COPs | 12 de 12 → ~4 de 12 **com invenções** | 8 de 12, sem invenção → ~4 de 12 **com invenções** | 12 de 12 → abstenção |
| Q3 academia | Correto (app, cadastro, agendamento) → **procedimento errado** | Correto → **uso e fonte inventados** | Recusa indevida → vaga/especulativa |
| Q4 quadra | Abstenção → abstenção | Abstenção → abstenção com afirmação não sustentada | Abstenção → abstenção |

Observações:

1. **Nos dois modelos maiores, perder o RAG transformou acertos em erros afirmados com confiança.** Gemini e Qwen estavam corretos em Q1 e Q3 com RAG. Sem RAG, ambos mantêm o tom seguro e passam a dar informações erradas: endereço e procedimento de uso. O caso da Q3 do Gemini é o mais perigoso para o usuário, porque é plausível ("academia pública é só chegar e usar") e contradiz a fonte oficial.
2. **O Gemini sem RAG é o mais cauteloso dos dois maiores.** Ele declara não conhecer a origem das informações e não inventa fontes. Ainda assim, essas ressalvas genéricas não impediram os erros factuais.
3. **O Llama sem RAG quase sempre se abstém.** Isso é mais seguro do que inventar, mas não entrega informação. Com RAG, ele acertou a Q2 (12 de 12), que aqui não conseguiu responder.
4. **Citações**: sem documentos, nenhum modelo consegue indicar uma fonte verificável, e o Qwen chega a fabricar uma (PontoAtivo). Com RAG, a rastreabilidade por ID era o principal ganho.
5. **A Q4 não diferencia os cenários.** Como nenhuma fonte tem agenda em tempo real, a resposta adequada é abster-se nos dois casos. A pergunta testa o comportamento de recusa, não o ganho do RAG.

## Custo e tempo

- **Tokens de entrada**: sem RAG, ~200–250 tokens. Com RAG, ~3.200–3.900, medidos nos modelos locais (14 a 17 vezes mais). O Gemini não foi tokenizado com os prompts com RAG.
- **Tokens de saída**: Gemini 178–225. Qwen ~430–530, a maior parte em raciocínio interno. Llama 74–192.
- **Tempo**:
  - Llama 2,2–4,7 s e Qwen 24,5–28,5 s, ambos locais (Apple M4, Ollama 0.32, modelo já carregado).
  - Gemini 1,6–51,9 s de ponta a ponta. A variação reflete a sobrecarga do serviço (houve um HTTP 503), não o modelo.
  - Os tempos com RAG não foram registrados na outra rodada, então não há comparação de latência entre os cenários.
- **Cenário de referência** (recuperação + resposta extrativa, sem LLM): ~3,7 s por consulta e nenhum token de LLM.

## Conclusão

Sem acesso aos documentos, nenhum dos três modelos respondeu corretamente às três perguntas que eram respondíveis (Q1–Q3). Os modelos maiores (Gemini e Qwen) erraram afirmando com confiança, e o menor (Llama) se absteve. Com RAG, Gemini e Qwen acertaram Q1 e Q3 citando o trecho correto.

Nesta amostra, o ganho do RAG aparece sobretudo em **informações locais e específicas** (endereço, procedimento de uso, lista oficial de modalidades), que os modelos não conhecem ou conhecem de forma genérica. O custo é um prompt de 14 a 17 vezes mais tokens de entrada.

## Limitações desta análise

- Foi feita 1 execução por pergunta e modelo, com temperatura padrão. Outra amostragem pode dar respostas diferentes.
- A rodada com RAG não registrou a versão do Ollama, o contexto nem o modo de raciocínio do Qwen. As configurações das duas rodadas podem não ser idênticas.
- A avaliação de "não sustentado" se limita às fontes do projeto. Não houve checagem externa dos fatos: o nome "Walmir Campelo Bezerra", por exemplo, pode estar correto no mundo real, apenas não consta nas fontes.
- A persona do prompt ("assistente do PontoAtivo") induziu o Qwen a usar o nome do projeto como fonte, e o Gemini se apresentou "como assistente do PontoAtivo" na Q4. Em próximas rodadas, vale avaliar se essa persona deve ser mantida no cenário sem RAG.
