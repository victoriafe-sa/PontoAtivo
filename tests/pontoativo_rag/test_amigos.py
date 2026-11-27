from datetime import datetime, timedelta, timezone
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread

import httpx
import pytest

from pontoativo_rag.amigos import Amigos
from pontoativo_rag.contas import Accounts
from pontoativo_rag.encontros import Meetings
from pontoativo_rag.persistencia import ApiError, Database
from pontoativo_rag.web import Handler

PLACES = [{"id": "campo-1", "nome": "Campo 1", "regiao": "Ceilândia"}]


@pytest.fixture
def mundo(tmp_path):
    db = Database(tmp_path / "db.sqlite3")
    accounts = Accounts(db)
    meetings = Meetings(db, PLACES)
    ids = {}
    for login in ("ana", "beto", "caio"):
        ids[login] = accounts.register({"login": login, "senha": "senha-segura-123", "apelido": login.title(), "idade": "25-34"})["id"]
    return db, meetings, Amigos(db), ids


def encontro(meetings, organizador, inicio=None):
    inicio = inicio or datetime.now(timezone.utc) + timedelta(days=1)
    return meetings.criar_encontro(organizador, {
        "local_id": "campo-1", "esporte": "Futebol", "inicio": inicio.isoformat(),
        "nivel": "todos", "idade": "todos", "formato": "grupo", "capacidade": 6,
    })["id"]


def realizar(db, event_id):
    """Põe o encontro no passado, como se já tivesse acontecido."""
    with db.transaction() as conn:
        conn.execute("UPDATE events SET start=? WHERE id=?",
                     ((datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(), event_id))


def praticaram(db, meetings, quem, *outros):
    event_id = encontro(meetings, quem)
    for outro in outros:
        meetings.entrar(event_id, outro)
    realizar(db, event_id)
    return event_id


def test_so_quem_praticou_junto_pode_pedir_amizade_ou_avaliar(mundo):
    db, meetings, amigos, ids = mundo
    with pytest.raises(ApiError) as erro:
        amigos.pedir(ids["ana"], ids["beto"])
    assert erro.value.status == 403
    # Encontro futuro ainda não conta.
    futuro = encontro(meetings, ids["ana"])
    meetings.entrar(futuro, ids["beto"])
    with pytest.raises(ApiError):
        amigos.avaliar(ids["ana"], ids["beto"], 1)
    realizar(db, futuro)
    assert amigos.pedir(ids["ana"], ids["beto"]) == {"amizade": "pedido_enviado"}
    with pytest.raises(ApiError):
        amigos.pedir(ids["ana"], ids["ana"])


def test_encontro_cancelado_nao_conta_como_pratica(mundo):
    db, meetings, amigos, ids = mundo
    event_id = encontro(meetings, ids["ana"])
    meetings.entrar(event_id, ids["beto"])
    meetings.cancelar(event_id, ids["ana"])
    realizar(db, event_id)
    assert amigos.resumo(ids["ana"])["pessoas"] == []


def test_pedido_aceito_vira_amizade_dos_dois_lados(mundo):
    db, meetings, amigos, ids = mundo
    praticaram(db, meetings, ids["ana"], ids["beto"])
    amigos.pedir(ids["ana"], ids["beto"])
    beto = amigos.resumo(ids["beto"])
    assert [p["apelido"] for p in beto["pedidos"]] == ["Ana"]
    assert beto["pessoas"][0]["amizade"] == "pedido_recebido"
    assert amigos.aceitar(ids["beto"], ids["ana"]) == {"amizade": "amigos"}
    assert [p["apelido"] for p in amigos.resumo(ids["ana"])["amigos"]] == ["Beto"]
    assert [p["apelido"] for p in amigos.resumo(ids["beto"])["amigos"]] == ["Ana"]
    amigos.remover(ids["beto"], ids["ana"])
    assert amigos.resumo(ids["ana"])["amigos"] == []


def test_pedidos_cruzados_viram_amizade_na_hora(mundo):
    db, meetings, amigos, ids = mundo
    praticaram(db, meetings, ids["ana"], ids["beto"])
    amigos.pedir(ids["ana"], ids["beto"])
    assert amigos.pedir(ids["beto"], ids["ana"]) == {"amizade": "amigos"}


def test_quem_pediu_nao_pode_aceitar_o_proprio_pedido(mundo):
    db, meetings, amigos, ids = mundo
    praticaram(db, meetings, ids["ana"], ids["beto"])
    amigos.pedir(ids["ana"], ids["beto"])
    with pytest.raises(ApiError) as erro:
        amigos.aceitar(ids["ana"], ids["beto"])
    assert erro.value.status == 404


def test_nota_em_estrelas_e_anonima_e_so_aparece_com_3_notas(mundo):
    db, meetings, amigos, ids = mundo
    praticaram(db, meetings, ids["ana"], ids["beto"], ids["caio"])
    amigos.avaliar(ids["beto"], ids["ana"], 5)
    amigos.avaliar(ids["caio"], ids["ana"], 2)
    ana = amigos.resumo(ids["ana"])
    # Com 2 notas a média ainda não aparece: daria para adivinhar quem deu cada uma.
    assert ana["reputacao"] == {"nota": None, "total": 2, "minimo": 3}
    for pessoa in ana["pessoas"]:
        assert pessoa["minha_nota"] == 0  # a Ana não avaliou ninguém
    # Mudar e apagar a própria nota.
    amigos.avaliar(ids["caio"], ids["ana"], 4)
    amigos.avaliar(ids["caio"], ids["ana"], 0)
    assert amigos.resumo(ids["ana"])["reputacao"]["total"] == 1
    assert {p["apelido"]: p["minha_nota"] for p in amigos.resumo(ids["beto"])["pessoas"]}["Ana"] == 5


def test_media_aparece_com_3_notas_e_nunca_diz_quem_deu(mundo):
    db, meetings, amigos, ids = mundo
    dani = Accounts(db).register({"login": "dani", "senha": "senha-segura-123", "apelido": "Dani", "idade": "25-34"})["id"]
    praticaram(db, meetings, ids["ana"], ids["beto"], ids["caio"], dani)
    for quem, nota in ((ids["beto"], 5), (ids["caio"], 4), (dani, 3)):
        amigos.avaliar(quem, ids["ana"], nota)
    rep = amigos.resumo(ids["ana"])["reputacao"]
    assert rep == {"nota": {"media": 4.0, "total": 3}, "total": 3, "minimo": 3}
    # A média aparece no cartão do encontro que a Ana organiza.
    novo = encontro(meetings, ids["ana"])
    cartao = next(e for e in meetings.listar_encontros({}, ids["beto"]) if e["id"] == novo)
    assert cartao["organizador_nota"] == {"media": 4.0, "total": 3}
    assert all(i not in str(cartao) for i in (ids["beto"], ids["caio"], dani))


@pytest.mark.parametrize("nota", [6, -1, "3", None, True, 2.5])
def test_nota_invalida_e_recusada(mundo, nota):
    db, meetings, amigos, ids = mundo
    praticaram(db, meetings, ids["ana"], ids["beto"])
    with pytest.raises(ApiError) as erro:
        amigos.avaliar(ids["ana"], ids["beto"], nota)
    assert erro.value.status == 400


def test_encontro_mostra_os_amigos_que_vao(mundo):
    db, meetings, amigos, ids = mundo
    praticaram(db, meetings, ids["ana"], ids["beto"])
    amigos.pedir(ids["ana"], ids["beto"])
    amigos.aceitar(ids["beto"], ids["ana"])
    novo = encontro(meetings, ids["caio"])
    meetings.entrar(novo, ids["beto"])
    ver = lambda quem: next(e for e in meetings.listar_encontros({}, quem) if e["id"] == novo)
    assert ver(ids["ana"])["amigos"] == ["Beto"]
    assert ver(ids["caio"])["amigos"] == []  # Caio não é amigo do Beto
    assert next(e for e in meetings.listar_encontros({}) if e["id"] == novo)["amigos"] == []


def test_bloqueio_desfaz_amizade_esconde_e_impede_encontros(mundo):
    db, meetings, amigos, ids = mundo
    praticaram(db, meetings, ids["ana"], ids["beto"])
    amigos.pedir(ids["ana"], ids["beto"])
    amigos.aceitar(ids["beto"], ids["ana"])
    amigos.bloquear(ids["ana"], ids["beto"])
    ana = amigos.resumo(ids["ana"])
    assert ana["amigos"] == [] and ana["pessoas"] == []
    assert [p["apelido"] for p in ana["bloqueados"]] == ["Beto"]
    beto = amigos.resumo(ids["beto"])
    assert beto["amigos"] == [] and beto["pessoas"] == [] and beto["bloqueados"] == []
    with pytest.raises(ApiError):
        amigos.pedir(ids["beto"], ids["ana"])
    # Beto não vê nem entra nos encontros da Ana, e vice-versa.
    novo = encontro(meetings, ids["ana"])
    assert all(e["id"] != novo for e in meetings.listar_encontros({}, ids["beto"]))
    with pytest.raises(ApiError) as erro:
        meetings.entrar(novo, ids["beto"])
    assert erro.value.status == 403
    # Caio, sem bloqueio, continua entrando.
    assert meetings.entrar(novo, ids["caio"])["participando"]
    amigos.desbloquear(ids["ana"], ids["beto"])
    assert meetings.entrar(novo, ids["beto"])["participando"]


@pytest.fixture
def api(tmp_path, mundo):
    db, meetings, amigos, ids = mundo
    accounts = Accounts(db)

    class Chat:
        def answer(self, question, foco="locais"):
            return {}

    factory = partial(Handler, chat=Chat(), accounts=accounts, meetings=meetings, friends=amigos,
                      directory=str(tmp_path / "public"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), factory)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    clients = {}
    for login in ("ana", "beto"):
        client = httpx.Client(base_url=url, headers={"Origin": url}, trust_env=False)
        assert client.post("/api/sessao", json={"login": login, "senha": "senha-segura-123"}).status_code == 200
        clients[login] = client
    yield clients, db, meetings, ids
    for client in clients.values():
        client.close()
    server.shutdown()
    server.server_close()
    thread.join()


def test_api_de_amigos_ponta_a_ponta(api):
    clients, db, meetings, ids = api
    ana, beto = clients["ana"], clients["beto"]
    praticaram(db, meetings, ids["ana"], ids["beto"])
    pessoas = ana.get("/api/amigos").json()["pessoas"]
    assert [p["apelido"] for p in pessoas] == ["Beto"]
    assert ana.post(f"/api/amigos/{ids['beto']}/pedido", json={}).json() == {"amizade": "pedido_enviado"}
    assert beto.post(f"/api/amigos/{ids['ana']}/aceite", json={}).json() == {"amizade": "amigos"}
    assert beto.put(f"/api/amigos/{ids['ana']}/nota", json={"nota": 4}).json() == {"minha_nota": 4}
    assert beto.put(f"/api/amigos/{ids['ana']}/nota", json={"nota": 9}).status_code == 400
    resumo = ana.get("/api/amigos").json()
    assert resumo["reputacao"] == {"nota": None, "total": 1, "minimo": 3}
    assert ana.put(f"/api/amigos/{ids['beto']}/bloqueio", json={}).json() == {"bloqueado": True}
    assert ana.delete(f"/api/amigos/{ids['beto']}/bloqueio").json() == {"bloqueado": False}
    assert ana.delete(f"/api/amigos/{ids['beto']}").json() == {"amizade": "nenhuma"}


def test_api_de_amigos_exige_login(api, tmp_path):
    clients, *_ = api
    url = str(clients["ana"].base_url)
    with httpx.Client(base_url=url, headers={"Origin": url}, trust_env=False) as anonimo:
        assert anonimo.get("/api/amigos").status_code == 401
        assert anonimo.post("/api/amigos/" + "a" * 32 + "/pedido", json={}).status_code == 401
