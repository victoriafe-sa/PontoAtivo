"""Serviços externos usados pelo site.

- BrasilAPI: feriados nacionais (sem chave), mais os feriados distritais do DF.

O site chama só o servidor do PontoAtivo, que consulta esses serviços com cache.
"""

from __future__ import annotations

import json
import time
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .persistencia import ApiError

USER_AGENT = "PontoAtivo/1.0 (projeto academico; mapa esportivo do DF)"
TIMEOUT = 12

BRASILAPI_FERIADOS = "https://brasilapi.com.br/api/feriados/v1/{ano}"

# Feriados distritais do DF que a BrasilAPI (só nacionais) não traz.
# Lei Distrital nº 963/1995: Dia do Evangélico, 30 de novembro.
FERIADOS_DF = (("11-30", "Dia do Evangélico (feriado distrital)"),)


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


class ServicosExternos:
    def __init__(self, fetch=_http_json, clock=time.time):
        self.fetch = fetch
        self.clock = clock
        self._cache = {}
        self._lock = Lock()

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
