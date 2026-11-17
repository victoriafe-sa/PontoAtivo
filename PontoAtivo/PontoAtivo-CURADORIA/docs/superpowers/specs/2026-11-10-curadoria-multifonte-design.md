# PontoAtivo — curadoria multifonte com níveis de confiança

## Intenção

Ampliar o mapa esportivo do Distrito Federal sem esconder as limitações das fontes. O sistema deve
incorporar PECs recentes, acessibilidade física, paradesporto, clubes/arenas/academias privadas e
localização de parques, mas sempre distinguir informação oficial, informação declarada pela
organização, contribuição comunitária e verificação presencial.

O objetivo não é prometer um inventário perfeito. É oferecer a melhor cobertura disponível e
permitir que cada pessoa entenda por que pode ou não confiar em cada atributo.

## Situação atual

- A base do site contém 1.748 locais, incluindo 403 PECs, 141 campos de futebol, quadras, parques,
  COPs e outros equipamentos.
- A camada de mobiliário esportivo da IDE-DF é majoritariamente de 2015–2017.
- A Novacap informou em novembro de 2025 que o DF possui mais de mil PECs.
- Nenhuma fonte oficial encontrada oferece inventário completo de rampas, banheiros acessíveis,
  piso tátil e vagas PcD por local.
- O conjunto marcado como “15 parques pendentes” contém 14 parques e um ginásio.
- O Ibram possui serviço geoespacial oficial atualizado para unidades de conservação.
- O CETEFE publica endereço próprio; documentos do Comitê Paralímpico relacionam modalidades e
  locais de atendimento no DF.

## Abordagens consideradas

### 1. Curadoria multifonte com níveis de confiança — escolhida

Combina governo, sites oficiais das organizações, dados colaborativos e visitas. Cada campo do
registro carrega sua própria fonte, data e nível de evidência. Entrega cobertura crescente sem
apresentar inferências como verificações.

**Troca:** exige regras de fusão, manutenção e uma interface que explique confiança com clareza.

### 2. Somente fontes governamentais

Tem maior homogeneidade jurídica, mas mantém grandes lacunas até respostas da LAI e não resolve
privados ou boa parte do paradesporto.

### 3. Importação ampla de diretórios e mapas colaborativos

Ganha cobertura rapidamente, porém aumenta locais fechados, duplicidades, endereços inexatos e
alegações frágeis de acessibilidade.

## Escopo

### Incluído

1. Atualizar o diagnóstico: “mais de mil PECs informadas pela Novacap; 403 no cadastro geográfico
   aberto”, com data e links.
2. Criar pipeline de candidatos para PECs recentes a partir de publicações da Novacap, Agência
   Brasília e administrações regionais.
3. Preparar um pedido de LAI à Novacap solicitando inventário georreferenciado completo.
4. Resolver os 14 parques pendentes com o serviço geoespacial oficial do Ibram; resolver o ginásio
   separadamente ou mantê-lo como localização pendente.
5. Cadastrar locais de paradesporto confirmados por CETEFE, CPB, CBDV, CBBC e organizações locais.
6. Criar catálogo inicial de clubes, arenas e academias privadas confirmados em seus sites oficiais.
7. Adicionar coleta comunitária de acessibilidade, com evidência e moderação.
8. Mostrar fonte, data, confiança e aviso de necessidade de confirmação em cada atributo relevante.
9. Criar verificações automáticas de duplicidade, coordenadas, fonte, data e consistência.

### Não incluído nesta etapa

- Garantir cobertura total dos mais de mil PECs sem receber a base da Novacap.
- Copiar avaliações, fotos ou dados proprietários de Google Maps e outros diretórios comerciais.
- Declarar conformidade com a ABNT NBR 9050 sem vistoria técnica.
- Publicar telefone ou endereço pessoal de atletas, professores ou dirigentes.
- Permitir que contribuições comunitárias entrem automaticamente como verificadas.

## Modelo de evidência

O nível será atribuído **por atributo**, não apenas por local. Um clube pode ter endereço confirmado
no site oficial e banheiro acessível ainda desconhecido.

| Código | Exibição | Requisitos |
|---|---|---|
| `oficial` | Fonte governamental | Publicação ou serviço do poder público com URL e data de consulta |
| `organizacao` | Declarado pela organização | Site oficial da entidade/estabelecimento, com URL e data |
| `colaborativo` | Dado colaborativo | OpenStreetMap ou contribuição de usuário, ainda sem verificação presencial |
| `campo` | Verificado em campo | Formulário completo, data, evidência fotográfica e revisão da moderação |
| `divergente` | Informação conflitante | Duas fontes atuais discordam; o sistema mostra a divergência |
| `desconhecido` | Não informado | Não há evidência suficiente |

O selo “acessível” só poderá ser usado quando os critérios exigidos pela atividade estiverem
verificados em campo. Dados declarados aparecerão como “recurso informado”, nunca “verificado”.

## Estrutura dos dados

Cada local terá:

- identificador estável e aliases;
- nome, categoria, público/privado e condições de acesso;
- endereço, coordenadas, região administrativa e precisão da localização;
- modalidades e serviços;
- custo ou regra de associação, quando a fonte informar;
- atributos de acessibilidade independentes: rota sem degraus, entrada, circulação, banheiro,
  vaga PcD, piso tátil, sinalização, equipamento adaptado e apoio humano;
- para cada atributo: valor, nível de evidência, fonte, data da fonte, data da consulta e observação;
- estado do registro: publicado, candidato, divergente, fechado ou arquivado;
- data da última revisão.

## Pipeline de curadoria

### 1. Descoberta

- Governo: IDE-DF, Ibram/ONDA, Novacap, Agência Brasília, SEL-DF e administrações regionais.
- Paradesporto: CPB, CBDV, CBBC, CETEFE e sites oficiais das entidades.
- Privados: site oficial do estabelecimento; OpenStreetMap apenas para descobrir candidatos e obter
  coordenadas quando não houver mapa próprio.
- Comunidade: formulário do PontoAtivo.

### 2. Normalização

- Normalizar nomes, abreviações de endereços e regiões administrativas.
- Converter coordenadas para WGS84.
- Preservar o texto original da fonte.
- Marcar coordenadas como exatas, aproximadas ou centro de polígono.

### 3. Deduplicação

Um candidato será comparado com registros existentes por:

- distância geográfica: alerta até 120 m;
- nome normalizado e aliases;
- endereço/quadra;
- categoria e modalidades;
- identificador da fonte.

Casos incertos ficam na fila de revisão, sem fusão automática.

### 4. Publicação

- Fonte governamental ou site oficial: pode publicar endereço/modalidades após validação automática.
- OpenStreetMap: publica como colaborativo, com aviso para confirmar acesso.
- Contribuição comunitária: fica pendente até revisão.
- Acessibilidade: somente muda para `campo` após evidência e moderação.

## PECs

O site passará a mostrar dois números distintos:

- **403 PECs georreferenciadas no cadastro aberto usado pelo mapa**;
- **mais de mil PECs informadas pela Novacap em novembro de 2025**.

Publicações com endereço inequívoco entram como candidatos oficiais recentes. O sistema não somará
notícias para tentar reconstruir artificialmente o total, pois uma matéria pode tratar de reforma,
substituição ou reinstalação de um PEC já cadastrado.

Será produzido um texto de LAI solicitando, preferencialmente em CSV/GeoJSON:

- identificador do equipamento;
- endereço e coordenadas;
- região administrativa;
- data de instalação e última manutenção;
- estado de conservação;
- iluminação;
- situação ativa/removida;
- recursos de acessibilidade registrados;
- processo SEI ou fonte de atualização.

## Acessibilidade e verificação comunitária

O formulário de vistoria terá perguntas objetivas e opção “não consegui verificar”:

- rota desde calçada/estacionamento sem degraus;
- largura e obstáculos da entrada;
- piso regular e circulação;
- banheiro acessível e em funcionamento;
- vaga reservada e sinalizada;
- piso tátil e sinalização;
- aparelhos/quadra adaptados;
- observações temporárias, como obras ou equipamento quebrado.

Fotos devem evitar rostos, placas de veículos e documentos. A interface explicará que a contribuição
será armazenada e exibida após revisão. Registros vencem para revisão após 12 meses ou quando outro
usuário informa mudança.

## Paradesporto

- CETEFE será atualizado com endereço oficial e modalidades confirmadas.
- Locais publicados pelo CPB serão cadastrados individualmente, cada um com modalidade e data da
  publicação.
- UNIACE e equipes de basquete em cadeira de rodas só serão ligadas a um local quando a entidade,
  federação ou fonte esportiva oficial confirmar que aquele é um local regular de treino.
- Um local que apenas sediou competição não será apresentado como sede ou treino regular.
- Contatos serão institucionais; dados pessoais não serão incluídos.

## Clubes, arenas e academias privadas

A primeira versão será uma curadoria de estabelecimentos com site oficial que informe endereço e ao
menos uma estrutura esportiva. Cada registro mostrará claramente “privado”, regras de associação,
day use ou necessidade de contato quando conhecidas.

OpenStreetMap poderá fornecer candidatos e coordenadas, mas não comprovará funcionamento, preço ou
acessibilidade. Diretórios comerciais serão usados apenas para descoberta, não como fonte final.

## Parques e equipamentos sem coordenadas

- Os 14 parques serão cruzados pelo nome com a camada oficial de Unidades de Conservação do Ibram.
- Para polígonos, o pino usará um ponto interno representativo, não simplesmente um centro que possa
  cair fora da área.
- A interface identificará “ponto representativo da área do parque”.
- O Ginásio de Esportes de Samambaia será pesquisado separadamente em fonte da SEL/Administração
  Regional; sem confirmação, continuará pendente.

## Interface

- Filtro novo por origem: público, privado e organização social.
- Filtro por nível de evidência.
- Cartões mostram “Atualizado/revisado em”.
- Acessibilidade aparece como uma matriz de atributos, não como um único sim/não.
- Registros divergentes mostram as fontes lado a lado.
- Botões “Informar mudança” e “Verificar acessibilidade” abrem o formulário comunitário.
- A página de fontes exibe cobertura, idade e limitações de cada conjunto.

## Qualidade e testes

Verificações automáticas:

- identificador único;
- coordenadas dentro ou próximas do DF;
- fonte e data obrigatórias para registros publicados;
- nível de evidência dentro dos valores aceitos;
- acessibilidade `campo` exige data e evidência;
- distância/semelhança para candidatos duplicados;
- URLs válidas;
- alerta de fonte com mais de 24 meses;
- contagens por categoria e origem comparadas à versão anterior;
- teste de busca por PEC, parque, paradesporto e privado;
- Google Maps/Waze presentes quando há coordenadas.

## Entregas previstas

1. Modelo de dados multifonte e migrador da base atual.
2. Importadores oficiais do Ibram e das fontes já estruturadas.
3. Fila de candidatos/revisão em arquivos locais versionáveis.
4. Atualização dos parques e paradesporto confirmados.
5. Catálogo inicial de privados com sites oficiais.
6. Formulário comunitário e fluxo de moderação local do protótipo.
7. Texto pronto do pedido de LAI.
8. Interface de confiança, filtros e transparência.
9. Relatório de cobertura antes/depois e testes de qualidade.

## Critério de sucesso

- Nenhum atributo colaborativo/declarado é mostrado como verificado.
- Os 14 parques têm localização oficial ou motivo explícito para permanecer pendentes.
- O site apresenta corretamente 403 PECs georreferenciadas versus mais de mil informadas.
- Paradesporto e privados têm fonte institucional por registro.
- Toda informação de acessibilidade mostra nível, fonte e data.
- Usuários conseguem sugerir correções sem alterar imediatamente a base publicada.

