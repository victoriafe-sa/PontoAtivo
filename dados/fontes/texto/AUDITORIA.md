# Auditoria dos 25 documentos-fonte em texto (2026-11-07)

Resposta à revisão do PR 'Adicionados 25 documentos-fonte em texto copiável e a lista'. **Nenhum documento está classificado como aprovado ou validado**: todos estão *pendentes de validação humana*. As verificações automáticas só confirmam que o cabeçalho (título, órgão, link, abrangência) bate com o conteúdo coletado e que o ruído de interface foi removido.

## 1. O que mudou desde o PR original

- **Cadastros oficiais no lugar de notícias.** Quatro notícias/planos (F014, F015, F077, F075) foram substituídos por quatro extratos de cadastros oficiais de localização da SEDUH-DF (R01 a R04), que trazem situação física/operacional, endereço quando existe e o alerta oficial de uso.
- **Erros de metadado corrigidos:** F060 estava como Planaltina e é Samambaia; F030 tinha tema errado (substituído por F009); F063 era norma REVOGADA e regional, rotulada como regra do DF (excluída).
- **Ruído removido:** F006/F007 (Sesc) sem 'Lorem ipsum', 'Título' repetido, 'Carregando...', tour virtual e notícias repetidas; F058 sem bloco duplicado e sem dados bancários.
- **Lacunas preenchidas:** regras de uso e PcD (N01, N05), modalidades dos COPs (N03), vagas e atendimento 2026 (N02), academia pública (N04), endereços dos 12 COPs (F028).

## 2. Os problemas apontados na revisão

| Problema | Situação |
|---|---|
| F058 insuficiente | Corrigido: conteúdo útil preservado (modalidades, requisitos, taxa, gratuidade/PcD). Persiste: endereço incompleto na fonte (`SRPN – Brasília, DF, 70655-775`) e sem horário das aulas. |
| F060 região errada | Corrigido para Samambaia (catálogo e banco vetorial). |
| Sesc F006 a F008 com ruído | F006 e F007 limpos; F008 retirado do pacote (reduz o peso de fonte não governamental; segue na base do projeto). Sesc não é órgão do governo e as páginas não trazem acessibilidade. |
| Obra/projeto não prova disponibilidade | Todos os documentos têm o campo 'COMPROVA FUNCIONAMENTO ATUAL?'. Nenhum comprova. Notícias de obra foram trocadas ou marcadas como mistas; os cadastros trazem o alerta oficial da SEDUH. |
| Lacunas de modalidades e acessibilidade | Modalidades: N03, F058, F006, F007, N04. Acessibilidade: N05 (Lei 6.637/2020, recorte), N01 (5% das vagas para PcD), F016 e F066 (rampas, piso tátil, calçadas), F029 (banheiros acessíveis, só afirmado). Persiste: nenhuma fonte descreve a acessibilidade de um espaço verificada em campo. |
| Substituir inadequados | Ver seção 4. Mantidos 25 documentos (mínimo pedido: 20). |

## 3. Situação individual dos documentos

| ID | Documento | Ação | Problema encontrado | Correção | Pendência |
|---|---|---|---|---|---|
| F028 | Centros Olímpicos e Paralímpicos | Limpo | Linhas de menu, rótulo de links de edital ('Informações Gerais ... Layout dos COP ...'), '#' solto e ID numérico do site. A tabela de modalidades não veio na extração. | Ruído removido; endereços, diretores e telefones institucionais dos 12 COPs preservados. | Modalidades por unidade: indisponíveis neste documento (a lista geral está em N03). |
| F003 | Manual de Uso dos Centros Olímpicos e Paralímpicos do DF | Mantido (com PDF original) | Extração de PDF cola palavras em títulos em caixa alta; documento de 2022, anterior ao corte de 2025. | Texto mantido sem alterações; PDF original incluído. | Vigência a conferir; o título da capa deve ser lido no PDF. |
| F062 | Espaços Esportivos (SEL) | Limpo | ID numérico do site no fim do texto. | Removido. | Sem endereços. |
| F064 | Decreto nº 45.269, de 08/12/2023 | Mantido (formatação) | Texto corrido em uma só linha. | Quebra de linha antes de cada 'Art.' (sem alterar o texto). | Vigência a conferir (o próprio SINJ lista legislação correlata posterior). |
| N01 | Portaria SEL nº 99, de 02/06/2022: Programa Centros Olímpicos e Paralímpicos | Novo (substitui o F063) | Lacuna de regras de uso vigentes, com acessibilidade/PcD. O F063 (OS 61/2024) estava revogado. | Incluída a norma vigente do Programa dos COPs; a Portaria 99/2021 foi verificada e está revogada (não incluída). | Fora da base do RAG (ID N##). Conferir vigência. |
| N02 | Centros olímpicos e paralímpicos abrem mais de 12 mil vagas no DF com estrutura reforçada | Novo | Lacuna de informação atual (2026) sobre COPs e pessoas com deficiência. | Incluída. | Fora da base do RAG; não traz modalidades. |
| N03 | Centros Olímpicos e Paralímpicos do DF oferecem mais de 10 mil vagas remanescentes | Novo | Lacuna: modalidades esportivas dos COPs (a tabela da F028 não veio). | Incluída a lista oficial de modalidades. | Lista exemplificativa, sem divisão por unidade. |
| N04 | Academia pública do Parque da Cidade vira ponto de encontro e saúde para brasilienses | Novo | Lacuna: modalidades e horários de um equipamento público de academia. | Incluída. | Abrangência (RA) inferida. |
| N05 | Lei nº 6.637/2020 (Estatuto da Pessoa com Deficiência do DF): recorte do Cap. VIII e do Cap. IX (Seções I a III) | Novo (recorte) | Lacuna de acessibilidade em fonte primária: nenhuma das outras fontes é norma sobre acessibilidade. | Recorte dos capítulos relevantes, com o trecho de cada um identificado no cabeçalho. | Recorte, não o texto integral; fora da base do RAG. |
| F058 | Conjunto Aquático Cláudio Coutinho | Limpo e corrigido | Conteúdo diluído: bloco de inscrição duplicado (inclusive datas de testes de 2025, desatualizadas), lista de modalidades 3 vezes, dados bancários irrelevantes, endereço incompleto. | Bloco duplicado e dados bancários removidos; modalidades, gratuidade, PcD, taxas e localização mantidos. | Endereço continua incompleto na fonte (não foi completado); sem horário das aulas. |
| F059 | Estádio Bezerrão | Limpo | Página curta; ID numérico do site. | ID removido. | Só nome, região, inauguração, capacidade e endereço. |
| F060 | Estádio Joaquim Domingos Roriz (Rorizão) | Corrigido | ERRO DE METADADO: abrangência 'Planaltina' no catálogo; a página diz REGIÃO: Samambaia e o endereço é QR 301, Samambaia Sul. | Abrangência corrigida para Samambaia (também no catálogo e no banco vetorial). | Endereço incompleto na fonte. |
| F061 | Estádio Abadião (Estádio Maria de Lourdes Abadia) | Limpo | Página curta; ID numérico. | ID removido. | Só dados básicos do estádio. |
| F029 | Parque da Cidade Dona Sarah Kubitschek (SEL) | Limpo | Abrangência 'Plano Piloto' era inferência; ID numérico. | Abrangência marcada como inferida. | Acessibilidade só afirmada, sem verificação em campo. |
| F009 | Parque Urbano do Setor O se solidifica como espaço de lazer, segurança e convivência em Ceilândia | Novo no pacote (já estava na base) | Substitui o F030, redundante com o F029 e que não era o 'inventário de quadras' descrito no catálogo. | Incluído: parque de outra região, com entrega concluída e horário. | Horário a confirmar. |
| F056 | Parques Distritais e Ecológicos sob gestão do Brasília Ambiental | Limpo | ID numérico; página de lista, não de equipamentos. | ID removido. | Não trata de equipamentos esportivos. |
| F016 | Praça Linear, na Avenida Hélio Prates, oferece lazer e esporte para a população | Novo no pacote (já estava na base) | Lacuna de acessibilidade com entrega concluída. | Incluída no lugar do F071 (obra em andamento). | Sem endereço exato. |
| F066 | Governo do DF amplia acessibilidade e entrega novo PEC para os moradores de Ceilândia | Limpo | Rótulo de interface e rodapé de site. | Removidos. | Mistura entrega concluída e obras em andamento. |
| F065 | PEC construído no GDF na Sua Porta promove saúde e lazer para a quadra 605 do Recanto das Emas | Limpo | Bloco de tags no fim. | Removido. | Sem acessibilidade/horário. |
| R01 | Espaços comunitários (cadastro oficial SEDUH-DF) | Novo (substitui notícias) | Notícias não permitem localizar espaços nem preservam situação física/operacional. | Cadastro oficial incluído com metadado, alerta de uso e códigos sem tradução. | Maioria dos registros sem nome/endereço; códigos sem dicionário; dados de 2016 em sua maioria. |
| R02 | Mobiliário Esporte e Lazer: Pontos de Encontro Comunitário (cadastro oficial SEDUH-DF) | Novo (substitui notícias) | Notícias de PEC não trazem endereço; o cadastro traz. | Extrato dos PECs com endereço e RA, com a ressalva de camada obsoleta. | Camada obsoleta; confirmar cada local por fonte atual. |
| R03 | Mobiliário Esporte e Lazer: quadras, campos, skate e ginástica (cadastro oficial SEDUH-DF) | Novo (substitui notícias) | Faltavam quadras, campos, pistas e modalidades com endereço. | Extrato por tipo com endereço e RA. | Camada obsoleta; confirmar cada local. |
| R04 | Campos e Quadras Poliesportivas (cadastro oficial SEDUH-DF) | Novo (substitui notícias) | Sem fonte oficial de localização de quadras e campos. | Cadastro com situação física pelo domínio oficial da camada. | Quase sem nomes e sem endereços; só serve para quem cruza com mapa/CIU. |
| F006 | Sesc Ceilândia | Limpo | Texto de modelo ('Lorem ipsum', 'Título' ×6), 'Carregando...', códigos '?version=', tour virtual e notícias repetidas. | Tudo isso removido; endereço, horário, estruturas e modalidades preservados. | Sem acessibilidade; fonte não governamental. |
| F007 | Sesc Taguatinga Norte (Unidade Francisco Valdenir Machado Elias) | Limpo | Blocos de interface duplicados no topo (Trabalhe Conosco, Cardápio, Convênios, Academias, Empresas Conveniadas, 'Acessar', 'NOVO'), tour virtual e notícias. | Removidos; endereço, horário, estruturas e modalidades preservados. | Sem acessibilidade; fonte não governamental. |

Todos: estado de validação = **pendente de validação humana**.

## 4. Removidos ou substituídos (e por quê)

- **F014 (GDF na Sua Porta investe R$ 10 milhões em PECs)**: SUBSTITUÍDO por cadastros oficiais (R01, R02): predomina planejamento e obra em andamento; não comprova disponibilidade e não traz endereços.
- **F015 (Novas estações de PEC são inauguradas na Fercal)**: SUBSTITUÍDO por cadastros oficiais (R01, R02): notícia sem localidade, quadra ou endereço dos 3 PECs.
- **F077 (Praça da Quadra 26 do Paranoá)**: SUBSTITUÍDO por cadastros oficiais (R03, R04): notícia de obra; o cadastro dá localização e situação física.
- **F075 (Plano de Uso e Ocupação do Parque Urbano do Setor O)**: SUBSTITUÍDO por cadastros oficiais: mistura equipamentos existentes e previstos (projeto) e é de abril de 2024. Segue na base do RAG.
- **F063 (Ordem de Serviço nº 61/2024)**: EXCLUÍDO: norma REVOGADA e de alcance regional. A OS 61/2024 (Administrador Regional do Plano Piloto) foi revogada pela OS 83/2025, que foi revogada pela OS 88/2025 (esta apenas revoga; não localizei regulamento vigente). Estava rotulada como regra do DF inteiro e com órgão 'Governo do DF': metadados errados.
- **F013 (PEC em unidade de acolhimento de idosos (Taguatinga))**: EXCLUÍDO: o PEC fica dentro de uma instituição de acolhimento e atende os moradores dela (acesso não público).
- **F071 (Riacho Fundo II: equipamentos reformados)**: SUBSTITUÍDO por F016: texto descreve obra em andamento ('estão sendo reformados'), sem comprovar espaço entregue.
- **F076 (Planaltina: melhorias e espaços reabilitados)**: SUBSTITUÍDO por N05/N01: predomina 'obras em andamento' (24 obras; 6 concluídas).
- **F031 (Parque da Cidade 47 anos: reformas)**: EXCLUÍDO do pacote: mistura reformas feitas e previstas (playground inclusivo 'previsto'); o tema do Parque da Cidade já tem F029, F030 e N04.
- **F030 (Parque da Cidade (Setur))**: SUBSTITUÍDO por F009: o catálogo o descrevia como 'inventário de quadras', mas a página traz só uma visão geral quase idêntica à F029 (SEL); o endereço que consta é o da administração. Esse erro de tema veio de um resumo de busca de outra página e foi corrigido no catálogo.
- **F008 (Sesc Taguatinga Sul)**: EXCLUÍDO do pacote: reduz o peso de fonte não governamental (Sesc passa de 3 para 2 páginas); o documento continua na base do projeto.

## 5. Candidatos avaliados e rejeitados

- **Edital 2026 / 2025 (PDF do site da SEL)**: O arquivo é um extrato do Diário Oficial inteiro (DODF nº 63), misturado com atos de telecomunicações e habitação: ruído.
- **SEL: 'Reformada, academia pública do Parque da Cidade...' (16/06/2024)**: Publicada em 2024; a N04 (11/01/2025) cobre o mesmo assunto de forma mais recente.
- **Agência Brasília: 'Brasília ganha o 1º parque 100% inclusivo do país' (24/05/2021)**: Boa fonte de acessibilidade, mas de 2021 e com obra em primeira etapa: abaixo do corte de atualidade.
- **SEPD: basquete sobre rodas (2023)**: Não trata de espaço de prática.
- **Portaria 99/2021**: Revogada pela Portaria 99/2022 (N01).
- **OS 83/2025 (Plano Piloto)**: Revogada pela OS 88/2025; não serve como substituta do F063.
- **OS 88/2025 (Plano Piloto)**: Apenas revoga a OS 83; não contém regras de uso.
- **SEL: página 'Escola de Esporte'**: A lista de modalidades não é texto na página (0 modalidades extraídas).

## 6. Cadastros oficiais (R01 a R04): o que foi encontrado

- Texto de cada cadastro: registro de metadados oficial da SEDUH (CSW do GeoNetwork) + registros do serviço ArcGIS público da IDE-DF, lidos na data da coleta.
- **Alerta oficial da SEDUH:** locais podem constar em projetos urbanísticos sem ter sido implantados. Por isso nenhum dos R01 a R04 afirma que o espaço está aberto ou funcionando. O R01 preserva `ec_sit_fisica` e `ec_operacional` de cada registro com nome ou endereço.
- **Espaços comunitários (R01):** 2.431 registros; só 7% têm nome e 10% têm endereço; 2.185 foram atualizados em 2016. A camada não declara dicionário para os códigos de situação física/operacional, por isso aparecem como código, sem tradução. Não inventamos o significado.
- **Mobiliário Esporte e Lazer (R02, R03):** o metadado oficial declara a camada como **obsoleta** (`obsolete`) e sem informação de precisão e fonte. Tem endereço em quase todos os registros e região administrativa pelo domínio oficial, mas é um retrato antigo.
- **Campos e Quadras Poliesportivas (R04):** 9.904 polígonos, base de 2016 (e 2023 em parte); a camada não tem endereço e só 82 registros têm nome. A situação física vem do domínio oficial da camada ('construído' é situação cadastral, não uso). O tipo (`cq_tipo`) não tem dicionário.
- **Carta de Serviços da SEL-DF:** consultada; não lista os endereços dos 12 COPs, que vêm do F028. Por isso não entrou como documento próprio.

## 7. Norma revogada descoberta na auditoria (F063)

A OS 61/2024 (Administrador Regional do Plano Piloto) foi revogada pela OS 83/2025, que foi revogada pela OS 88/2025 (apenas revoga). Não localizei regulamento vigente para quadras e campos. A base do projeto também foi corrigida (a pergunta de avaliação Q13 passou a ser de 'sem resposta').

## 8. Problemas que continuam

- Nenhum documento foi validado por pessoa. Isso precisa ser feito antes de usar como informação oficial.
- Nenhuma fonte comprova funcionamento atual; notícias e cadastros descrevem a situação na data deles.
- Cadastros: dados majoritariamente de 2016, camada de mobiliário obsoleta, quase sem nomes (R01, R04) e sem endereço (R04).
- F058 e F060: endereço incompleto na fonte. F059 a F061: páginas curtas. F028: a tabela de modalidades por unidade não veio na extração.
- Sesc (F006, F007): entidade não governamental e sem informação de acessibilidade.
- Vigência a conferir: F003 (2022), F064 (alterado por legislação correlata), N01 (alterada por Portarias 279/281/282 de 2022), N05 (recorte; vetos).
- Não há regulamento vigente identificado para quadras e campos.
- Abrangência inferida (não consta do texto): F029 e N04.
- A busca por POST no GeoNetwork retorna 403; foi usado o CSW público, que funcionou.
