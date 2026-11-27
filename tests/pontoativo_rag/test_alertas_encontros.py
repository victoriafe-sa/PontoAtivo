from datetime import datetime, timedelta, timezone

import pytest

from pontoativo_rag.contas import Accounts
from pontoativo_rag.encontros import Meetings
from pontoativo_rag.persistencia import Database

PLACES = [{"id": "campo-1", "nome": "Campo 1", "regiao": "Ceilândia"}]


@pytest.fixture
def mundo(tmp_path):
    db = Database(tmp_path / "db.sqlite3")
    accounts = Accounts(db)
    ids = {}
    pessoas = [("ana", "mulher"), ("bia", "mulher"), ("caio", "homem"), ("davi", "homem"),
               ("edu", "homem"), ("fabi", "mulher"), ("gil", "")]
    for login, genero in pessoas:
        ids[login] = accounts.register({"login": login, "senha": "senha-segura-123", "apelido": login.title(),
                                        "idade": "25-34", "genero": genero})["id"]
    return db, Meetings(db, PLACES), ids


def grupo(meetings, quem, capacidade=6, dias=1):
    return meetings.criar_encontro(quem, {
        "local_id": "campo-1", "esporte": "Futebol", "nivel": "todos", "idade": "todos",
        "formato": "grupo", "capacidade": capacidade,
        "inicio": (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat(),
    })["id"]


def ver(meetings, evento, quem):
    return next(e for e in meetings.listar_encontros({}, quem) if e["id"] == evento)


def test_mulher_ve_alerta_em_grupo_de_desconhecidos_com_mais_homens(mundo):
    db, meetings, ids = mundo
    evento = grupo(meetings, ids["caio"])
    meetings.entrar(evento, ids["davi"])
    assert ver(meetings, evento, ids["ana"])["alerta_grupo"] is True
    # Homens e quem não informou o gênero não recebem esse alerta.
    assert ver(meetings, evento, ids["edu"])["alerta_grupo"] is False
    assert ver(meetings, evento, ids["gil"])["alerta_grupo"] is False
    # Sem conta, nenhum alerta pessoal.
    assert next(e for e in meetings.listar_encontros({}) if e["id"] == evento)["alerta_grupo"] is False


def test_sem_alerta_quando_ha_mulheres_suficientes(mundo):
    db, meetings, ids = mundo
    evento = grupo(meetings, ids["caio"])
    meetings.entrar(evento, ids["bia"])
    # Caio (homem) contra Bia + Ana (que está vendo): mais mulheres.
    assert ver(meetings, evento, ids["ana"])["alerta_grupo"] is False


def test_sem_alerta_em_grupos_pequenos(mundo):
    db, meetings, ids = mundo
    evento = grupo(meetings, ids["caio"], capacidade=4)
    meetings.entrar(evento, ids["davi"])
    assert ver(meetings, evento, ids["ana"])["alerta_grupo"] is False


def test_sem_alerta_se_ela_ja_praticou_com_alguem_do_grupo(mundo):
    db, meetings, ids = mundo
    antigo = grupo(meetings, ids["caio"])
    meetings.entrar(antigo, ids["ana"])
    with db.transaction() as conn:
        conn.execute("UPDATE events SET start=? WHERE id=?",
                     ((datetime.now(timezone.utc) - timedelta(days=3)).isoformat(), antigo))
    evento = grupo(meetings, ids["davi"])
    meetings.entrar(evento, ids["caio"])
    assert ver(meetings, evento, ids["ana"])["alerta_grupo"] is False


def test_alerta_nao_revela_generos(mundo):
    db, meetings, ids = mundo
    evento = grupo(meetings, ids["caio"])
    meetings.entrar(evento, ids["davi"])
    cartao = ver(meetings, evento, ids["ana"])
    texto = str(cartao)
    assert "homem" not in texto and "mulher" not in texto


SEGURANCA = {"ano": 2025, "regioes": {
    "Ceilândia": {"vezes_media_df": 2.13, "alerta": True},
    "Lago Sul": {"vezes_media_df": 0.4, "alerta": False},
    "Sol Nascente/Pôr do Sol": {"vezes_media_df": 1.6, "alerta": True},
}}


def test_alerta_de_regiao_usa_a_tabela_da_ssp(tmp_path):
    db = Database(tmp_path / "db.sqlite3")
    quem = Accounts(db).register({"login": "ana", "senha": "senha-segura-123", "apelido": "Ana", "idade": "25-34"})["id"]
    lugares = [{"id": "a", "nome": "COP Ceilândia", "regiao": "Ceilândia"},
               {"id": "b", "nome": "Lago", "regiao": "Lago Sul"},
               {"id": "c", "nome": "PEC", "regiao": "Sol Nascente"},
               {"id": "d", "nome": "Novo", "regiao": "Arapoanga"}]
    meetings = Meetings(db, lugares, seguranca=SEGURANCA)
    inicio = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    alerta = {}
    for lugar in lugares:
        e = meetings.criar_encontro(quem, {"local_id": lugar["id"], "esporte": "Corrida", "inicio": inicio,
                                           "nivel": "todos", "idade": "todos", "formato": "dupla"})
        alerta[lugar["regiao"]] = e["alerta_regiao"]
    assert alerta["Ceilândia"] == {"vezes_media_df": 2.13, "ano": 2025, "regiao": "Ceilândia"}
    assert alerta["Lago Sul"] is None          # abaixo do limiar
    assert alerta["Sol Nascente"]["regiao"] == "Sol Nascente/Pôr do Sol"  # nome do mapa diferente
    assert alerta["Arapoanga"] is None         # RA nova, sem dados da SSP


def test_sem_tabela_nao_ha_alerta_de_regiao(tmp_path):
    db = Database(tmp_path / "db.sqlite3")
    quem = Accounts(db).register({"login": "ana", "senha": "senha-segura-123", "apelido": "Ana", "idade": "25-34"})["id"]
    meetings = Meetings(db, [{"id": "a", "nome": "COP", "regiao": "Ceilândia"}])
    e = meetings.criar_encontro(quem, {"local_id": "a", "esporte": "Corrida", "nivel": "todos", "idade": "todos",
                                       "formato": "dupla", "inicio": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()})
    assert e["alerta_regiao"] is None


def test_tabela_versionada_tem_fonte_e_33_ras():
    import json
    from pathlib import Path
    dados = json.loads((Path(__file__).resolve().parents[2] / "dados/mapa/seguranca/seguranca_ras_2025.json").read_text(encoding="utf-8"))
    assert dados["ano"] == 2025 and len(dados["regioes"]) == 33
    assert "ssp.df.gov.br" in dados["fontes"]["crimes"]
    for r in dados["regioes"].values():
        assert r["alerta"] == (r["taxa_100mil"] >= 1.5 * dados["taxa_df_100mil"])
