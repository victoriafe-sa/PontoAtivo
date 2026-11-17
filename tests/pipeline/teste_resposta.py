"""A resposta deve conter evidência exata e rastreabilidade sem inventar fatos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from geracao.responder import responder
from ingestao.chunking import chunkar_pasta


def test_resposta_preserva_trechos_e_fontes():
    chunks, _ = chunkar_pasta(Path(__file__).resolve().parents[2] / "dados/fontes/texto")
    resultados = [{"id": c["id"], "texto": c["texto"], "metadados": c["metadados"]} for c in chunks[:5]]
    resposta = responder(resultados)
    for r in resultados[:3]:
        assert r["texto"] in resposta
        for campo in ("link", "titulo", "data_coleta", "ressalvas"):
            assert r["metadados"][campo] in resposta
        assert f"[{r['id']}]" in resposta
    assert f"[{resultados[3]['id']}]" not in resposta
    assert "não garante" in resposta


def test_resposta_sem_evidencias():
    assert "Não há evidências" in responder([])


if __name__ == "__main__":
    test_resposta_preserva_trechos_e_fontes()
    test_resposta_sem_evidencias()
