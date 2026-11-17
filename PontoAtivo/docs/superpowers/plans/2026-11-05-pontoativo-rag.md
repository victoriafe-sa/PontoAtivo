# PontoAtivo RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar um protótipo RAG de terminal, modular, testado e auditável para consultar fontes reais sobre atividade física e espaços esportivos do Distrito Federal.

**Architecture:** A ingestão transforma fontes catalogadas em documentos normalizados, chunks-pai citáveis e segmentos curtos de embedding persistidos no ChromaDB. A consulta recupera segmentos, agrega por chunk-pai e fornece o contexto a um gerador Ollama configurável, com fallback explícito de recuperação sem geração.

**Tech Stack:** Python 3.11, PyPDF, Beautiful Soup, Sentence Transformers, ChromaDB, HTTPX, python-dotenv e Pytest.

**Spec:** `docs/superpowers/specs/2026-11-05-pontoativo-rag-design.md`

## Global Constraints

- Usar Python 3.11 e caminhos relativos ao projeto.
- Usar `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` para documentos e perguntas.
- Manter chunks-pai em torno de 450 tokens, sobreposição de 50 tokens e segmentos de embedding de no máximo 120 tokens.
- Nunca inventar fatos, fontes, resultados, métricas ou disponibilidade de espaços.
- Não incluir login, reservas, pagamentos, rede social, gamificação ou interface web.
- Não exigir Ollama para o modo de diagnóstico.

## Review Focus

- PDF digitalizado sem texto deve ser relatado, não silenciosamente ingerido.
- Fonte duplicada por checksum deve ser ignorada sem duplicar chunks.
- Metadados ausentes não podem derrubar a consulta nem ativar filtros excludentes indevidos.
- Pergunta sem evidência suficiente deve causar abstenção, não resposta inventada.
- Instruções maliciosas dentro de documentos devem permanecer delimitadas como dados.

---

### Task 1: Fundação executável e diagnóstico

**Files:**
- Create: `.python-version`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`
- Create: `src/pontoativo_rag/__init__.py`, `src/pontoativo_rag/configuracao.py`, `src/pontoativo_rag/diagnostico.py`
- Create: `tests/test_configuracao.py`, `tests/test_diagnostico.py`, `pyproject.toml`

**Interfaces:**
- Produces: `Settings.from_env(root: Path | None = None) -> Settings`; `run_diagnostics(settings: Settings) -> DiagnosticReport`; `python -m pontoativo_rag.diagnostico`.

- [x] Escrever testes para defaults, criação explícita de diretórios e relatório de dependências/Ollama indisponível.
- [x] Executar os testes e confirmar falha por módulos ausentes.
- [x] Implementar configuração imutável e diagnóstico sem importar dependências pesadas antecipadamente.
- [x] Criar ambiente Python 3.11, instalar o pacote em modo editável e executar testes.
- [x] Documentar comandos PowerShell e Unix e registrar o diagnóstico real.

### Task 2: Catálogo, extração e normalização

**Files:**
- Create: `dados/catalogo_fontes.csv`, `src/pontoativo_rag/modelos.py`, `src/pontoativo_rag/carregamento.py`, `src/pontoativo_rag/processamento.py`
- Create: `tests/fixtures/`, `tests/test_carregamento.py`, `tests/test_processamento.py`

**Interfaces:**
- Consumes: `Settings`.
- Produces: `SourceRecord`, `NormalizedDocument`, `load_document(path, source)`, `normalize_text(text)`, `deduplicate_documents(documents)`.

- [x] Testar TXT, Markdown, HTML, PDF textual, vazio, PDF sem texto e duplicação por checksum.
- [x] Implementar modelos e leitores com erros por documento, sem interromper o lote.
- [x] Persistir documentos normalizados em JSONL e validar o catálogo.
- [x] Executar testes unitários e uma ingestão de fixtures.

### Task 3: Chunking hierárquico

**Files:**
- Modify: `src/pontoativo_rag/modelos.py`, `src/pontoativo_rag/processamento.py`
- Create: `tests/test_chunking.py`, `documentacao/estrategia_chunking.md`

**Interfaces:**
- Produces: `create_parent_chunks(document, target_tokens=450, overlap_tokens=50)` e `create_embedding_segments(chunk, max_tokens=120)`.

- [x] Testar documento curto, parágrafos longos, sobreposição, IDs estáveis e preservação de página/seção.
- [x] Implementar contagem determinística aproximada e segmentação hierárquica.
- [x] Gravar `dados/chunks.jsonl` e documentar a razão da hierarquia.

### Task 4: Embeddings e ChromaDB

**Files:**
- Create: `src/pontoativo_rag/embeddings.py`, `src/pontoativo_rag/armazenamento.py`
- Create: `tests/test_embeddings.py`, `tests/test_armazenamento.py`, `documentacao/estrategia_embeddings.md`

**Interfaces:**
- Produces: `EmbeddingProvider.encode(texts)`, `ChromaStore.upsert(segments)`, `ChromaStore.query(vector, n_results, filters)`.

- [x] Testar lotes e modelo único com provedor falso; testar persistência, metadados e upsert idempotente em diretório temporário.
- [x] Implementar carregamento tardio do Sentence Transformer e coleção cosseno persistente.
- [x] Executar teste de integração real, baixando o modelo somente quando autorizado/disponível.

### Task 5: Ingestão e recuperação

**Files:**
- Create: `src/pontoativo_rag/ingestao.py`, `src/pontoativo_rag/recuperacao.py`
- Create: `tests/test_ingestao.py`, `tests/test_recuperacao.py`, `documentacao/pipeline.md`

**Interfaces:**
- Produces: CLI `python -m pontoativo_rag.ingestao`; `Retriever.search(question, top_k=5, filters=None) -> list[RetrievedChunk]`.

- [ ] Testar pipeline idempotente, agregação de segmentos por pai, ordenação por menor distância e filtros opcionais.
- [ ] Implementar CLI com resumo de documentos aceitos, rejeitados, chunks e erros.
- [ ] Documentar pipeline e executar ingestão real das fontes disponíveis.

### Task 6: Geração segura e consulta interativa

**Files:**
- Create: `src/pontoativo_rag/geracao.py`, `src/pontoativo_rag/consulta.py`
- Create: `tests/test_geracao.py`, `tests/test_consulta.py`

**Interfaces:**
- Produces: `AnswerGenerator.generate(question, chunks) -> GroundedAnswer`; CLI `python -m pontoativo_rag.consulta`.

- [ ] Testar prompt delimitado, citações válidas, abstenção e fallback quando Ollama falhar.
- [ ] Implementar cliente HTTP do Ollama com modelo/URL/timeout configuráveis.
- [ ] Implementar ciclo de perguntas em português e encerramento seguro.

### Task 7: Curadoria de 20 fontes reais

**Files:**
- Modify: `dados/catalogo_fontes.csv`
- Create: `fontes_originais/`, `documentacao/criterios_fontes.md`

**Interfaces:**
- Produces: pelo menos 20 registros distintos com origem, instituição, tipo, datas, assunto, verificação e checksum.

- [ ] Selecionar fontes primárias/oficiais e separar fontes secundárias justificadas.
- [ ] Baixar snapshots ou documentos, calcular integridade e rejeitar propostas que não comprovem existência.
- [ ] Validar quantidade real, diversidade, duplicatas e legibilidade.

### Task 8: Avaliação, evidências e documentação final

**Files:**
- Create: `src/pontoativo_rag/avaliacao.py`, `dados/perguntas_avaliacao.jsonl`, `tests/test_avaliacao.py`
- Create: `documentacao/arquitetura.md`, `documentacao/relatorio_tecnico.md`, `evidencias/README.md`
- Modify: `README.md`

**Interfaces:**
- Produces: CLI de avaliação, dez perguntas compatíveis com a base e relatório JSONL de execuções reais.

- [ ] Testar Recall@k, validade de citações e detecção de ausência de evidência.
- [ ] Executar dez perguntas reais e registrar duração, recuperados e resposta sem fabricar métricas.
- [ ] Completar diagramas Mermaid, limitações, status dos critérios e instruções PowerShell reproduzíveis.
- [ ] Executar toda a suíte e o fluxo fim a fim; registrar saídas reais.
