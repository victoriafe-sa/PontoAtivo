import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from pontoativo_rag.persistencia import Database, ApiError
from pontoativo_rag.contas import Accounts
from pontoativo_rag.encontros import Meetings


@pytest.fixture
def app(tmp_path):
    db = Database(tmp_path / "encontros.sqlite3")
    accounts = Accounts(db)
    users = [
        accounts.register({"login": f"pessoa{i}", "senha": "senha-segura-123", "apelido": f"Pessoa {i}", "idade": age})
        for i, age in enumerate(["25-34", "25-34", "25-34", "60+"])
    ]
    meetings = Meetings(db, [{"id": "campo-1", "nome": "Campo 1", "regiao": "Ceilândia"}])
    return db, accounts, meetings, users


def event(**extra):
    return {
        "local_id": "campo-1", "esporte": "Futebol",
        "inicio": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "nivel": "iniciante", "idade": "todos", "formato": "dupla", **extra,
    }


def test_dupla_concorrente_saida_reentrada_e_persistencia(app):
    db, _, meetings, users = app
    created = meetings.criar_encontro(users[0]["id"], event())
    def join(user):
        try:
            meetings.entrar(created["id"], user["id"])
            return "entrou"
        except ApiError as error:
            return error.status
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(join, users[1:3]), key=str) == [409, "entrou"]
    current = meetings.listar_encontros({}, users[0]["id"])[0]
    assert current["vagas"] == 0
    winner = next(u for u in users[1:3] if meetings.listar_encontros({"meus": True}, u["id"]))
    assert meetings.entrar(created["id"], winner["id"])["vagas"] == 0
    meetings.sair(created["id"], winner["id"])
    assert meetings.listar_encontros({})[0]["vagas"] == 1
    meetings.entrar(created["id"], winner["id"])
    reopened = Meetings(Database(db.path), list(meetings.places.values()))
    assert reopened.listar_encontros({})[0]["vagas"] == 0
    with pytest.raises(ApiError, match="organizou"):
        meetings.cancelar(created["id"], winner["id"])
    meetings.cancelar(created["id"], users[0]["id"])
    assert meetings.listar_encontros({}) == []
    assert meetings.listar_encontros({"meus": True}, winner["id"])[0]["estado"] == "cancelado"
    with pytest.raises(ApiError):
        meetings.entrar(created["id"], users[2]["id"])


@pytest.mark.parametrize("patch", [
    {"local_id": "inexistente"}, {"esporte": ""},
    {"inicio": "2020-01-01T10:00:00-03:00"}, {"inicio": "2030-01-01T10:00"},
    {"formato": "grupo", "capacidade": 3}, {"formato": "grupo", "capacidade": 21},
    {"nivel": "outro"}, {"idade": "menor"},
])
def test_validacao(app, patch):
    _, _, meetings, users = app
    with pytest.raises(ApiError):
        meetings.criar_encontro(users[0]["id"], event(**patch))


def test_faixa_etaria_e_filtros(app):
    _, _, meetings, users = app
    created = meetings.criar_encontro(users[0]["id"], event(idade="25-34"))
    with pytest.raises(ApiError, match="etária"):
        meetings.entrar(created["id"], users[3]["id"])
    assert len(meetings.listar_encontros({"regiao": "Ceilândia", "esporte": "Futebol", "idade": "25-34"})) == 1
    assert meetings.listar_encontros({"regiao": "Guará"}) == []
    assert meetings.listar_encontros({"nivel": "avancado"}) == []
    assert meetings.listar_encontros({"data": "2020-01-01"}) == []
    with pytest.raises(ApiError):
        meetings.sair(created["id"], users[0]["id"])


def test_contas_sessoes_privacidade_e_limite(app):
    db, accounts, meetings, users = app
    token, user = accounts.login("pessoa0", "senha-segura-123", "ip")
    assert accounts.current(token) == user
    assert "senha" not in str(user) and "login" not in user
    accounts.logout(token)
    assert accounts.current(token) is None
    with db.transaction() as connection:
        row = connection.execute("SELECT password FROM users LIMIT 1").fetchone()
        assert "senha-segura" not in row["password"]
    with pytest.raises(ApiError):
        accounts.register({"login": "pessoa0", "senha": "senha-segura-123", "apelido": "Outro", "idade": "25-34"})
    with pytest.raises(ApiError):
        accounts.register({"login": "menor", "senha": "senha-segura-123", "apelido": "Menor", "idade": "17"})
    for _ in range(5):
        with pytest.raises(ApiError) as error:
            accounts.login("pessoa0", "errada", "outro-ip")
        assert error.value.status == 401
    with pytest.raises(ApiError) as error:
        accounts.login("pessoa0", "senha-segura-123", "outro-ip")
    assert error.value.status == 429
    token, _ = accounts.login("pessoa1", "senha-segura-123", "ip")
    with db.transaction() as connection:
        connection.execute("UPDATE sessions SET expires=0")
    assert accounts.current(token) is None


def test_repetir_publicacao_nao_duplica_encontro(app):
    _, _, meetings, users = app
    payload = event(request_id="pedido-teste-123")
    first = meetings.criar_encontro(users[0]["id"], payload)
    repeated = meetings.criar_encontro(users[0]["id"], payload)
    assert first["id"] == repeated["id"]
    assert len(meetings.listar_encontros({})) == 1
    with pytest.raises(ApiError):
        meetings.criar_encontro(users[0]["id"], {**payload, "esporte": "Basquete"})


@pytest.mark.parametrize(("formato", "capacidade", "expected"), [
    ("dupla", 20, 2), ("trio", 20, 3), ("grupo", 4, 4), ("grupo", 20, 20),
])
def test_capacidade_inclui_organizador(app, formato, capacidade, expected):
    _, _, meetings, users = app
    created = meetings.criar_encontro(users[0]["id"], event(formato=formato, capacidade=capacidade))
    assert created["capacidade"] == expected
    assert created["participantes"] == 1
    assert created["vagas"] == expected - 1


def test_filtro_de_data_usa_brasilia(app):
    _, _, meetings, users = app
    meetings.criar_encontro(users[0]["id"], event(inicio="2099-01-02T02:30:00+00:00"))
    assert len(meetings.listar_encontros({"data": "2099-01-01"})) == 1
    assert meetings.listar_encontros({"data": "2099-01-02"}) == []


def test_filtro_de_faixa_inclui_encontros_para_todos_os_adultos(app):
    _, _, meetings, users = app
    aberto = meetings.criar_encontro(users[0]["id"], event(idade="todos"))
    faixa = meetings.criar_encontro(users[1]["id"], event(idade="25-34"))
    meetings.criar_encontro(users[3]["id"], event(idade="60+"))

    def ids(filtro):
        return {item["id"] for item in meetings.listar_encontros({"idade": filtro})}

    assert ids("25-34") == {aberto["id"], faixa["id"]}
    assert ids("todos") == {aberto["id"]}


@pytest.mark.parametrize(
    ("dados", "mensagem"),
    [
        ({"apelido": "Rei do Sexo"}, 'apelido tem um termo impróprio ("Sexo")'),
        ({"apelido": "pu7aria total"}, 'apelido tem um termo impróprio ("pu7aria")'),
        ({"login": "viado.fc"}, 'usuário tem um termo impróprio ("viado")'),
    ],
)
def test_cadastro_recusa_apelido_ou_usuario_improprio(app, dados, mensagem):
    db, accounts, _, _ = app
    base = {"login": "novo.usuario", "senha": "senha-segura-123", "apelido": "Novo", "idade": "25-34"}

    with pytest.raises(ApiError, match=re.escape(mensagem)) as erro:
        accounts.register({**base, **dados})

    assert erro.value.status == 400
    with db.transaction() as conn:
        assert conn.execute("SELECT count(*) FROM users WHERE login=?", (base.get("login"),)).fetchone()[0] == 0


@pytest.mark.parametrize("apelido", ["Sexta do Vôlei", "Ana Disputa", "Pedro Transporte", "Maria (teste)"])
def test_cadastro_aceita_apelidos_comuns(app, apelido):
    _, accounts, _, _ = app
    criado = accounts.register({"login": "comum." + str(abs(hash(apelido)) % 10000), "senha": "senha-segura-123",
                                "apelido": apelido, "idade": "25-34"})
    assert criado["apelido"] == apelido


def _conta(accounts, login, **prefs):
    return accounts.register({"login": login, "senha": "senha-segura-123", "apelido": login, "idade": "25-34", **prefs})


def test_cadastro_guarda_preferencias_opcionais(tmp_path):
    accounts = Accounts(Database(tmp_path / "p.sqlite3"), regions={"Guará", "Gama"})

    sem = _conta(accounts, "semprefs")
    com = _conta(accounts, "comprefs", esportes=["Vôlei", "Corrida", "Vôlei"], regiao="Guará")
    token, logado = accounts.login("comprefs", "senha-segura-123", "1.1.1.1")

    assert sem["preferencias"] == {"esportes": [], "regiao": ""}
    assert com["preferencias"] == {"esportes": ["Vôlei", "Corrida"], "regiao": "Guará"}
    assert logado["preferencias"] == com["preferencias"]
    assert accounts.current(token)["preferencias"] == com["preferencias"]


@pytest.mark.parametrize("prefs", [
    {"esportes": ["Xadrez"]},
    {"esportes": "Futebol,Vôlei"},
    {"esportes": ["Futebol", "Futsal", "Vôlei", "Basquete", "Tênis", "Corrida"]},
    {"esportes": [1]},
    {"regiao": "Atlântida"},
    {"regiao": 3},
])
def test_preferencias_invalidas_sao_recusadas(tmp_path, prefs):
    accounts = Accounts(Database(tmp_path / "p.sqlite3"), regions={"Guará"})

    with pytest.raises(ApiError) as error:
        _conta(accounts, "pessoa", **prefs)

    assert error.value.status == 400


def test_preferencias_podem_ser_editadas_e_apagadas(tmp_path):
    accounts = Accounts(Database(tmp_path / "p.sqlite3"), regions={"Gama"})
    user = _conta(accounts, "pessoa", esportes=["Skate"])

    accounts.update_preferences(user["id"], {"esportes": ["Natação"], "regiao": "Gama"})
    token, _ = accounts.login("pessoa", "senha-segura-123", "1.1.1.1")
    assert accounts.current(token)["preferencias"] == {"esportes": ["Natação"], "regiao": "Gama"}

    accounts.update_preferences(user["id"], {"esportes": [], "regiao": ""})
    assert accounts.current(token)["preferencias"] == {"esportes": [], "regiao": ""}
