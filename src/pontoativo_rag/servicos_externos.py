"""Serviços externos usados pelo site: tempo, feriados e rotas.

- Open-Meteo: previsão do tempo, índice UV e qualidade do ar (sem chave).
- BrasilAPI: feriados nacionais (sem chave), mais os feriados distritais do DF.
- openrouteservice: rotas a pé e para cadeira de rodas (precisa de chave gratuita,
  em PONTOATIVO_ORS_API_KEY).

O site chama só o servidor do PontoAtivo, que consulta esses serviços com cache.
Assim a chave não vai para o navegador e as coordenadas ficam restritas ao DF.
"""

from __future__ import annotations

import json
import math
import time
from datetime import date, datetime, timedelta, timezone
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .persistencia import ApiError

# Limites do DF (os mesmos do mapa), com uma folga para o entorno imediato.
DF_SUL, DF_OESTE, DF_NORTE, DF_LESTE = -16.13, -48.37, -15.42, -47.23
USER_AGENT = "PontoAtivo/1.0 (projeto academico; mapa esportivo do DF)"
TIMEOUT = 12

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AR = "https://air-quality-api.open-meteo.com/v1/air-quality"
BRASILAPI_FERIADOS = "https://brasilapi.com.br/api/feriados/v1/{ano}"
ORS_DIRECTIONS = "https://api.openrouteservice.org/v2/directions/{perfil}/geojson"

PERFIS_ROTA = {"a_pe": "foot-walking", "cadeira_de_rodas": "wheelchair"}
MAX_DISTANCIA_ROTA_KM = 30

# Feriados distritais do DF que a BrasilAPI (só nacionais) não traz.
# Lei Distrital nº 963/1995: Dia do Evangélico, 30 de novembro.
FERIADOS_DF = (("11-30", "Dia do Evangélico (feriado distrital)"),)

# Códigos de tempo da OMM usados pelo Open-Meteo.
CONDICOES = {
    0: "céu limpo", 1: "poucas nuvens", 2: "parcialmente nublado", 3: "nublado",
    45: "neblina", 48: "neblina", 51: "garoa fraca", 53: "garoa", 55: "garoa forte",
    61: "chuva fraca", 63: "chuva", 65: "chuva forte", 66: "chuva congelante", 67: "chuva congelante",
    80: "pancadas de chuva fracas", 81: "pancadas de chuva", 82: "pancadas de chuva fortes",
    95: "trovoadas", 96: "trovoadas com granizo", 99: "trovoadas com granizo",
}


class ServicoIndisponivel(ApiError):
    """Erro de um serviço externo, mostrado ao usuário sem detalhes técnicos."""

    def __init__(self, message):
        super().__init__(503, message)


def _http_json(url, *, headers=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = Request(url, data=data, headers={"User-Agent": USER_AGENT, "Accept": "application/json",
                                                **({"Content-Type": "application/json"} if data else {}),
                                                **(headers or {})})
    with urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def validar_ponto(lat, lon):
    if not all(math.isfinite(v) for v in (lat, lon)) or not (DF_SUL <= lat <= DF_NORTE and DF_OESTE <= lon <= DF_LESTE):
        raise ApiError(400, "O ponto precisa estar no Distrito Federal.")
    return lat, lon


def _distancia_km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def nivel_uv(uv):
    if uv is None:
        return None
    return ("baixo" if uv < 3 else "moderado" if uv < 6 else "alto" if uv < 8
            else "muito alto" if uv < 11 else "extremo")


def nivel_ar(aqi):
    """Faixas do índice de qualidade do ar (US AQI) em português."""
    if aqi is None:
        return None
    return ("bom" if aqi <= 50 else "moderado" if aqi <= 100 else "ruim para grupos sensíveis"
            if aqi <= 150 else "ruim" if aqi <= 200 else "muito ruim" if aqi <= 300 else "péssimo")


class ServicosExternos:
    def __init__(self, ors_key="", fetch=_http_json, clock=time.time):
        self.ors_key = (ors_key or "").strip()
        self.fetch = fetch
        self.clock = clock
        self._cache = {}
        self._lock = Lock()

    @property
    def rotas_disponiveis(self):
        return bool(self.ors_key)

    def _cached(self, key, ttl, load):
        now = self.clock()
        with self._lock:
            hit = self._cache.get(key)
            if hit and hit[0] > now:
                return hit[1]
        value = load()
        with self._lock:
            if len(self._cache) > 2000:
                self._cache.clear()
            self._cache[key] = (now + ttl, value)
        return value

    def _buscar(self, nome, url, **kwargs):
        try:
            return self.fetch(url, **kwargs)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            raise ServicoIndisponivel(f"{nome} não respondeu agora. Tente novamente mais tarde.") from None

    # ---------- Open-Meteo ----------
    def clima(self, lat, lon, quando):
        """Previsão para a hora de ``quando`` (horário de Brasília, sem fuso)."""
        lat, lon = validar_ponto(lat, lon)
        hora = quando.replace(minute=0, second=0, microsecond=0)
        ponto = (round(lat, 2), round(lon, 2))

        def previsao():
            query = urlencode({
                "latitude": ponto[0], "longitude": ponto[1], "timezone": "America/Sao_Paulo",
                "hourly": "temperature_2m,precipitation_probability,uv_index,weather_code",
                "forecast_days": 16,
            })
            return self._buscar("O serviço de previsão do tempo", f"{OPEN_METEO}?{query}")

        def ar():
            query = urlencode({"latitude": ponto[0], "longitude": ponto[1], "timezone": "America/Sao_Paulo",
                               "hourly": "us_aqi,pm2_5", "forecast_days": 5})
            try:
                return self._buscar("O serviço de qualidade do ar", f"{OPEN_METEO_AR}?{query}")
            except ServicoIndisponivel:
                return {}  # a previsão do tempo continua útil sem o dado do ar

        tempo = self._cached(("tempo", ponto), 1800, previsao)
        horas = tempo.get("hourly", {}).get("time", [])
        alvo = hora.strftime("%Y-%m-%dT%H:00")
        if alvo not in horas:
            return {"disponivel": False, "motivo": "A previsão cobre só os próximos 16 dias."}
        i = horas.index(alvo)
        h = tempo["hourly"]
        valor = lambda serie, idx=i, dados=h: (dados.get(serie) or [None] * (idx + 1))[idx]
        uv = valor("uv_index")
        resultado = {
            "disponivel": True,
            "hora": alvo,
            "temperatura": valor("temperature_2m"),
            "chance_chuva": valor("precipitation_probability"),
            "uv": uv,
            "uv_nivel": nivel_uv(uv),
            "condicao": CONDICOES.get(valor("weather_code"), ""),
            "qualidade_ar": None,
            "fonte": "Open-Meteo",
        }
        dados_ar = self._cached(("ar", ponto), 1800, ar)
        horas_ar = dados_ar.get("hourly", {}).get("time", [])
        if alvo in horas_ar:
            j = horas_ar.index(alvo)
            aqi = (dados_ar["hourly"].get("us_aqi") or [None] * (j + 1))[j]
            if aqi is not None:
                resultado["qualidade_ar"] = {"indice": aqi, "nivel": nivel_ar(aqi)}
        return resultado

    # ---------- BrasilAPI ----------
    def feriados(self, ano):
        if not 2000 <= ano <= 2100:
            raise ApiError(400, "Ano inválido.")

        def carregar():
            dados = self._buscar("O serviço de feriados", BRASILAPI_FERIADOS.format(ano=ano))
            lista = [{"data": f["date"], "nome": f["name"], "tipo": "nacional"}
                     for f in dados if isinstance(f, dict) and f.get("date") and f.get("name")]
            datas = {f["data"] for f in lista}
            for dia, nome in FERIADOS_DF:
                if f"{ano}-{dia}" not in datas:
                    lista.append({"data": f"{ano}-{dia}", "nome": nome, "tipo": "distrital"})
            return sorted(lista, key=lambda f: f["data"])

        return self._cached(("feriados", ano), 86400, carregar)

    # ---------- openrouteservice ----------
    def rota(self, origem, destino, perfil):
        if perfil not in PERFIS_ROTA:
            raise ApiError(400, "Escolha a rota a pé ou para cadeira de rodas.")
        if not self.ors_key:
            raise ServicoIndisponivel("As rotas ainda não estão configuradas neste servidor.")
        origem, destino = validar_ponto(*origem), validar_ponto(*destino)
        if _distancia_km(origem, destino) > MAX_DISTANCIA_ROTA_KM:
            raise ApiError(400, f"A rota a pé vai até {MAX_DISTANCIA_ROTA_KM} km.")
        chave = ("rota", perfil, *(round(v, 4) for v in (*origem, *destino)))

        def carregar():
            dados = self._buscar(
                "O serviço de rotas",
                ORS_DIRECTIONS.format(perfil=PERFIS_ROTA[perfil]),
                headers={"Authorization": self.ors_key},
                body={"coordinates": [[origem[1], origem[0]], [destino[1], destino[0]]],
                      "language": "pt", "instructions": True},
            )
            try:
                feature = dados["features"][0]
                resumo = feature["properties"]["summary"]
                passos = [p for s in feature["properties"].get("segments", []) for p in s.get("steps", [])]
                return {
                    "perfil": perfil,
                    "distancia_m": round(resumo.get("distance", 0)),
                    "duracao_s": round(resumo.get("duration", 0)),
                    "linha": [[lat, lon] for lon, lat, *_ in feature["geometry"]["coordinates"]],
                    "passos": [{"instrucao": p.get("instruction", ""), "distancia_m": round(p.get("distance", 0))}
                               for p in passos[:30]],
                    "fonte": "openrouteservice",
                }
            except (KeyError, IndexError, TypeError, ValueError):
                raise ServicoIndisponivel("Não encontrei uma rota entre esses pontos.") from None

        return self._cached(chave, 86400, carregar)


def ler_data_hora(texto):
    """Aceita "2026-11-22T18:00" ou ISO com fuso; devolve a hora de Brasília sem fuso."""
    try:
        valor = datetime.fromisoformat(str(texto).replace("Z", "+00:00"))
    except ValueError:
        raise ApiError(400, "Data inválida.") from None
    if valor.tzinfo is not None:
        # Brasília não tem horário de verão desde 2019: UTC-3 o ano todo.
        valor = valor.astimezone(timezone(timedelta(hours=-3))).replace(tzinfo=None)
    if not date(2000, 1, 1) <= valor.date() <= date(2100, 12, 31):
        raise ApiError(400, "Data inválida.")
    return valor
