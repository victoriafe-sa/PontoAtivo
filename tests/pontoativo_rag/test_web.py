import json
import threading
import urllib.error
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from pontoativo_rag import consulta, web
from pontoativo_rag.configuracao import Settings
from pontoativo_rag.geracao import GroundedAnswer, LLMUnavailable
from pontoativo_rag.recuperacao import RetrievedChunk


class FakeModel:
    def __init__(self, reply="", error=None):
        self.reply = reply
        self.error = error
        self.calls = []

    def complete(self, system, user, *, schema=None, options=None):
        self.calls.append((system, user, schema))
        self.options = options
        if self.error is not None:
            raise self.error
        return self.reply if isinstance(self.reply, str) else json.dumps(self.reply)


def _chunk(index: int, text: str = "Trecho do documento.") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=f"c{index}",
        source_id=f"00{index}",
        title=f"Fonte {index}",
        institution="SEL-DF",
        location=f"dados/rag/fontes/00{index}.pdf",
        text=text,
        distance=0.2,
        matched_segments=1,
        page_number=index,
    )


@pytest.fixture
def chat(tmp_path: Path) -> web.Chat:
    return web.Chat(Settings.from_env(root=tmp_path))


def _use_rag(monkeypatch, answer: GroundedAnswer) -> list:
    calls = []
    monkeypatch.setattr(consulta, "build_pipeline", lambda settings: ("retriever", "generator"))

    def fake_answer(settings, retriever, generator, question):
        calls.append((retriever, generator, question))
        return answer, {}

    monkeypatch.setattr(consulta, "answer_question", fake_answer)
    return calls


@pytest.mark.parametrize(
    "question",
    ["Jogar bola em Brasília", "onde posso jogar futebol no DF?", "Jogar futebol no Distrito Federal!"],
)
def test_busca_direta_de_futebol_no_df_nao_chama_o_modelo(chat, question):
    chat.model = FakeModel(error=AssertionError("não deveria chamar o modelo"))

    assert chat.answer(question) == {"rota": "mapa", "busca": "futebol em Brasília"}


def test_rota_mapa_devolve_busca_reescrita(chat):
    chat.model = FakeModel({"rota": "mapa", "busca": "  campo de futebol em Taguatinga  "})

    assert chat.answer("tem campo pra bater uma pelada em Taguatinga?") == {
        "rota": "mapa",
        "busca": "campo de futebol em Taguatinga",
    }
    _, user, schema = chat.model.calls[0]
    assert user == "tem campo pra bater uma pelada em Taguatinga?"
    assert schema == web.SCHEMA
    assert chat.model.options == web.CLASSIFICATION_OPTIONS


@pytest.mark.parametrize("route", ["fora_escopo", "esclarecer"])
def test_rotas_sem_busca_descartam_campo_busca(chat, route):
    chat.model = FakeModel({"rota": route, "busca": "ignorado"})

    assert chat.answer("pergunta qualquer") == {"rota": route}


@pytest.mark.parametrize(
    "reply",
    [
        {"rota": "outra", "busca": ""},
        {"rota": "mapa", "busca": "x" * 1001},
        {"rota": "mapa"},
        ["mapa"],
    ],
)
def test_classificacao_invalida_gera_value_error(chat, reply):
    chat.model = FakeModel(reply)

    with pytest.raises(ValueError):
        chat.answer("pergunta")


@pytest.mark.parametrize(
    "question",
    ["pec no gama?", "PEC no Gama", "onde tem pec no gama?", "Quadra de areia no Guará!",
     "campo de futebol em Taguatinga", "tem pista de skate em Ceilândia?",
     "campo sintético no Gama", "campo society em Samambaia", "campo de terra batida no Gama"],
)
def test_tipo_e_regiao_vao_direto_ao_mapa(chat, question):
    chat.model = FakeModel(error=AssertionError("não deveria chamar o modelo"))

    assert chat.answer(question) == {"rota": "mapa", "busca": question}


@pytest.mark.parametrize(
    "question",
    ["campo de futebol e cassino em Brasília", "matrícula no Centro Olímpico do Gama",
     "horário do pec no gama", "pec"],
)
def test_pergunta_com_outras_palavras_passa_pelo_modelo(chat, question):
    chat.model = FakeModel({"rota": "esclarecer", "busca": ""})

    assert chat.answer(question) == {"rota": "esclarecer"}


@pytest.mark.parametrize("busca", ["", "   "])
def test_mapa_com_busca_vazia_usa_a_pergunta(chat, busca):
    chat.model = FakeModel({"rota": "mapa", "busca": busca})

    assert chat.answer("onde tem pec no gama?") == {"rota": "mapa", "busca": "onde tem pec no gama?"}


def test_foco_duvidas_vai_direto_aos_documentos_sem_classificar(chat, monkeypatch):
    retrieved = [_chunk(1)]
    answer = GroundedAnswer(
        question="q", mode="rag", answer="Inscrição pelo SISCOP [F1].",
        retrieved=retrieved, cited=retrieved,
    )
    calls = _use_rag(monkeypatch, answer)
    chat.model = FakeModel(error=AssertionError("não deveria classificar"))

    result = chat.answer("pec no gama?", "duvidas")

    assert calls == [("retriever", "generator", "pec no gama?")]
    assert result["rota"] == "duvidas"
    assert result["resposta"] == "Inscrição pelo SISCOP [F1]."


def test_foco_duvidas_ainda_barra_termo_improprio(chat, monkeypatch):
    calls = _use_rag(monkeypatch, None)

    result = chat.answer("matrícula no COP e sexo", "duvidas")

    assert result["rota"] == "fora_escopo" and calls == []


def test_pergunta_complexa_na_barra_de_locais_indica_a_aba_duvidas(chat, monkeypatch):
    calls = _use_rag(monkeypatch, None)
    chat.model = FakeModel({"rota": "duvidas", "busca": ""})

    assert chat.answer("como faço matrícula no COP?") == {"rota": "duvidas"}
    assert calls == []


def test_json_malformado_gera_value_error(chat):
    chat.model = FakeModel("isto não é json")

    with pytest.raises(ValueError):
        chat.answer("pergunta")


def test_rota_documentos_com_rag_mostra_apenas_fontes_citadas(chat, monkeypatch):
    retrieved = [_chunk(1), _chunk(2), _chunk(3)]
    answer = GroundedAnswer(
        question="matrícula no COP",
        mode="rag",
        answer="A matrícula é presencial [F2].",
        retrieved=retrieved,
        cited=[retrieved[1]],
    )
    calls = _use_rag(monkeypatch, answer)
    chat.model = FakeModel({"rota": "documentos", "busca": ""})

    result = chat.answer("como faço matrícula no COP?")

    assert calls == [("retriever", "generator", "como faço matrícula no COP?")]
    assert result == {
        "rota": "documentos",
        "modo": "rag",
        "resposta": "A matrícula é presencial [F2].",
        "fontes": [
            {
                "referencia": "F2",
                "titulo": "Fonte 2",
                "url": "dados/rag/fontes/002.pdf",
                "paginas": "2",
                "trecho": "",
            }
        ],
    }


def test_rota_documentos_sem_geracao_mostra_trechos_recuperados(chat, monkeypatch):
    retrieved = [_chunk(1, "a" * 700), _chunk(2)]
    answer = GroundedAnswer(
        question="q",
        mode="recuperacao_sem_geracao",
        answer="Trechos recuperados.",
        retrieved=retrieved,
    )
    _use_rag(monkeypatch, answer)
    chat.model = FakeModel({"rota": "documentos", "busca": ""})

    result = chat.answer("q")

    assert [fonte["referencia"] for fonte in result["fontes"]] == ["F1", "F2"]
    assert result["fontes"][0]["trecho"] == "a" * 600
    assert result["fontes"][1]["trecho"] == "Trecho do documento."


def test_pipeline_e_montado_uma_unica_vez(chat, monkeypatch):
    builds = []
    monkeypatch.setattr(
        consulta, "build_pipeline", lambda settings: builds.append(1) or ("r", "g")
    )
    monkeypatch.setattr(
        consulta,
        "answer_question",
        lambda *args: (GroundedAnswer(question="q", mode="abstencao", answer="", retrieved=[]), {}),
    )
    chat.model = FakeModel({"rota": "documentos", "busca": ""})

    chat.answer("primeira")
    chat.answer("segunda")

    assert builds == [1]


class FakeChat:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.questions = []
        self.focos = []

    def answer(self, question, foco="locais"):
        self.questions.append(question)
        self.focos.append(foco)
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def server(tmp_path: Path):
    (tmp_path / "index.html").write_text("<h1>PontoAtivo</h1>", encoding="utf-8")
    fake = FakeChat(result={"rota": "esclarecer"})
    handler = partial(web.Handler, chat=fake, directory=str(tmp_path))
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}", fake
    finally:
        httpd.shutdown()
        httpd.server_close()


def _post(base: str, path: str, body: bytes) -> tuple[int, dict, dict]:
    request = urllib.request.Request(
        base + path, data=body, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, dict(response.headers), json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), json.loads(error.read())


def _json(payload) -> bytes:
    return json.dumps(payload).encode("utf-8")


def test_servidor_entrega_arquivos_estaticos(server):
    base, _ = server

    with urllib.request.urlopen(base + "/", timeout=5) as response:
        assert response.status == 200
        assert "PontoAtivo" in response.read().decode("utf-8")


def test_arquivos_do_site_sao_conferidos_a_cada_visita(server):
    base, _ = server

    with urllib.request.urlopen(base + "/", timeout=5) as response:
        assert response.headers["Cache-Control"] == "no-cache"
    # A API continua sem cache nenhum.
    status, headers, _ = _post(base, "/api/perguntar", _json({"pergunta": "Onde jogar?"}))
    assert headers["Cache-Control"] == "no-store"


def test_perguntar_responde_json_e_remove_espacos(server):
    base, fake = server

    status, headers, payload = _post(base, "/api/perguntar", _json({"pergunta": "  Onde jogar?  "}))

    assert status == 200
    assert payload == {"rota": "esclarecer"}
    assert fake.questions == ["Onde jogar?"]
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize(("body", "foco"), [({}, "locais"), ({"foco": "duvidas"}, "duvidas")])
def test_perguntar_repassa_o_foco_da_barra(server, body, foco):
    base, fake = server

    status, _, _ = _post(base, "/api/perguntar", _json({"pergunta": "oi", **body}))

    assert status == 200
    assert fake.focos == [foco]


def test_foco_desconhecido_devolve_400(server):
    base, fake = server

    status, _, _ = _post(base, "/api/perguntar", _json({"pergunta": "oi", "foco": "outro"}))

    assert status == 400
    assert fake.questions == []


def test_post_em_rota_inexistente_devolve_404(server):
    base, fake = server

    status, _, payload = _post(base, "/api/outra", _json({"pergunta": "oi"}))

    assert status == 404
    assert "erro" in payload
    assert fake.questions == []


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"{nao e json",
        _json(["pergunta"]),
        _json({"pergunta": 123}),
        _json({"pergunta": "   "}),
        _json({"pergunta": "x" * 1001}),
        _json({"pergunta": "x" * 9000}),
        b"\xff\xfe",
    ],
)
def test_pedidos_invalidos_devolvem_400(server, body):
    base, fake = server

    status, _, payload = _post(base, "/api/perguntar", body)

    assert status == 400
    assert payload == {"erro": "Digite uma pergunta de até 1.000 caracteres."}
    assert fake.questions == []


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (SystemExit(1), 503),
        (LLMUnavailable("offline"), 503),
        (ValueError("classificação inválida"), 503),
        (RuntimeError("falha interna"), 500),
    ],
)
def test_erros_do_chat_viram_respostas_legiveis(server, error, status):
    base, fake = server
    fake.error = error

    code, _, payload = _post(base, "/api/perguntar", _json({"pergunta": "oi"}))

    assert code == status
    assert set(payload) == {"erro"}
    assert "falha interna" not in payload["erro"]


@pytest.mark.parametrize(
    ("question", "termo"),
    [
        ("campo de futebol e sexo em brasilia", "sexo"),
        ("Jogar bola e putaria em Brasília", "putaria"),
    ],
)
def test_termo_improprio_e_barrado_antes_do_modelo(chat, question, termo):
    chat.model = FakeModel(error=AssertionError("não deveria chamar o modelo"))

    assert chat.answer(question) == {"rota": "fora_escopo", "motivo": "termo_improprio", "termo": termo}


def test_prompt_pede_para_ler_a_frase_inteira():
    assert "nunca descarte uma parte" in web.PROMPT
    assert "'campo de futebol e cassino em Brasília' -> fora_escopo" in web.PROMPT


def test_barra_do_mapa_classifica_com_o_modelo_do_mapa(tmp_path, monkeypatch):
    monkeypatch.setenv("PONTOATIVO_OLLAMA_MODEL", "gemma4:12b")
    monkeypatch.setenv("PONTOATIVO_OLLAMA_MODEL_MAPA", "qwen3:4b")
    chat = web.Chat(Settings.from_env(root=tmp_path))
    assert chat.model.model == "qwen3:4b"
    assert chat.settings.ollama_model == "gemma4:12b"


def test_classificar_nao_busca_nos_documentos(chat, monkeypatch):
    calls = _use_rag(monkeypatch, None)
    chat.model = FakeModel({"rota": "documentos", "busca": ""})
    assert chat.classify("qual o horário do COP do Gama?") == {"rota": "documentos"}
    assert calls == []
