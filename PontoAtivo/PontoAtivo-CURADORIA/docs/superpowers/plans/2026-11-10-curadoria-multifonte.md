# Curadoria multifonte do PontoAtivo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ampliar e qualificar o mapa do PontoAtivo com níveis de evidência por atributo, localização oficial dos parques pendentes, locais confirmados de paradesporto, catálogo inicial de privados, diagnóstico correto das PECs e contribuição comunitária moderável.

**Architecture:** Manter o site estático e a base publicada em `data/locais.js`, adicionando arquivos JSON versionáveis para fontes, candidatos e contribuições. Um módulo Python puro normaliza, valida, deduplica e gera a base; a interface JavaScript consome os novos campos sem depender de backend. Contribuições do protótipo ficam em `localStorage` e podem ser exportadas para revisão, nunca entrando automaticamente na base publicada.

**Tech Stack:** HTML/CSS/JavaScript sem framework, Leaflet, Python 3 (biblioteca padrão), Node.js para testes CDP, JSON/GeoJSON, ArcGIS REST.

**Spec:** `docs/superpowers/specs/2026-11-10-curadoria-multifonte-design.md`

## Global Constraints

- Nenhum atributo colaborativo ou declarado pode ser apresentado como verificado em campo.
- O nível de evidência pertence ao atributo, não somente ao local.
- Fontes publicadas exigem URL e data de consulta.
- Não copiar avaliações, fotos ou conteúdo proprietário de diretórios comerciais.
- Não declarar conformidade com a ABNT NBR 9050 sem vistoria técnica.
- Não publicar dados pessoais de atletas, professores ou dirigentes.
- OpenStreetMap serve como fonte colaborativa ou descoberta, nunca como comprovação de preço, funcionamento ou acessibilidade.
- Contribuições comunitárias permanecem pendentes até moderação.
- O site continua funcional como aplicação estática servida por `python3 -m http.server 5173`.

## Review Focus

- Registro com fonte oficial para o endereço, mas acessibilidade desconhecida: a interface deve mostrar níveis diferentes por atributo — teste na Task 6.
- Candidato a menos de 120 m de um registro existente, porém com nome diferente: deve ir para revisão e não ser fundido automaticamente — teste na Task 1.
- Parque em polígono côncavo: o ponto representativo deve cair dentro do polígono — teste na Task 2.
- Contribuição comunitária sem foto ou com “não consegui verificar”: deve salvar como pendente sem promover acessibilidade — teste na Task 7.
- Fonte antiga ou URL indisponível: deve continuar visível com alerta de revisão, sem apagar silenciosamente o registro — teste na Task 1.

---

## Estrutura de arquivos

- `ferramentas/curadoria.py`: modelo, normalização, validação, deduplicação e fusão por atributo.
- `ferramentas/importar_ibram.py`: consulta/ingestão do serviço geoespacial oficial e ponto interno dos parques.
- `ferramentas/gerar_base.py`: orquestra fontes curadas e produz `data/locais.js` e métricas.
- `ferramentas/tests/test_curadoria.py`: testes unitários do modelo e regras de qualidade.
- `ferramentas/tests/test_ibram.py`: testes de correspondência e geometria dos parques.
- `ferramentas/tests/fixtures/`: pequenas amostras determinísticas das fontes para testes offline.
- `data/curadoria/fontes.json`: catálogo de fontes e datas de consulta.
- `data/curadoria/paradesporto.json`: locais/modalidades confirmados por fontes institucionais.
- `data/curadoria/privados.json`: catálogo inicial de privados verificados em sites oficiais.
- `data/curadoria/pecs_recentes.json`: candidatos encontrados em publicações oficiais.
- `data/curadoria/revisao.json`: divergências, duplicidades possíveis e pendências.
- `data/curadoria/metricas.json`: cobertura, idade e qualidade por categoria/origem.
- `data/locais.js`: base publicada gerada.
- `app.js`: filtros, cartões, níveis de evidência e contribuição comunitária.
- `index.html`: controles, transparência, modal/formulário e diagnóstico de cobertura.
- `styles.css`: componentes visuais de confiança, acessibilidade e moderação.
- `ferramentas/teste-curadoria.mjs`: teste funcional CDP da interface.
- `docs/pedido-lai-novacap.md`: pedido pronto de acesso à informação.
- `docs/relatorio-cobertura.md`: resultado antes/depois e lacunas restantes.

---

### Task 1: Modelo de evidência e qualidade

**Files:**
- Create: `ferramentas/curadoria.py`
- Create: `ferramentas/tests/test_curadoria.py`
- Create: `ferramentas/tests/fixtures/locais_minimos.json`
- Create: `data/curadoria/fontes.json`

**Interfaces:**
- Produces: `Evidence(value, level, source_id, source_date, checked_at, note)`; `normalize_place(record) -> dict`; `validate_place(record, sources, today) -> list[Issue]`; `find_duplicate_candidates(candidate, published, radius_m=120) -> list[Match]`; `merge_place(existing, candidate) -> MergeResult`.
- Consumes: nenhum componente novo.

- [ ] **Step 1: Escrever testes falhos para níveis, validação e duplicidade**

Cobrir: enum aceito; fonte/data obrigatórias; `campo` exige data e evidência; coordenadas fora do DF; fonte com mais de 24 meses gera aviso; candidato a 80 m com nome diferente vira `possible_duplicate`; atributos com evidência distinta não são achatados.

- [ ] **Step 2: Executar os testes e confirmar falha pela ausência do módulo**

Run: `python3 -m unittest ferramentas.tests.test_curadoria -v`
Expected: FAIL com `ModuleNotFoundError` ou funções ausentes.

- [ ] **Step 3: Implementar o modelo e as regras mínimas**

Valores exatos de `level`: `oficial`, `organizacao`, `colaborativo`, `campo`, `divergente`, `desconhecido`. Severidades: `error`, `warning`, `review`.

- [ ] **Step 4: Executar testes unitários**

Run: `python3 -m unittest ferramentas.tests.test_curadoria -v`
Expected: PASS, zero falhas.

- [ ] **Step 5: Registrar o catálogo inicial de fontes**

Incluir IDE-DF, Novacap, Agência Brasília, Ibram/ONDA, SEL-DF, CPB, CETEFE e OpenStreetMap com `id`, `name`, `url`, `kind`, `checked_at` e observações de uso.

- [ ] **Step 6: Commit**

```bash
git add ferramentas/curadoria.py ferramentas/tests data/curadoria/fontes.json
git commit -m "feat: add evidence-aware curation model"
```

### Task 2: Localização oficial dos parques pendentes

**Files:**
- Create: `ferramentas/importar_ibram.py`
- Create: `ferramentas/tests/test_ibram.py`
- Create: `ferramentas/tests/fixtures/ibram_poligonos.json`
- Modify: `data/curadoria/fontes.json`
- Modify: `data/curadoria/revisao.json`

**Interfaces:**
- Consumes: `normalize_place`, `validate_place` da Task 1.
- Produces: `normalize_park_name(name) -> str`; `representative_point(geometry) -> tuple[float, float]`; `match_pending_parks(pending, features) -> MatchReport`.

- [ ] **Step 1: Escrever testes falhos de nomes e geometria**

Cobrir aliases como `Irmão Afonso Haus`/`Irmãos Afonso Haus`, `Cachoeirinha e Coqueirão`/`Cachoeirinha`, acentos e qualificadores. Testar polígono côncavo cujo centro médio cai fora e exigir ponto interno.

- [ ] **Step 2: Confirmar falha**

Run: `python3 -m unittest ferramentas.tests.test_ibram -v`
Expected: FAIL por módulo/funções ausentes.

- [ ] **Step 3: Implementar importação offline e consulta opcional**

Aceitar arquivo ArcGIS/GeoJSON local para reprodutibilidade. A consulta remota deve ser um comando explícito, nunca executada durante testes.

- [ ] **Step 4: Resolver os 14 parques e separar o ginásio**

Gerar relatório com `matched`, `ambiguous`, `unmatched`. Atualizar coordenadas como `oficial`, precisão `representative_point`, e fonte Ibram/ONDA. O Ginásio de Samambaia não entra na contagem de parques.

- [ ] **Step 5: Executar testes**

Run: `python3 -m unittest ferramentas.tests.test_ibram -v`
Expected: PASS, incluindo ponto interno.

- [ ] **Step 6: Commit**

```bash
git add ferramentas/importar_ibram.py ferramentas/tests data/curadoria
git commit -m "feat: resolve pending parks from official Ibram geometry"
```

### Task 3: PECs recentes, diagnóstico e pedido de LAI

**Files:**
- Create: `data/curadoria/pecs_recentes.json`
- Create: `ferramentas/tests/test_pecs.py`
- Create: `docs/pedido-lai-novacap.md`
- Modify: `index.html`
- Modify: `data/curadoria/metricas.json`

**Interfaces:**
- Consumes: validação/deduplicação da Task 1.
- Produces: registros candidatos com `status=candidate`; métricas `pec_geocoded_open=403`, `pec_reported_min=1000`, `pec_reported_as_of=2025-11-04`.

- [ ] **Step 1: Escrever teste falho para não somar matérias como PECs únicas**

O teste deve garantir que reforma/reinstalação com mesmo endereço gere possível duplicidade, e que candidato sem endereço inequívoco não seja publicado.

- [ ] **Step 2: Confirmar falha**

Run: `python3 -m unittest ferramentas.tests.test_pecs -v`
Expected: FAIL por fixture/função ausente.

- [ ] **Step 3: Curar candidatos oficiais recentes**

Registrar URL, data da publicação, trecho de localização, endereço normalizado e status. Não inferir coordenadas quando a publicação só nomear a região.

- [ ] **Step 4: Criar pedido de LAI**

Solicitar CSV/GeoJSON com identificador, endereço, coordenadas, RA, instalação, manutenção, conservação, iluminação, status, acessibilidade e processo SEI. Incluir período e formato preferencial; não enviar o pedido nesta tarefa.

- [ ] **Step 5: Atualizar o diagnóstico público**

Exibir “403 PECs georreferenciadas no cadastro aberto” e “mais de mil informadas pela Novacap em 04/11/2025”, com links e sem calcular cobertura exata a partir do termo “mais de mil”.

- [ ] **Step 6: Executar testes**

Run: `python3 -m unittest ferramentas.tests.test_pecs -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add data/curadoria/pecs_recentes.json data/curadoria/metricas.json ferramentas/tests/test_pecs.py docs/pedido-lai-novacap.md index.html
git commit -m "feat: document current PEC coverage and LAI request"
```

### Task 4: Locais confirmados de paradesporto

**Files:**
- Create: `data/curadoria/paradesporto.json`
- Create: `ferramentas/tests/test_paradesporto.py`
- Modify: `data/curadoria/fontes.json`
- Modify: `data/curadoria/revisao.json`

**Interfaces:**
- Consumes: modelo de evidência e deduplicação da Task 1.
- Produces: locais institucionais com modalidades por fonte/data; pendências de entidades sem local regular confirmado.

- [ ] **Step 1: Escrever testes falhos das regras institucionais**

Cobrir: competição pontual não vira sede; CETEFE tem endereço `organizacao`; modalidade do CPB tem evidência independente; UNIACE sem fonte de treino regular fica pendente; nenhum contato pessoal é aceito.

- [ ] **Step 2: Confirmar falha**

Run: `python3 -m unittest ferramentas.tests.test_paradesporto -v`
Expected: FAIL por dados/funções ausentes.

- [ ] **Step 3: Cadastrar CETEFE e locais CPB**

Incluir CETEFE/ENAP, UnB, CECAF/DIREF, escola e IFB quando a publicação institucional relacionar modalidade e endereço. Preservar a data da publicação e marcar horários antigos para revisão, sem apresentá-los como atuais.

- [ ] **Step 4: Registrar lacunas, não suposições**

UNIACE e Candangos entram em `revisao.json` com entidade, modalidade, fonte que comprova atividade e motivo `regular_training_address_unconfirmed`.

- [ ] **Step 5: Executar testes**

Run: `python3 -m unittest ferramentas.tests.test_paradesporto -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add data/curadoria/paradesporto.json data/curadoria/fontes.json data/curadoria/revisao.json ferramentas/tests/test_paradesporto.py
git commit -m "feat: curate sourced parasport venues"
```

### Task 5: Catálogo inicial de privados

**Files:**
- Create: `data/curadoria/privados.json`
- Create: `ferramentas/tests/test_privados.py`
- Modify: `data/curadoria/fontes.json`

**Interfaces:**
- Consumes: modelo/deduplicação da Task 1.
- Produces: estabelecimentos `ownership=private`, `access_rule`, modalidades e atributos declarados pela organização.

- [ ] **Step 1: Escrever testes falhos de inclusão e confiança**

Exigir site oficial, endereço e ao menos uma modalidade. Rejeitar candidato baseado só em diretório. Garantir que “tem piscina” não implique “piscina acessível”. Garantir que associação/day use desconhecido apareça como desconhecido.

- [ ] **Step 2: Confirmar falha**

Run: `python3 -m unittest ferramentas.tests.test_privados -v`
Expected: FAIL.

- [ ] **Step 3: Curar o catálogo inicial**

Incluir, quando confirmados em seus sites oficiais: Clube Naval, AABB Brasília, Minas Brasília, Clube da Aeronáutica e outros candidatos que satisfaçam o teste. Cada modalidade deve apontar para a fonte institucional.

- [ ] **Step 4: Executar testes**

Run: `python3 -m unittest ferramentas.tests.test_privados -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add data/curadoria/privados.json data/curadoria/fontes.json ferramentas/tests/test_privados.py
git commit -m "feat: add institution-sourced private sports venues"
```

### Task 6: Gerador, filtros e interface de evidência

**Files:**
- Create: `ferramentas/gerar_base.py`
- Create: `ferramentas/tests/test_gerar_base.py`
- Modify: `data/locais.js`
- Modify: `app.js`
- Modify: `index.html`
- Modify: `styles.css`

**Interfaces:**
- Consumes: arquivos curados das Tasks 1–5.
- Produces: `data/locais.js` com `ownership`, `reviewed_at`, `evidence` por atributo; filtros `origem` e `evidencia`; cartões e popups consistentes.

- [ ] **Step 1: Escrever teste falho do gerador**

Garantir IDs únicos, coordenadas válidas, fonte/data nos publicados, atributos independentes, métricas por origem e saída determinística.

- [ ] **Step 2: Confirmar falha**

Run: `python3 -m unittest ferramentas.tests.test_gerar_base -v`
Expected: FAIL por gerador ausente.

- [ ] **Step 3: Implementar o gerador**

Preservar compatibilidade com os campos atuais usados pelo mapa e adicionar os novos campos. Gerar primeiro em arquivo temporário e substituir apenas após validação sem erros.

- [ ] **Step 4: Implementar filtros e cartões**

Adicionar origem `public`, `private`, `social_organization`; níveis de evidência; “Atualizado/revisado em”; matriz de acessibilidade; divergências lado a lado; “ponto representativo” para parques.

- [ ] **Step 5: Escrever o teste funcional CDP**

Em `ferramentas/teste-curadoria.mjs`, testar: atributo oficial + acessibilidade desconhecida; filtro privado; filtro verificado em campo; parque representativo; Maps/Waze; ausência de erros de console.

- [ ] **Step 6: Executar testes unitários e funcionais**

Run: `python3 -m unittest ferramentas.tests.test_gerar_base -v`
Expected: PASS.

Run: `node ferramentas/teste-curadoria.mjs`
Expected: `TESTE_OK`, zero erros do navegador.

- [ ] **Step 7: Commit**

```bash
git add ferramentas/gerar_base.py ferramentas/tests/test_gerar_base.py ferramentas/teste-curadoria.mjs data/locais.js app.js index.html styles.css
git commit -m "feat: expose source confidence and ownership filters"
```

### Task 7: Contribuição comunitária e moderação local

**Files:**
- Create: `ferramentas/tests/test_contribuicoes.py`
- Modify: `app.js`
- Modify: `index.html`
- Modify: `styles.css`

**Interfaces:**
- Consumes: IDs e atributos de acessibilidade da Task 6.
- Produces: `CommunitySubmissionV1`; armazenamento `pontoativo.contribuicoes.v1`; exportação JSON; estados `draft` e `pending_review`.

- [ ] **Step 1: Escrever testes falhos da validação da contribuição**

Cobrir: consentimento obrigatório; opção “não consegui verificar”; ausência de foto aceita como pendente; foto não promove automaticamente; nenhum valor vira `campo`; validade de 12 meses só após moderação.

- [ ] **Step 2: Confirmar falha**

Run: `python3 -m unittest ferramentas.tests.test_contribuicoes -v`
Expected: FAIL.

- [ ] **Step 3: Implementar formulário acessível**

Campos objetivos para rota, entrada, circulação, banheiro, vaga, piso tátil, sinalização, equipamento adaptado e observações. Avisar para não fotografar rostos, placas ou documentos.

- [ ] **Step 4: Implementar armazenamento e exportação**

Salvar somente após ação explícita. Exibir que o envio fica neste navegador no protótipo. Permitir baixar JSON para moderação; não transmitir a terceiros.

- [ ] **Step 5: Implementar “Informar mudança” e “Verificar acessibilidade”**

Abrir o formulário com local e tipo de contribuição preenchidos. Incluir foco, teclado, mensagens de erro e alto contraste.

- [ ] **Step 6: Executar testes unitários e funcionais**

Run: `python3 -m unittest ferramentas.tests.test_contribuicoes -v`
Expected: PASS.

Run: `node ferramentas/teste-curadoria.mjs`
Expected: `TESTE_OK`, contribuição pendente e base publicada inalterada.

- [ ] **Step 7: Commit**

```bash
git add ferramentas/tests/test_contribuicoes.py app.js index.html styles.css
git commit -m "feat: add moderated accessibility contributions"
```

### Task 8: Relatório, documentação e verificação integrada

**Files:**
- Create: `docs/relatorio-cobertura.md`
- Modify: `ferramentas/LEIA-ME.md`
- Modify: `index.html`

**Interfaces:**
- Consumes: base e métricas de todas as tasks.
- Produces: relatório reproduzível e documentação de atualização.

- [ ] **Step 1: Gerar métricas antes/depois**

Reportar por categoria, origem, nível de evidência, coordenadas pendentes, idade da fonte e possíveis duplicidades. Não chamar “cobertura” a razão 403/1000, pois “mais de mil” não é denominador exato.

- [ ] **Step 2: Documentar reprodução e atualização**

Incluir comandos para importar Ibram, validar curadoria, gerar base e executar testes. Explicar como adicionar uma fonte e revisar contribuição.

- [ ] **Step 3: Atualizar a página de transparência**

Mostrar dados atuais, fontes, datas e lacunas remanescentes. Linkar o pedido de LAI como documento do projeto, sem afirmar que foi protocolado.

- [ ] **Step 4: Executar toda a suíte**

Run: `python3 -m unittest discover -s ferramentas/tests -v`
Expected: todos os testes PASS.

Run: `node --check app.js && python3 -m py_compile ferramentas/*.py`
Expected: exit 0.

Run: `node ferramentas/teste-campos.mjs && node ferramentas/teste-curadoria.mjs`
Expected: ambos `TESTE_OK`, zero erros de console.

- [ ] **Step 5: Auditar requisitos do desenho**

Confirmar os cinco critérios: PECs, acessibilidade, paradesporto, privados, parques/ginásio. Registrar lacunas reais no relatório, sem convertê-las em sucesso.

- [ ] **Step 6: Commit**

```bash
git add docs ferramentas/LEIA-ME.md index.html
git commit -m "docs: report multifonte coverage and remaining gaps"
```

---

## Verificação final

1. Executar todos os testes da Task 8 com saída fresca.
2. Comparar `data/locais.js` anterior e novo: totais, IDs removidos, duplicidades e pendências.
3. Inspecionar no desktop e em 375×812: filtros, cartões, modal de contribuição, teclado e contraste.
4. Confirmar que nenhum dado `organizacao`/`colaborativo` usa o rótulo “verificado”.
5. Revisar URLs e datas das fontes institucionais.
6. Fazer revisão integral contra o spec e classificar achados antes de corrigir.

