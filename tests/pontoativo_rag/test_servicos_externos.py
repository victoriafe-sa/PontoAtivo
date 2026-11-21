from datetime import datetime
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.error import URLError

import httpx
import pytest

from pontoativo_rag.persistencia import ApiError
from pontoativo_rag.servicos_externos import ServicoIndisponivel, ServicosExternos, ler_data_hora, nivel_ar, nivel_uv
from pontoativo_rag.web import Handler

PARQUE_DA_CIDADE = (-15.80, -47.90)


def tempo_fake():
    horas = ["2026-11-22T17:00", "2026-11-22T18:00"]
    return {"hourly": {"time": horas, "temperature_2m": [29.0, 27.4], "precipitation_probability": [10, 40],
                       "uv_index": [6.1, 2.0], "weather_code": [2, 80]}}


def ar_fake():
    return {"hourly": {"time": ["2026-11-22T18:00"], "us_aqi": [42], "pm2_5": [8.0]}}


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


def test_clima_pega_a_hora_do_encontro_e_usa_cache():
    fetch = FakeFetch({"air-quality": ar_fake(), "forecast": tempo_fake()})
    servicos = ServicosExternos(fetch=fetch)
    clima = servicos.clima(*PARQUE_DA_CIDADE, datetime(2026, 11, 22, 18, 30))
    assert clima == {
        "disponivel": True, "hora": "2026-11-22T18:00", "temperatura": 27.4, "chance_chuva": 40,
        "uv": 2.0, "uv_nivel": "baixo", "condicao": "pancadas de chuva fracas",
        "qualidade_ar": {"indice": 42, "nivel": "bom"}, "fonte": "Open-Meteo",
    }
    servicos.clima(*PARQUE_DA_CIDADE, datetime(2026, 11, 22, 17, 0))
    assert len(fetch.chamadas) == 2  # tempo e ar só uma vez cada, depois cache


def test_clima_fora_do_alcance_da_previsao():
    servicos = ServicosExternos(fetch=FakeFetch({"air-quality": ar_fake(), "forecast": tempo_fake()}))
    assert servicos.clima(*PARQUE_DA_CIDADE, datetime(2026, 12, 25, 9))["disponivel"] is False


def test_clima_continua_sem_o_dado_do_ar():
    fetch = FakeFetch({"air-quality": URLError("fora"), "forecast": tempo_fake()})
    clima = ServicosExternos(fetch=fetch).clima(*PARQUE_DA_CIDADE, datetime(2026, 11, 22, 18))
    assert clima["temperatura"] == 27.4 and clima["qualidade_ar"] is None


def test_clima_recusa_ponto_fora_do_df():
    with pytest.raises(ApiError):
        ServicosExternos(fetch=FakeFetch({})).clima(-23.55, -46.63, datetime(2026, 11, 22, 18))


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


def test_niveis_em_portugues():
    assert nivel_uv(9) == "muito alto" and nivel_ar(160) == "ruim"


def test_data_com_fuso_vira_horario_de_brasilia():
    assert ler_data_hora("2026-11-22T21:00:00Z") == datetime(2026, 11, 22, 18, 0)


@pytest.fixture
def api(tmp_path):
    servicos = ServicosExternos(fetch=FakeFetch({
        "air-quality": ar_fake(), "forecast": tempo_fake(),
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


def test_rotas_http_de_clima_e_feriados(api):
    clima = api.get("/api/clima", params={"lat": -15.80, "lon": -47.90, "inicio": "2026-11-22T18:00"})
    assert clima.status_code == 200 and clima.json()["temperatura"] == 27.4
    assert api.get("/api/clima", params={"lat": 0, "lon": 0, "inicio": "2026-11-22T18:00"}).status_code == 400
    feriados = api.get("/api/feriados", params={"ano": 2026}).json()
    assert feriados["fonte"] == "BrasilAPI" and len(feriados["feriados"]) == 2
    assert api.get("/api/feriados", params={"ano": "x"}).status_code == 400
