# Avaliação do assistente (RAG)

O portão de qualidade roda as 18 perguntas de
[`dados/rag/perguntas/avaliacao.jsonl`](../../dados/rag/perguntas/avaliacao.jsonl)
(13 com resposta nas fontes e 5 sem) e confere se o assistente acha a fonte certa,
cita só trechos recuperados, não afirma nada sem apoio e se abstém quando deve.

```bash
.venv/bin/python -m pontoativo_rag.avaliacao --verificar-qualidade
```

Cada execução grava `avaliacao_<data>.md` e `.jsonl` nesta pasta; esses arquivos
ficam fora do Git. Quando uma rodada passa no portão e é revisada, ela vai para `atual/`.

| Pasta | Conteúdo |
|---|---|
| [`atual/`](atual/) | **Resultado oficial**: [E5 + Gemma 4 12B](atual/referencia_gemma12b_e5.md) e a [revisão humana](atual/revisao_humana_rag.md) (a refazer com o E5) |
| [`relatorios/`](relatorios/) | Relatórios das fases 3 (recuperação) e 4 (qualidade) e a comparação com e sem RAG |
| [`historico/`](historico/) | Rodadas anteriores, incluindo a [referência com o MiniLM](historico/referencia_gemma12b_minilm.md) |
