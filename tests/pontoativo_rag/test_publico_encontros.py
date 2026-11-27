import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from pontoativo_rag.contas import Accounts
from pontoativo_rag.encontros import Meetings
from pontoativo_rag.persistencia import ApiError, Database

PLACES = [{"id": "campo-1", "nome": "Campo 1", "regiao": "Ceilândia"}]


@pytest.fixture
def mundo(tmp_path):
    db = Database(tmp_path / "db.sqlite3")
    accounts = Accounts(db)
    ids = {}
    for login, genero in (("ana", "mulher"), ("beto", "homem"), ("cris", ""), ("dani", "outro")):
        ids[login] = accounts.register({"login": login, "senha": "senha-segura-123", "apelido": login.title(),
                                        "idade": "25-34", "genero": genero})["id"]
    return db, accounts, Meetings(db, PLACES), ids


def encontro(meetings, quem, publico="misto"):
    return meetings.criar_encontro(quem, {
        "local_id": "campo-1", "esporte": "Vôlei", "nivel": "todos", "idade": "todos",
        "formato": "grupo", "capacidade": 6, "publico": publico,
        "inicio": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    })


def test_genero_fica_na_conta_e_so_aparece_para_a_propria_pessoa(mundo):
    db, accounts, meetings, ids = mundo
    token, ana = accounts.login("ana", "senha-segura-123", "127.0.0.1")
    assert ana["genero"] == "mulher"
    assert accounts.current(token)["genero"] == "mulher"
    # O cartão do encontro não expõe o gênero de ninguém.
    evento = encontro(meetings, ids["ana"], "mulheres")
    assert "mulher" not in str({k: v for k, v in evento.items() if k != "publico"})


@pytest.mark.parametrize("genero", ["feminino", 3, ["mulher"]])
def test_genero_invalido_e_recusado(tmp_path, genero):
    accounts = Accounts(Database(tmp_path / "db.sqlite3"))
    with pytest.raises(ApiError) as erro:
        accounts.register({"login": "eva", "senha": "senha-segura-123", "apelido": "Eva", "idade": "25-34", "genero": genero})
    assert erro.value.status == 400


def test_genero_pode_ser_mudado_nas_preferencias(mundo):
    db, accounts, meetings, ids = mundo
    assert accounts.update_preferences(ids["cris"], {"esportes": [], "regiao": "", "genero": "mulher"})["genero"] == "mulher"
    # Sem o campo "genero", as preferências não apagam o gênero salvo.
    assert "genero" not in accounts.update_preferences(ids["cris"], {"esportes": ["Vôlei"], "regiao": ""})
    assert encontro(meetings, ids["cris"], "mulheres")["publico"] == "mulheres"


def test_so_mulheres_marcam_e_entram_em_encontro_so_para_mulheres(mundo):
    db, accounts, meetings, ids = mundo
    with pytest.raises(ApiError) as erro:
        encontro(meetings, ids["beto"], "mulheres")
    assert erro.value.status == 400
    evento = encontro(meetings, ids["ana"], "mulheres")
    assert evento["publico"] == "mulheres"
    for quem in ("beto", "cris", "dani"):  # homem, sem gênero informado e "outro"
        with pytest.raises(ApiError) as erro:
            meetings.entrar(evento["id"], ids[quem])
        assert erro.value.status == 403
    accounts.update_preferences(ids["cris"], {"esportes": [], "regiao": "", "genero": "mulher"})
    assert meetings.entrar(evento["id"], ids["cris"])["participando"]


def test_so_homens_e_misto(mundo):
    db, accounts, meetings, ids = mundo
    homens = encontro(meetings, ids["beto"], "homens")
    with pytest.raises(ApiError):
        meetings.entrar(homens["id"], ids["ana"])
    misto = encontro(meetings, ids["ana"])
    assert misto["publico"] == "misto"
    for quem in ("beto", "cris", "dani"):
        assert meetings.entrar(misto["id"], ids[quem])["participando"]


def test_publico_invalido_e_recusado(mundo):
    db, accounts, meetings, ids = mundo
    with pytest.raises(ApiError) as erro:
        encontro(meetings, ids["ana"], "criancas")
    assert erro.value.status == 400


def test_filtro_por_publico(mundo):
    db, accounts, meetings, ids = mundo
    encontro(meetings, ids["ana"], "mulheres")
    encontro(meetings, ids["beto"], "homens")
    encontro(meetings, ids["cris"])
    assert [e["publico"] for e in meetings.listar_encontros({"publico": "mulheres"})] == ["mulheres"]
    assert len(meetings.listar_encontros({})) == 3


def test_banco_antigo_ganha_as_colunas_novas(tmp_path):
    caminho = tmp_path / "antigo.sqlite3"
    with sqlite3.connect(caminho) as conn:
        conn.executescript("""
            CREATE TABLE users (id TEXT PRIMARY KEY, login TEXT UNIQUE NOT NULL,
                nickname TEXT NOT NULL, age TEXT NOT NULL, password TEXT NOT NULL);
            CREATE TABLE events (id TEXT PRIMARY KEY, organizer TEXT NOT NULL, place_id TEXT NOT NULL,
                sport TEXT NOT NULL, start TEXT NOT NULL, level TEXT NOT NULL, age TEXT NOT NULL,
                format TEXT NOT NULL, capacity INTEGER NOT NULL, cancelled INTEGER NOT NULL DEFAULT 0);
            INSERT INTO users VALUES ('u1', 'velha', 'Velha', '25-34', 'x');
            INSERT INTO events VALUES ('e1', 'u1', 'campo-1', 'Futebol', '2030-01-01T00:00:00+00:00',
                'todos', 'todos', 'grupo', 6, 0);
        """)
    db = Database(caminho)
    with db.transaction() as conn:
        assert conn.execute("SELECT gender FROM users").fetchone()[0] == ""
        assert conn.execute("SELECT audience FROM events").fetchone()[0] == "misto"


def test_exclusivos_somem_para_quem_nao_pode_entrar(mundo):
    db, accounts, meetings, ids = mundo
    mulheres = encontro(meetings, ids["ana"], "mulheres")["id"]
    homens = encontro(meetings, ids["beto"], "homens")["id"]
    misto = encontro(meetings, ids["cris"])["id"]
    ver = lambda quem: {e["id"] for e in meetings.listar_encontros({}, ids[quem] if quem else None)}
    assert ver("ana") == {mulheres, misto}
    assert ver("beto") == {homens, misto}
    assert ver("cris") == {misto} and ver("dani") == {misto}
    assert ver(None) == {mulheres, homens, misto}  # sem conta, todos aparecem
    # Na própria agenda, quem organizou continua vendo o seu.
    assert {e["id"] for e in meetings.listar_encontros({"meus": True}, ids["ana"])} == {mulheres}
