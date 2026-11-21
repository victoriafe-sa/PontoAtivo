from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import URLError

import httpx
import pytest

from pontoativo_rag.persistencia import ApiError
from pontoativo_rag.servicos_externos import ServicoIndisponivel, ServicosExternos
from pontoativo_rag.web import Handler


class FakeFetch:
    def __init__(self, respostas):
        self.respostas = respostas
        self.chamadas = []

    def __call__(self, url, **kwargs):
        self.chamadas.append((url, kwargs))
        for trecho, resposta in self.respostas.items():
            if trecho in url:
                if isinstance(resposta, Exception):
                    raise resposta
                return resposta
        raise AssertionError(f"URL inesperada: {url}")


def test_feriados_somam_os_distritais_do_df_e_usam_cache():
    fetch = FakeFetch({"brasilapi": [{"date": "2026-11-15", "name": "Proclamação da República", "type": "national"}]})
    servicos = ServicosExternos(fetch=fetch)
    feriados = servicos.feriados(2026)
    assert feriados == [
        {"data": "2026-11-15", "nome": "Proclamação da República", "tipo": "nacional"},
        {"data": "2026-11-30", "nome": "Dia do Evangélico (feriado distrital)", "tipo": "distrital"},
    ]
    servicos.feriados(2026)
    assert len(fetch.chamadas) == 1


def test_feriados_recusam_ano_fora_do_intervalo():
    with pytest.raises(ApiError):
        ServicosExternos(fetch=FakeFetch({})).feriados(1500)


def test_falha_do_servico_vira_mensagem_amigavel():
    servicos = ServicosExternos(fetch=FakeFetch({"brasilapi": URLError("fora")}))
    with pytest.raises(ServicoIndisponivel) as erro:
        servicos.feriados(2026)
    assert erro.value.status == 503


@pytest.fixture
def api(tmp_path):
    servicos = ServicosExternos(fetch=FakeFetch({
        "brasilapi": [{"date": "2026-11-15", "name": "Proclamação da República"}],
    }))

    class Chat:
        def answer(self, question, foco="locais"):
            return {}

    factory = partial(Handler, chat=Chat(), services=servicos, directory=str(tmp_path))
    server = ThreadingHTTPServer(("127.0.0.1", 0), factory)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    with httpx.Client(base_url=url, headers={"Origin": url}, trust_env=False) as client:
        yield client
    server.shutdown()
    server.server_close()
    thread.join()


def test_rota_http_de_feriados(api):
    feriados = api.get("/api/feriados", params={"ano": 2026}).json()
    assert feriados["fonte"] == "BrasilAPI" and len(feriados["feriados"]) == 2
    assert api.get("/api/feriados", params={"ano": "x"}).status_code == 400
