import json

import pytest

from pontoativo_rag.agentes.pesquisa import AgentePesquisa, main
from pontoativo_rag.recuperacao import RetrievedChunk


def _chunk(chunk_id, distance, **extra):
    return RetrievedChunk(
        chunk_id=chunk_id, source_id=extra.pop("source_id", "DOC-003"),
        title="Manual de Uso dos COPs", institution="SEL-DF",
        location="https://www.esporte.df.gov.br/manual", text=f"Texto do {chunk_id}.",
        distance=distance, matched_segments=1, page_number=5, section="7. Faltas",
        **extra,
    )


class Buscador:
    def __init__(self, chunks):
        self.chunks = chunks
        self.chamadas = []

    def search(self, question, top_k=None, filters=None):
        self.chamadas.append((question, top_k, filters))
        return list(self.chunks)


def _agente(chunks):
    buscador = Buscador(chunks)
    return AgentePesquisa(buscador, max_distance=0.12, distance_scale=0.12 / 0.45, top_k=4), buscador


def test_devolve_trechos_dentro_do_limiar_com_a_fonte_e_ids_para_citar():
    agente, buscador = _agente([_chunk("c1", 0.05), _chunk("c2", 0.10), _chunk("c3", 0.30)])

    saida = agente.executar({"consulta": "  faltas graves no COP ", "tipo": "buscar_regra"})

    assert saida["status"] == "encontrado"
    assert [t["id"] for t in saida["trechos"]] == ["T1", "T2"]
    assert saida["descartados"] == 1
    fonte = saida["trechos"][0]["fonte"]
    assert fonte["id"] == "DOC-003" and fonte["paginas"] == "5" and fonte["url"].startswith("https://")
    assert saida["acao"]["consulta"] == "faltas graves no COP" and saida["acao"]["tipo"] == "buscar_regra"
    assert buscador.chamadas == [("faltas graves no COP", 4, None)]
    json.dumps(saida)  # a mensagem precisa ser JSON para os outros agentes


def test_busca_sem_evidencia_explica_o_motivo():
    agente, _ = _agente([_chunk("c1", 0.40), _chunk("c2", 0.55)])

    saida = agente.executar({"consulta": "previsão do tempo amanhã"})

    assert saida["status"] == "sem_evidencia" and saida["trechos"] == []
    assert "0.400" in saida["motivo"] and saida["descartados"] == 2


def test_busca_vazia_tambem_e_sem_evidencia():
    agente, _ = _agente([])
    saida = agente.executar({"consulta": "qualquer coisa"})
    assert saida["status"] == "sem_evidencia" and saida["motivo"] == "A busca não retornou nenhum trecho."


def test_usa_a_mesma_regra_do_gerador_para_trecho_perto_do_limiar():
    # Fora do limiar, mas com muitas palavras da consulta: o gerador aceitaria.
    agente, _ = _agente([_chunk("c1", 0.15, lexical_overlap=0.8), _chunk("c2", 0.15)])
    saida = agente.executar({"consulta": "faltas graves"})
    assert [t["texto"] for t in saida["trechos"]] == ["Texto do c1."]


def test_regiao_vira_filtro_da_busca():
    agente, buscador = _agente([_chunk("c1", 0.05)])
    agente.executar({"consulta": "natação", "regiao": "Ceilândia"})
    assert buscador.chamadas[0][2] == {"administrative_region": "Ceilândia"}


@pytest.mark.parametrize("acao", [None, {}, {"consulta": "  "}, {"consulta": "x", "regiao": 3}])
def test_acao_invalida_e_recusada(acao):
    agente, _ = _agente([])
    with pytest.raises(ValueError):
        agente.executar(acao)


def test_linha_de_comando_grava_o_resultado(tmp_path, monkeypatch):
    agente, _ = _agente([_chunk("c1", 0.05)])
    monkeypatch.setattr("pontoativo_rag.agentes.pesquisa.criar_agente", lambda: agente)
    acao = tmp_path / "acao.json"
    acao.write_text(json.dumps({"consulta": "faltas graves"}), encoding="utf-8")
    saida = tmp_path / "saida.json"

    assert main(["--acao", str(acao), "--saida", str(saida)]) == 0
    assert json.loads(saida.read_text(encoding="utf-8"))["trechos"][0]["fonte"]["id"] == "DOC-003"
