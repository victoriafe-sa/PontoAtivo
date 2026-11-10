# Análise das respostas — LLM com RAG

Análise inicial dos 12 arquivos de resposta de Q1 a Q4, confrontados com os quatro JSONs de evidências e os quatro prompts locais. A ampliação para as 60 respostas de Q1 a Q20 está registrada ao final deste documento. Não houve nova execução dos modelos nem verificação da situação atual dos espaços. A referência desta análise são as evidências fornecidas ao experimento.

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

## Ampliação da análise — Q5 a Q20

Esta seção acrescenta a avaliação individual das 48 respostas de Q5 a Q20, mantendo a análise inicial de Q1 a Q4 acima. O conjunto atual reúne 60 respostas, uma por pergunta e modelo, 20 prompts e 20 arquivos de evidências. Na conferência desta ampliação, os cinco resultados de cada JSON de Q5 a Q20 coincidiram integralmente com os resultados incluídos no respectivo prompt local. Para Q5, o arquivo de evidências é `evidencias/q05-evidencias.json`.

A avaliação considera fidelidade aos trechos, completude em relação à pergunta, correspondência entre afirmação e citação, identificação correta de espaços/programas e preservação de datas e limites. “Abstenção adequada” significa que a informação solicitada não está demonstrada no contexto recuperado; “recusa indevida” significa que a resposta deixa de usar informação explícita. Uma ressalva genérica não corrige uma afirmação sem suporte feita antes dela.

Esta é uma avaliação documental do contexto recuperado, sem consulta externa, nova execução dos modelos ou confirmação da situação atual dos espaços e da vigência das normas. A ausência de informação nos cinco trechos não demonstra ausência na base completa ou no mundo real. A análise distingue insuficiência da recuperação de erro na utilização das evidências, sem atribuir causas técnicas não comprovadas.

### Resultado das novas perguntas

| Pergunta | Gemini | Qwen3 8B | Llama 3.2 3B |
|---|---|---|---|
| Q5 — regiões com COPs | Lista fiel; reconhece diferença entre total e relação disponível | Lista fiel; não distingue claramente unidades e regiões nem explicita a lacuna do total | Recusa indevida: ignora a relação explícita |
| Q6 — modalidades do COP do Setor O | Abstenção adequada; acrescenta infraestrutura de outro espaço e omite data das vagas | Reconhece insuficiência, mas chama equipamentos de modalidades e aproxima parque de COP | Abstenção adequada; sem IDs e com justificativa genérica |
| Q7 — equipamentos do COP de Samambaia | Abstenção adequada; distingue cadastro regional da unidade | Atribuição indevida de equipamentos da região ao COP | Reconhece insuficiência, mas deixa associação ambígua com equipamentos da região |
| Q8 — investimento e meta de PECs | Parcial: informa valores pontuais e não inventa meta; escopo de R$ 350 mil exige cautela | Parcial: mesmos limites, perde o caráter aproximado de R$ 35 mil | Abstenção adequada sobre meta; omite valores disponíveis |
| Q9 — acessibilidade junto ao PEC | Correta; distingue calçadas de acessibilidade do PEC | Parcial: trata exigências de padrão como entrega comprovada e usa obras em andamento sem data | Recusa indevida: ignora que a pergunta inclui melhorias nas calçadas |
| Q10 — faltas graves | Lista fiel e ressalva de vigência | Mistura pichação com destruição, classificada como falta média no contexto | Lista fiel; limitação contradiz a evidência e faltam IDs |
| Q11 — horários de aulas | Correta segundo o manual; distingue aulas e lazer comunitário | Omite segunda-feira e classifica domingo como atividade orientada | Recusa excessiva e atribuição de horários ao ID errado |
| Q12 — Decreto 28.494/2007 | Abstenção adequada: trechos são de outra norma | Abstenção adequada; contextualiza outra lei | Atribui ao decreto conteúdo de outra lei e o lista sem evidência |
| Q13 — Escola Paralímpica de Esportes | Abstenção adequada; distingue escola de COPs | Transfere idade e modalidade dos COPs para a escola | Transfere idade e modalidade dos COPs para a escola |
| Q14 — Semear | Abstenção adequada; distingue programas | Atribui ao Semear regras dos COPs e de outro projeto | Mesma troca de programa; ressalva posterior não corrige a resposta |
| Q15 — início no esporte paralímpico | Síntese sustentada; reconhece ausência de passo a passo | Orientação parcialmente sustentada; afirma vigência não comprovada | Acrescenta procedimentos sem suporte, incluindo avaliação médica e física |
| Q16 — PECs do Plano Piloto | Lista correta e ressalva de cadastro obsoleto | Lista correta e ressalva de cadastro obsoleto | Recusa indevida sobre endereços explicitamente listados |
| Q17 — isenção na Escola de Esportes | Abstenção adequada; separa escola, eventos e COPs | Responde sobre isenção de eventos, sem resolver o objeto da pergunta | Abstenção adequada; separa a regra geral da informação ausente |
| Q18 — mensalidades privadas no Lago Sul | Abstenção adequada | Abstenção adequada | Abstenção adequada; sem IDs |
| Q19 — reserva de tênis hoje à noite | Abstenção adequada | Abstenção adequada; reconhece cadastro obsoleto | Abstenção adequada, com data e identificação de fonte incorretas |
| Q20 — banheiro adaptado no PEC da Fercal | Abstenção adequada; identifica desencontro geográfico | Abstenção adequada; distingue obrigação legal de comprovação local | Abstenção adequada; sem IDs e pouco detalhamento |

### Q5 — regiões administrativas com Centros Olímpicos e Paralímpicos

**Referência:** N02-005 apresenta 11 entradas de unidades em dez nomes de localidades, pois Ceilândia aparece duas vezes, como Setor O e P Norte. N02-002 menciona 12 unidades no DF. Logo, a relação recuperada não basta para identificar a unidade faltante nem para oferecer uma lista exaustiva de toda a rede. Não se deve completar a lista por conhecimento externo ou deduzir presença física em todas as regiões a partir da fala institucional.

**Gemini:** apresenta os dez nomes de localidades disponíveis, agrupa corretamente as duas unidades de Ceilândia e cita N02-005. Reconhece a diferença entre o total declarado de 12 unidades e os locais listados, além de situar os dados em abril de 2026. É a resposta mais completa das três para o contexto disponível. O arquivo atual `respostas-gemini/q5.txt` não contém identificação de modelo; a atribuição ao Gemini decorre da pasta e não de um registro individual de execução.

**Qwen:** reproduz fielmente as 11 entradas, sem inventar localização. Entretanto, apresenta as duas unidades de Ceilândia em uma lista chamada de “regiões”, sem distinguir claramente unidade e região, e não explicita a inconsistência com o total de 12. A ressalva sobre o prazo de inscrição é acessória à pergunta e não substitui a indicação de que a relação pode estar incompleta.

**Llama:** afirma que as regiões não são mencionadas, apesar da listagem explícita em N02-005. É recusa indevida por não aproveitar a evidência. Também substitui os IDs por uma descrição genérica das instituições.

### Q6 — modalidades do COP do Setor O

**Referência:** N02-005 informa vagas por unidade, sem modalidades. F009-004 e os demais trechos F009 descrevem o Parque Urbano do Setor O, sem demonstrar que sua infraestrutura pertença ao COP. A resposta adequada é reconhecer a ausência de modalidades específicas da unidade.

**Gemini:** reconhece corretamente a insuficiência e cita N02-005. Identifica a infraestrutura adicional como pertencente ao parque, mas incluí-la em uma resposta sobre o COP pode sugerir associação não demonstrada. Também apresenta as 1.793 vagas sem situá-las em abril de 2026; o número é histórico, não comprovação de vagas disponíveis na execução.

**Qwen:** admite que não há modalidades específicas do COP, mas chama quadra, campo, playground e academia de “modalidades esportivas”. São equipamentos ou instalações. A referência a “dezenas de modalidades” em N02-005 diz respeito ao conjunto dos COPs e não comprova a oferta específica do Setor O. A resposta deveria separar explicitamente parque, unidade e rede.

**Llama:** abstém-se corretamente de listar modalidades do COP. Contudo, a afirmação ampla de que os trechos não mencionam atividades físicas é imprecisa: F009-008 menciona atividades físicas orientadas no parque. Isso não responde à pergunta sobre o COP. Faltam IDs que permitam rastrear essa distinção, e dizer que nenhuma fonte foi utilizada não documenta a leitura dos trechos.

### Q7 — equipamentos do Centro Olímpico de Samambaia

**Referência:** F028-009 apresenta contato e endereço do COP, e N02-005 informa vagas. R03-174, R03-179 e R03-171 listam equipamentos em endereços da região administrativa, sem vinculá-los ao centro. Portanto, não é possível construir um inventário do COP com esses registros.

**Gemini:** identifica corretamente a lacuna e distingue os logradouros regionais da unidade. Os dados adicionais de endereço, direção e vagas estão sustentados; o número de vagas é situado em abril de 2026. A resposta é adequada, embora os contatos e a direção devam continuar entendidos como informações da página na data indicada, sem confirmação operacional atual.

**Qwen:** afirma que o COP possui quadras, campos, skate parks e aparelhos de ginástica, usando registros de diferentes endereços de Samambaia. É atribuição indevida de informações geográficas: estar na mesma região não prova pertencer ao mesmo equipamento público. A ressalva sobre obsolescência não resolve esse erro de identidade.

**Llama:** começa reconhecendo que faltam informações específicas, mas em seguida lista equipamentos regionais e diz que podem não refletir a situação atual “do centro”. Essa formulação deixa uma associação indevida implícita. Deveria informar que o vínculo com o COP não está demonstrado, além de citar os IDs em vez de declarar que nenhuma fonte específica foi citada.

### Q8 — investimento da Novacap e quantidade de PECs prevista

**Referência:** F065-002 informa aproximadamente R$ 35 mil por PEC no contexto da notícia. F066-001 e F066-002 associam R$ 350 mil à descrição de calçadas e entrega de um PEC em Ceilândia; o recorte não discrimina o orçamento de cada componente. Nenhum dos cinco trechos apresenta investimento global e meta total de instalação ou revitalização.

**Gemini:** recupera o valor aproximado por PEC e reconhece corretamente que não há quantitativo total. Entretanto, descreve R$ 350 mil como investimento na entrega do PEC, sem esclarecer o possível escopo conjunto com as calçadas. Não é seguro equiparar os dois valores como custos unitários comparáveis. Faltam datas para situar os investimentos pontuais.

**Qwen:** também evita inventar meta ou investimento total. Perde a qualificação “aproximadamente” ao apresentar R$ 35 mil e generaliza o valor para “cada PEC instalado”. Repete a atribuição dos R$ 350 mil exclusivamente a um PEC, sem separar os componentes da obra. É uma resposta parcial, útil se esses limites forem explicitados.

**Llama:** abstém-se adequadamente sobre a meta, mas não informa nenhum dos valores disponíveis. Confunde “quanto” em dinheiro com “quantidade de PECs” e não distingue a parte respondível da parte sem evidência. A listagem de fontes com datas não compensa a omissão do valor aproximado de F065-002.

### Q9 — melhorias de acessibilidade entregues junto ao PEC de Ceilândia

**Referência:** F066-001 e F066-002 descrevem 2 mil metros de calçadas na EQNO 11/13 e entrega do PEC na quadra 9/11. F066-003 e F066-004 mencionam exigências de piso tátil e rebaixamento de meio-fio. As ressalvas delimitam a acessibilidade às calçadas; não certificam o PEC. F066-005 descreve outras obras em andamento na época da notícia.

**Gemini:** informa corretamente extensão e localização das calçadas e distingue as exigências de padrão da acessibilidade do PEC. Preserva a data da publicação e evita afirmar situação atual. F066-001 também registra atualização em 26/10/2026; reconhecê-la tornaria a ressalva temporal mais completa, sem transformar a atualização editorial em vistoria das instalações.

**Qwen:** acerta os 2 mil metros e a distinção entre calçadas e PEC. Contudo, afirma a entrega das calçadas “com piso tátil e rebaixamento de meio-fio”, quando o corpo dos trechos apresenta esses itens como exigências dos padrões atuais. Além disso, F066-001 e F066-002 não são os trechos que explicitam tais exigências. Ao dizer que outras obras “não estão concluídas”, omite que essa era a situação descrita na notícia, sem prova da situação atual.

**Llama:** recusa responder porque as melhorias eram calçadas, e não o PEC. A pergunta pede melhorias entregues “junto com” o equipamento, de modo que as calçadas respondem diretamente. É recusa indevida por estreitar o objeto da pergunta; faltam ainda IDs e dados concretos da intervenção.

### Q10 — condutas classificadas como falta grave nos COPs

**Referência:** F003-014 contém os oito itens da seção de faltas graves e a pena de desligamento. F003-012 classifica depredação de equipamentos ou instalações como falta média. O manual é identificado nos metadados como documento de 2022, cuja vigência precisa ser conferida.

**Gemini:** reproduz os oito itens e a pena com citação direta a F003-014, preservando a ressalva de vigência. Mantém inclusive o item circular “incidir em uma falta grave”, que já está no texto recuperado; isso é limitação da redação da evidência, não invenção do modelo. A troca de “objetivo” por “objeto” normaliza um provável ruído de extração.

**Qwen:** recupera os principais itens e a ressalva temporal, mas amplia pichação para “pichar ou destruir dependências”. O contexto classifica depredação como falta média em F003-012, portanto essa síntese altera a categoria disciplinar. A citação de ambos os trechos no final não corrige a classificação. A pena também deveria receber ID junto à afirmação.

**Llama:** reproduz fielmente a lista, inclusive o ruído “objetivo”, mas usa números de subitens em vez dos IDs solicitados. A limitação final diz que não é possível confirmar a classificação porque a fonte traz regras de uso e conduta; isso contradiz a seção explicitamente intitulada “Falta Grave”. O limite correto seria a vigência atual do manual, não a ausência de classificação no documento. A pena é omitida, embora seja informação adicional à pergunta.

### Q11 — horários das aulas nos COPs

**Referência:** F003-004 prevê atividades orientadas às segundas das 14h às 18h, de terça a sexta das 6h45 às 21h45 e aos sábados das 8h às 12h, conforme a grade. F003-004 e F003-005 distinguem o lazer comunitário de sábado à tarde e domingo. São faixas gerais do manual, não a grade atual de cada turma.

**Gemini:** apresenta corretamente as três faixas, separa manutenção e lazer comunitário e cita os trechos apropriados. Preserva a ressalva sobre o manual de 2022. A resposta é a mais completa e deveria continuar sendo lida como descrição documental, sem confirmação da grade vigente por modalidade e unidade.

**Qwen:** omite a segunda-feira das 14h às 18h e inclui domingo das 9h às 16h como atividade física orientada. O domingo pertence à oferta comunitária de lazer em F003-005, não à lista de aulas do item 2.3 de F003-004. Depois repete os horários de lazer corretamente, mas não corrige a classificação anterior. Acerta a necessidade de conferir a vigência.

**Llama:** declara ausência de horários e, na mesma resposta, reproduz as faixas de segunda a sábado. Há informação suficiente para responder com ressalva, embora não para indicar turma específica. Atribui essas faixas a F003-005, mas elas estão em F003-004, e não apresenta a ressalva relevante sobre o ano do manual.

### Q12 — Decreto distrital nº 28.494/2007 e acessibilidade esportiva

**Referência:** os cinco resultados são trechos N05 da Lei nº 6.637/2020. Não há texto do decreto solicitado. Não é possível atribuir ao decreto o conteúdo de outra norma apenas pela semelhança temática.

**Gemini:** abstém-se corretamente e identifica a troca de norma no contexto recuperado. A seção de fontes poderia citar os IDs N05 para sustentar essa identificação, em vez de registrar apenas “Nenhuma”. O conteúdo do decreto permanece não demonstrado.

**Qwen:** também distingue a lei do decreto e reconhece a insuficiência. A síntese adicional sobre acessibilidade é compatível com os trechos, mas os IDs aparecem concentrados no final, sem vinculação às afirmações específicas. A conclusão central é correta.

**Llama:** atribui ao decreto determinações e artigos de outra lei e inclui o próprio decreto nas fontes, embora não tenha sido fornecido. Além da troca de norma, o art. 99 recuperado trata de datas para eventos esportivos para pessoas com deficiência, não de uma regra geral de acessibilidade das instalações. A limitação subsequente não corrige a atribuição sem suporte.

### Q13 — faixa etária e modalidades da Escola Paralímpica de Esportes

**Referência:** os trechos tratam dos COPs, não identificam a Escola Paralímpica de Esportes. Há ainda idades diferentes no contexto: a portaria traz 3 anos, enquanto a página e a notícia de matrícula mencionam 4. N03-002 apresenta apenas o começo de uma lista de modalidades, com atletismo.

**Gemini:** reconhece a ausência de informação sobre a escola e mantém os dados dos COPs identificados como dados de outro programa. Expõe as duas idades com seus IDs e não completa a lista de modalidades por inferência. Seria útil situar a portaria de 2022 e a notícia de 2025, em vez de deixar as idades apenas como alternativas; isso não altera a abstenção correta para a escola.

**Qwen:** atribui à escola idade mínima de 3 anos e atletismo com base em documentos dos COPs. A ressalva admite falta de modalidades específicas, mas não corrige a afirmação inicial sobre a instituição errada nem a idade. Citações existentes não significam sustentação quando a entidade citada é outra.

**Llama:** faz a mesma transferência, escolhendo 4 anos e atletismo de N03-002. Cita o trecho, mas não demonstra vínculo entre os COPs e a escola, não reconhece a idade divergente e não apresenta a seção de limitações. A falha principal é de identidade institucional.

### Q14 — oferta do programa Semear para pessoas com deficiência

**Referência:** nenhum dos cinco trechos menciona Semear. N01-009, N01-014 e N01-023 tratam dos COPs; N01-042 inclui o Projeto Esporte à Meia-Noite e o início da seção de outro projeto. Não há base para transferir essas regras ao Semear.

**Gemini:** identifica corretamente a ausência do programa e apresenta os dados dos COPs como contexto separado, com IDs adequados para reserva de vagas, espaços e turmas. Não os transforma em descrição do Semear. Poderia preservar também a ressalva de vigência da portaria ao incluir esse contexto normativo.

**Qwen:** combina objetivos dos COPs, reserva de 5% e atividades de outro projeto para descrever o Semear. É uma composição sem suporte para o programa perguntado. A ressalva sobre funcionamento e vigência não trata do problema central: as evidências não identificam Semear.

**Llama:** atribui atividades e reserva de vagas ao Semear e depois admite que não sabe se o programa é separado dos COPs. Essa incerteza deveria impedir a atribuição inicial. Também não cita os IDs junto às afirmações.

### Q15 — como começar a praticar esporte paralímpico

**Referência:** os trechos sustentam direitos gerais, objetivos dos COPs, possibilidade de pleitear acesso, prioridade presencial e alocação em turmas mediante avaliação e disponibilidade. Não contêm procedimento completo de inscrição, documentos ou exigência explícita de avaliação médica e física.

**Gemini:** aproveita as informações disponíveis e preserva a condição de avaliação e vaga, sem inventar documentos ou etapas. Explica que falta um passo a passo prático. A idade de 3 anos está sustentada em N01-012, mas deveria vir acompanhada da identificação temporal da portaria e da necessidade de conferir vigência; o contexto não comprova a idade atualmente aplicada em cada turma.

**Qwen:** oferece orientação geral compatível com os objetivos e os direitos documentados, mas omite a condição de avaliação e disponibilidade de turmas, relevante para o ingresso. Nas limitações, declara que as normas “são vigentes e em vigor”, embora os metadados peçam conferir vigência e redação consolidada. A recomendação posterior de verificar a atualidade não comprova a afirmação anterior.

**Llama:** apresenta um roteiro com busca de modalidades, contatos e avaliação médica e física. Algumas ações podem parecer razoáveis, mas não estão estabelecidas como procedimento pelos trechos fornecidos; sobretudo, a avaliação de N01-014 não está qualificada como médica e física. Não informa a idade explícita que diz ser preciso verificar, omite IDs e reconhece a falta de procedimento apenas depois de inventar etapas. O roteiro deveria separar informação documental de orientação adicional, que o prompt não autorizava como fato externo.

### Q16 — endereços dos PECs listados no Plano Piloto

**Referência:** R02-038 e R02-039 apresentam nove endereços distintos: Parque da Cidade, SGAS 614 e sete endereços SQS. Parque da Cidade aparece em três registros, sem coordenadas que permitam distinguir suas posições no trecho. R02-038 também contém uma linha de Planaltina, que deve ser excluída da resposta. O cadastro é obsoleto e as linhas têm atualização de 27/08/2015.

**Gemini:** lista corretamente os nove endereços, exclui Planaltina e cita os trechos correspondentes. Preserva a ressalva de que o cadastro não prova existência ou funcionamento atual. A data de atualização do metadado em 07/03/2023 está sustentada nos metadados de R02-038 e não deve ser confundida com atualização das linhas de 2015. Poderia explicitar as três ocorrências do Parque da Cidade para não sugerir um inventário de apenas nove equipamentos.

**Qwen:** também lista os nove endereços corretamente e reconhece a obsolescência e a falta de prova de existência atual. Faltam as datas das linhas e a distinção entre endereços únicos e múltiplos registros no parque. São ressalvas de completude, sem invalidar a lista apresentada.

**Llama:** repete apenas a região e afirma que não há localização específica. Os endereços estão explícitos em R02-038 e R02-039. É recusa indevida: não se deve confundir ausência de coordenadas ou confirmação atual com ausência de endereço cadastrado. Acerta apenas a ressalva de obsolescência.

### Q17 — isenção da taxa da Escola de Esportes

**Referência:** F064-004 trata de preço público para uso de espaços em eventos e autorização de isenção ou redução. N01-049 prevê gratuidade das ações dos COPs. Nenhum trecho estabelece quem é isento de taxa na Escola de Esportes solicitada.

**Gemini:** reconhece a insuficiência específica e separa as regras de eventos e COPs. Os fatos adicionais são sustentados, mas F064-004 termina no meio da condição de autorização; a resposta não deve ser lida como descrição completa dos requisitos de isenção. Seria útil preservar as ressalvas sobre vigência das normas citadas.

**Qwen:** apresenta uma regra verdadeira de F064-004 sobre órgãos públicos que realizam eventos, mas não explica que ela não responde à taxa da Escola de Esportes. É resposta ao objeto errado, ainda que a citação esteja correta e a ressalva de vigência seja adequada. Faltou abster-se especificamente sobre a escola.

**Llama:** apresenta a regra de eventos com ID e reconhece explicitamente que faltam dados sobre a escola. A conclusão é adequada e evita transferir a isenção automaticamente aos alunos. Poderia começar pela insuficiência específica e incluir a ressalva de vigência, reduzindo o risco de confundir a contextualização com a resposta.

### Q18 — mensalidade de academias particulares do Lago Sul

**Referência:** o contexto contém notícia da academia pública gratuita do Parque da Cidade e cadastro de equipamentos públicos. Não informa preços de academias particulares do Lago Sul. Gratuidade de um espaço público em outra região não responde à pergunta sobre mensalidades privadas.

**Gemini:** abstém-se corretamente e identifica tanto o desencontro entre público e privado quanto a diferença de local. Usa IDs para explicar o conteúdo disponível, sem estimar preços.

**Qwen:** também se abstém e preserva a ressalva temporal da notícia. A frase de que as evidências são “apenas” sobre a academia pública é incompleta, pois há R03-072, mas o próprio bloco de fontes reconhece esse cadastro. Essa imprecisão de descrição não muda a ausência de dados sobre mensalidades.

**Llama:** reconhece a falta de preços e evita inventá-los. A estrutura repete a conclusão antes e depois de “Resposta” e não usa IDs. “Nenhuma fonte foi utilizada” deveria ser substituído por indicação de quais trechos foram examinados e por que não respondem à pergunta, sem sugerir que houve uma fonte de preços.

### Q19 — quadra de tênis do Gama disponível hoje à noite

**Referência:** o contexto traz o Bezerrão e registros cadastrais de quadras poliesportivas e outros equipamentos. Não identifica quadra de tênis nem agenda ou sistema de reservas. As linhas cadastrais são de 2015/2017, embora a coleta dos documentos seja de 2026.

**Gemini:** abstém-se adequadamente, sem transformar quadra poliesportiva em quadra de tênis nem inferir disponibilidade. Cita os documentos para explicar a limitação. Poderia mencionar expressamente a obsolescência cadastral, mas a falta de dados de reserva já sustenta a conclusão.

**Qwen:** também reconhece corretamente a ausência de modalidade específica e de disponibilidade, com ressalva explícita sobre os dados obsoletos. Não inventa local ou horário e mantém a conclusão no nível de impossibilidade de confirmação.

**Llama:** chega à abstenção correta, mas afirma que os registros são de 2026, confundindo a coleta com as datas das linhas. Também chama F059 de “metadados do cadastro”; F059-001 é a página do Estádio Bezerrão. Usa códigos de fonte em vez dos IDs completos dos trechos. Esses erros prejudicam a rastreabilidade da justificativa, embora não levem à indicação de uma reserva falsa.

### Q20 — banheiro adaptado no PEC da Fercal

**Referência:** F065 descreve Recanto das Emas; F066 descreve Ceilândia. N05-024 apresenta exigência geral de sanitários acessíveis em espaços públicos, sem vistoria ou descrição do PEC da Fercal. Norma geral não comprova instalação local.

**Gemini:** reconhece corretamente a falta de informação sobre Fercal, identifica as duas localidades efetivamente descritas e cita os trechos. Não converte ausência de dado em afirmação de inexistência de banheiro.

**Qwen:** também se abstém corretamente e distingue de forma explícita a exigência normativa da comprovação de cumprimento no local. A referência ao art. 113 deveria receber N05-024 junto à afirmação; listá-lo apenas no final reduz a precisão das citações. A conclusão é sustentada.

**Llama:** diz corretamente que não há evidência que comprove o banheiro, sem afirmar que ele não existe. A justificativa é breve e não identifica os desencontros geográficos nem a diferença entre norma e instalação. Faltam IDs dos trechos examinados.

## Síntese atualizada do conjunto

A conclusão inicial acima refere-se às quatro primeiras perguntas. Com a inclusão de Q5 a Q20, o Gemini continua apresentando a melhor consistência documental observada neste conjunto: distingue programas e espaços, recupera listas explícitas e reconhece informações ausentes. Isso não significa ausência de problemas: há limites na apresentação do escopo do investimento de Q8, informações históricas sem data em Q6 e ressalvas de vigência incompletas em respostas que contextualizam normas.

O Qwen utiliza bem várias evidências, mas os novos casos revelam erros de atribuição que vão além de omissões de detalhe: equipamentos da região são atribuídos ao COP em Q7; regras dos COPs são transferidas à Escola Paralímpica em Q13; regras dos COPs e de outro projeto são atribuídas ao Semear em Q14. Em Q10 altera a classificação de uma conduta, e em Q11 mistura faixas de aulas e lazer. Acerta abstenções relevantes, como Q12, Q18, Q19 e Q20.

O Llama combina abstenções corretas em perguntas sem suporte com recusas indevidas diante de dados explícitos, como Q5, Q9 e Q16, além da resposta contraditória de Q11. Também apresenta atribuições sem suporte em Q12, Q13 e Q14 e um procedimento não documentado em Q15. Assim, a tendência observada nas primeiras perguntas persiste, mas deve ser descrita por tipo de falha, sem concluir incapacidade geral do modelo ou causa técnica específica.

As falhas de recuperação e geração devem ser separadas. Em Q6, Q7, Q12, Q13, Q14 e Q17, por exemplo, os trechos não entregam a informação específica pedida; inventar uma resposta com documentos apenas semelhantes é erro adicional de geração. Em Q5, Q9 e Q16, a evidência necessária para pelo menos uma resposta documental está disponível, e a recusa do Llama não pode ser atribuída simplesmente à falta de recuperação.

As 48 respostas novas têm até 200 palavras pelo critério simples de separação por espaços, excluída a linha inicial de identificação do modelo quando presente. Esse requisito formal não garante qualidade: o principal problema de formato é a ausência ou má associação de IDs, especialmente nas respostas do Llama. Listar um documento no final não demonstra que ele sustente cada afirmação, e metadados de coleta não devem ser apresentados como datas de atualização dos registros.

Não foram atribuídas notas numéricas ou taxas globais de acerto, porque respostas parciais combinam dimensões diferentes e ainda não há rubrica quantitativa previamente fixada. A ampliação permite uma comparação qualitativa destas 60 respostas, sem demonstrar superioridade geral, ganho causal do RAG, custo ou velocidade. Para medir ganho do RAG, permanece necessária a comparação equivalente com respostas sem RAG e o registro das condições efetivas de execução.

### Verificações adicionais sugeridas pela ampliação

1. Incluir casos de controle para distinguir COP, parque, região administrativa, Escola Paralímpica, Escola de Esportes e Semear, avaliando a entidade de cada afirmação e não apenas a presença de citação.
2. Diferenciar ausência de informação, dado histórico e confirmação operacional atual; tratar datas de publicação, atualização editorial, coleta e atualização cadastral como campos distintos.
3. Em Q8, conferir o documento integral antes de interpretar R$ 350 mil como custo exclusivo de um PEC; manter essa verificação separada da avaliação dos cinco trechos enviados.
4. Em futuras execuções, preservar identificação de modelo, entrada efetivamente enviada e parâmetros em registro rastreável. A organização atual dos TXT e os prompts locais, isoladamente, não comprovam esses elementos.
5. Definir uma rubrica antes de calcular percentuais: correção factual, completude, identidade da entidade, citações, temporalidade e abstenção. Registrar separadamente a suficiência do contexto recuperado.
