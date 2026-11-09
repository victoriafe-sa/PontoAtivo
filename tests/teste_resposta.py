"""A resposta deve conter evidência exata e rastreabilidade sem inventar fatos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from geracao.responder import responder
from ingestao.chunking import chunkar_pasta

chunks, _ = chunkar_pasta(Path(__file__).resolve().parents[1] / "dados/fontes/texto")
resultados = [{"id": c["id"], "texto": c["texto"], "metadados": c["metadados"]} for c in chunks[:5]]
resposta = responder(resultados)
for r in resultados[:3]:
    assert r["texto"] in resposta
    for campo in ("link", "titulo", "data_coleta", "ressalvas"):
        assert r["metadados"][campo] in resposta
    assert f"[{r['id']}]" in resposta
assert f"[{resultados[3]['id']}]" not in resposta
assert "Não há evidências" in responder([])
assert "não garante" in resposta
print("OK: texto exato, IDs, fontes, datas, ressalvas, limite de 3 chunks e caso vazio.")
