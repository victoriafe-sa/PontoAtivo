from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from pontoativo_rag.persistencia import Database
from pontoativo_rag.contas import Accounts
from pontoativo_rag.encontros import Meetings
from pontoativo_rag.web import Handler


@pytest.fixture
def api(tmp_path):
    db = Database(tmp_path / "private" / "db.sqlite3")
    accounts = Accounts(db)
    meetings = Meetings(db, [{"id": "campo-1", "nome": "Campo 1", "regiao": "Ceilândia"}])
    class Chat:
        def answer(self, question, foco="locais"):
            return {"rota": "mapa", "busca": question}
    factory = partial(Handler, chat=Chat(), accounts=accounts, meetings=meetings, directory=str(tmp_path / "public"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), factory)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    with httpx.Client(base_url=url, headers={"Origin": url}, trust_env=False) as a, httpx.Client(base_url=url, headers={"Origin": url}, trust_env=False) as b:
        yield a, b, db
    server.shutdown()
    server.server_close()
    thread.join()


def signup(client, login):
    result = client.post("/api/conta", json={"login": login, "senha": "senha-segura-123", "apelido": login, "idade": "25-34"})
    assert result.status_code == 201
    assert "HttpOnly" in result.headers["set-cookie"]
    assert "SameSite=Strict" in result.headers["set-cookie"]
    return result.json()


def test_fluxo_compartilhado_api_e_privacidade(api):
    a, b, _ = api
    assert a.get("/api/me").json()["usuario"] is None
    assert a.post("/api/encontros", json={}).status_code == 401
    signup(a, "pessoa-a")
    signup(b, "pessoa-b")
    created = a.post("/api/encontros", json={
        "local_id": "campo-1", "esporte": "Futebol",
        "inicio": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "nivel": "todos", "idade": "todos", "formato": "dupla",
    })
    assert created.status_code == 201
    event_id = created.json()["id"]
    joined = b.put(f"/api/encontros/{event_id}/participacao", json={})
    assert joined.json()["vagas"] == 0
    assert a.get("/api/encontros").json()["encontros"][0]["estado"] == "lotado"
    assert "password" not in a.get("/api/encontros").text
    assert "login" not in a.get("/api/encontros").text
    assert b.post(f"/api/encontros/{event_id}/cancelamento", json={}).status_code == 403
    assert b.delete(f"/api/encontros/{event_id}/participacao").json()["vagas"] == 1
    assert b.put(f"/api/encontros/{event_id}/participacao", json={}).status_code == 200
    assert a.post(f"/api/encontros/{event_id}/cancelamento", json={}).status_code == 200
    assert b.get("/api/encontros/meus").json()["encontros"][0]["estado"] == "cancelado"
    assert a.get("/api/encontros").json()["encontros"] == []
    assert b.delete("/api/sessao").status_code == 200
    assert b.get("/api/me").json()["usuario"] is None
    assert b.post("/api/sessao", json={"login": "pessoa-b", "senha": "senha-segura-123"}).status_code == 200
    assert a.post("/api/perguntar", json={"pergunta": "jogar bola"}).json()["rota"] == "mapa"


def test_api_rejeita_origem_corpo_e_sessao(api):
    a, _, _ = api
    assert a.post("/api/conta", json={}, headers={"Origin": "https://outro-site.example"}).status_code == 403
    assert a.post("/api/conta", content='{}', headers={"Content-Type": "text/plain"}).status_code == 400
    assert a.post("/api/conta", content='[]', headers={"Content-Type": "application/json"}).status_code == 400
    assert a.get("/api/encontros/meus").status_code == 401
    assert a.get("/../private/db.sqlite3").status_code == 404


def test_rota_inexistente_responde_404_sem_exigir_login(api):
    a, _, _ = api

    assert a.post("/api/qualquer", json={}).status_code == 404
    assert a.put("/api/encontros/abc/participacao", json={}).status_code == 404
    assert a.post("/api/encontros", json={}).status_code == 401


def test_falha_inesperada_na_listagem_devolve_500_legivel(api, monkeypatch):
    a, _, _ = api
    from pontoativo_rag.encontros import Meetings

    def quebra(*args, **kwargs):
        raise RuntimeError("banco ocupado")

    monkeypatch.setattr(Meetings, "listar_encontros", quebra)
    response = a.get("/api/encontros")

    assert response.status_code == 500
    assert set(response.json()) == {"erro"}
    assert "banco" not in response.json()["erro"]


@pytest.mark.parametrize(
    ("path", "public"),
    [
        ("/", True),
        ("/index.html", True),
        ("/app.js?v=4", True),
        ("/telas.js?v=telas-1", True),
        ("/data/locais.js", True),
        ("/assets/logo.svg", True),
        ("/ferramentas/build.py", False),
        ("/docs/relatorio.md", False),
        ("/.claude/launch.json", False),
        ("/data/", False),
        ("/data/../ferramentas/build.py", False),
        ("/data/%2e%2e/ferramentas/build.py", False),
        ("/data/%2E%2E/%2E%2E/pyproject.toml", False),
        ("/assets/..%5c..%5cferramentas", False),
    ],
)
def test_servidor_publica_somente_os_arquivos_do_site(path, public):
    from urllib.parse import urlsplit
    from pontoativo_rag.web import is_public

    assert is_public(urlsplit(path).path) is public


def test_arquivos_internos_e_listagem_de_pasta_ficam_ocultos(tmp_path):
    from pontoativo_rag.web import Handler

    public = tmp_path / "site"
    (public / "data").mkdir(parents=True)
    (public / "ferramentas").mkdir()
    (public / "index.html").write_text("<h1>ok</h1>", encoding="utf-8")
    (public / "data" / "locais.js").write_text("window.PA_LOCAIS=[]", encoding="utf-8")
    (public / "ferramentas" / "build.py").write_text("segredo = 1", encoding="utf-8")
    factory = partial(Handler, chat=None, directory=str(public))
    server = ThreadingHTTPServer(("127.0.0.1", 0), factory)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{server.server_port}", trust_env=False) as client:
            assert client.get("/").status_code == 200
            assert client.get("/data/locais.js").status_code == 200
            assert client.get("/ferramentas/build.py").status_code == 404
            assert client.get("/data/%2e%2e/ferramentas/build.py").status_code == 404
            assert client.get("/data/").status_code == 404
            assert client.head("/ferramentas/build.py").status_code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_limite_de_login_usa_ip_do_proxy_somente_quando_confiavel(tmp_path):
    from pontoativo_rag.web import Handler

    db = Database(tmp_path / "db.sqlite3")
    accounts = Accounts(db)
    accounts.register({"login": "vitima", "senha": "senha-segura-123", "apelido": "Vítima", "idade": "25-34"})

    def serve(trust_proxy):
        factory = partial(Handler, chat=None, accounts=accounts, meetings=None,
                          trust_proxy=trust_proxy, directory=str(tmp_path))
        server = ThreadingHTTPServer(("127.0.0.1", 0), factory)
        Thread(target=server.serve_forever, daemon=True).start()
        return server

    server = serve(trust_proxy=True)
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{server.server_port}", trust_env=False) as client:
            for _ in range(5):
                wrong = client.post("/api/sessao", json={"login": "vitima", "senha": "errada-errada"},
                                    headers={"X-Forwarded-For": "203.0.113.9"})
                assert wrong.status_code == 401
            blocked = client.post("/api/sessao", json={"login": "vitima", "senha": "senha-segura-123"},
                                  headers={"X-Forwarded-For": "203.0.113.9"})
            assert blocked.status_code == 429
            # A pessoa dona da conta, vinda de outro IP, continua entrando.
            owner = client.post("/api/sessao", json={"login": "vitima", "senha": "senha-segura-123"},
                                headers={"X-Forwarded-For": "198.51.100.7"})
            assert owner.status_code == 200
    finally:
        server.shutdown()
        server.server_close()

    server = serve(trust_proxy=False)
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{server.server_port}", trust_env=False) as client:
            # Sem proxy confiável, o cabeçalho é ignorado: não dá para fugir do limite trocando-o.
            for index in range(5):
                client.post("/api/sessao", json={"login": "vitima", "senha": "errada-errada"},
                            headers={"X-Forwarded-For": f"10.0.0.{index}"})
            assert client.post("/api/sessao", json={"login": "vitima", "senha": "senha-segura-123"},
                               headers={"X-Forwarded-For": "10.0.0.99"}).status_code == 429
    finally:
        server.shutdown()
        server.server_close()


def test_rota_de_preferencias_exige_login_e_salva(api):
    a, _, _ = api

    assert a.put("/api/conta/preferencias", json={"esportes": ["Futebol"]}).status_code == 401
    signup(a, "pessoa")
    saved = a.put("/api/conta/preferencias", json={"esportes": ["Futebol"], "regiao": ""})
    invalid = a.put("/api/conta/preferencias", json={"esportes": ["Xadrez"]})

    assert saved.status_code == 200
    assert saved.json() == {"preferencias": {"esportes": ["Futebol"], "regiao": ""}}
    assert a.get("/api/me").json()["usuario"]["preferencias"]["esportes"] == ["Futebol"]
    assert invalid.status_code == 400


def test_admin_entra_sem_cadastro_no_proprio_computador(api):
    a, b, _ = api
    assert a.get("/api/me").json()["admin_local"] is True
    entrou = a.post("/api/sessao/admin", json={})
    assert entrou.status_code == 200
    assert "HttpOnly" in entrou.headers["set-cookie"]
    admin = entrou.json()["usuario"]
    assert admin["apelido"] == "Admin"
    assert a.get("/api/me").json()["usuario"]["id"] == admin["id"]
    # Entrar de novo reaproveita a mesma conta.
    assert b.post("/api/sessao/admin", json={}).json()["usuario"]["id"] == admin["id"]


def test_admin_nao_entra_por_senha_nem_por_cadastro(api):
    a, _, _ = api
    a.post("/api/sessao/admin", json={})
    tentativa = a.post("/api/sessao", json={"login": "admin", "senha": "qualquer-senha-123"})
    assert tentativa.status_code == 401
    cadastro = a.post("/api/conta", json={"login": "admin", "senha": "senha-segura-123", "apelido": "Falso", "idade": "25-34"})
    assert cadastro.status_code == 409


@pytest.mark.parametrize("headers", [
    {"X-Forwarded-For": "203.0.113.7"},
    {"Forwarded": "for=203.0.113.7"},
    {"Host": "pontoativo.exemplo.org"},
])
def test_admin_bloqueado_quando_o_acesso_nao_e_local(api, headers):
    a, _, _ = api
    assert a.get("/api/me", headers=headers).json()["admin_local"] is False
    assert a.post("/api/sessao/admin", json={}, headers=headers).status_code == 403


def test_admin_bloqueado_atras_de_proxy(tmp_path):
    db = Database(tmp_path / "private" / "db.sqlite3")
    class Chat:
        def answer(self, question, foco="locais"):
            return {}
    factory = partial(Handler, chat=Chat(), accounts=Accounts(db), meetings=Meetings(db, []),
                      public_origin="https://pontoativo.exemplo.org", directory=str(tmp_path / "public"))
    server = ThreadingHTTPServer(("127.0.0.1", 0), factory)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        with httpx.Client(base_url=url, headers={"Origin": url}, trust_env=False) as client:
            assert client.get("/api/me").json()["admin_local"] is False
            assert client.post("/api/sessao/admin", json={}).status_code == 403
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
