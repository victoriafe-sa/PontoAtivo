"""Importa campos, quadras e praças da camada oficial "Espaços comunitários" (IDE-DF).

A camada (SEDUH, EQUIPAMENTOS_URBANOS/MapServer/2) traz polígonos com um código de
tipo e quase nenhum nome ou endereço. Ela não publica o significado dos códigos;
os três usados aqui foram confirmados pelo "Guia dos Espaços Públicos de Lazer do
DF" (Bruno Lofrano Porto, PPG-GEA/UnB, 2023), que os mapeia como Campos (5),
Quadras (7) e Praças (1), e pela área típica dos polígonos (quadras ~560 m²).

Saída: data/curadoria/espacos_comunitarios.json, no formato dos registros de
data/locais.js; ferramentas/gerar_base.py incorpora o arquivo na base candidata.

Uso (na pasta curadoria):
    python3 -B ferramentas/importar_espacos_comunitarios.py
"""
from __future__ import annotations

import argparse
import json
import math
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

CAMADA = "https://www.geoservicos.ide.df.gov.br/arcgis/rest/services/Publico/EQUIPAMENTOS_URBANOS/MapServer/2"
LIMITES_RA = "https://www.geoservicos.ide.df.gov.br/arcgis/rest/services/Publico/LIMITES/MapServer/1"

# código ec_tipo -> (tipo no mapa, nome, modalidades, raio para considerar duplicata, tipos comparados)
TIPOS = {
    5: ("campo", "Campo de futebol", ["futebol"], 60, {"campo"}),
    7: ("quadra", "Quadra poliesportiva", ["futebol", "vôlei", "basquete", "handebol"], 40, {"quadra", "areia"}),
    1: ("praca", "Praça", [], 30, {"praca"}),
}
# Mesma grafia de RA usada por ferramentas/build.py
RA_FIX = {"SCIA": "SCIA/Estrutural", "SIA": "SIA", "SOL NASCENTE E POR DO SOL": "Sol Nascente/Pôr do Sol",
          "AGUA QUENTE": "Água Quente"}  # a fonte grafa sem acento


def title(nome: str) -> str:
    small = {"de", "da", "do", "das", "dos", "e"}
    palavras = (nome or "").lower().split()
    return " ".join(p if p in small and i else p.capitalize() for i, p in enumerate(palavras))


def ra_name(raw: str) -> str:
    return RA_FIX.get(raw, title(raw))


def ring_area_centroid(ring: list[list[float]]) -> tuple[float, float, float]:
    """Área em m² e centroide (lon, lat) de um anel em graus (aproximação local)."""
    lat0 = sum(p[1] for p in ring) / len(ring)
    kx, ky = 111320 * math.cos(math.radians(lat0)), 110540
    area2 = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        cross = x1 * y2 - x2 * y1
        area2 += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(area2) < 1e-15:
        return 0.0, sum(p[0] for p in ring) / len(ring), lat0
    return abs(area2) / 2 * kx * ky, cx / (3 * area2), cy / (3 * area2)


def point_in_ring(x: float, y: float, ring: list[list[float]]) -> bool:
    inside, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi:
            inside = not inside
        j = i
    return inside


def representative_point(rings: list[list[list[float]]]) -> tuple[float, float, float]:
    """(lat, lon, área m²): centroide do maior anel, ou um vértice médio se cair fora."""
    best = max((ring_area_centroid(r) + (r,) for r in rings), key=lambda t: t[0])
    area, lon, lat, ring = best
    if not point_in_ring(lon, lat, ring):
        lon = sum(p[0] for p in ring) / len(ring)
        lat = sum(p[1] for p in ring) / len(ring)
    return round(lat, 6), round(lon, 6), round(area)


def ra_of(lon: float, lat: float, regions: list[tuple[str, list]]) -> str | None:
    for name, rings in regions:
        if sum(1 for r in rings if point_in_ring(lon, lat, r)) % 2 == 1:
            return name
    return None


def distance_m(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    return math.hypot((a_lat - b_lat) * 110540, (a_lon - b_lon) * 111320 * math.cos(math.radians(a_lat)))


def is_duplicate(lat: float, lon: float, kinds: set[str], radius: float, places: list[dict]) -> bool:
    return any(
        p.get("t") in kinds and p.get("lat") is not None
        and abs(p["lat"] - lat) < 0.001 and abs(p["lon"] - lon) < 0.001
        and distance_m(lat, lon, p["lat"], p["lon"]) <= radius
        for p in places
    )


def clean(value) -> str:
    text = " ".join(str(value or "").replace("_", " ").split())
    return "" if text.casefold() in {"", "<null>", "null", "none"} else text


def to_record(feature: dict, regions: list, places: list[dict]) -> dict | None:
    attrs, geom = feature["attributes"], feature.get("geometry") or {}
    code = attrs.get("ec_tipo")
    if code not in TIPOS or not geom.get("rings"):
        return None
    kind, label, mods, radius, compare = TIPOS[code]
    lat, lon, area = representative_point(geom["rings"])
    region = ra_of(lon, lat, regions)
    if not region or is_duplicate(lat, lon, compare, radius, places):
        return None
    address = clean(attrs.get("ec_endereco"))
    name = clean(attrs.get("ec_nome"))
    year = attrs.get("ec_ano")
    if name and label.casefold() in name.casefold():
        title_text = title(name)  # nome próprio já diz o tipo: "Praça dos Cristais"
    else:
        # "QC 04 PRAÇA" vira "Praça – QC 04", sem repetir o tipo no nome
        where = re.sub(rf"\b{label}\b", "", name or address, flags=re.I).strip(" -–,") or region
        title_text = f"{label} – {where}"
    record = {
        "id": f"epc-{attrs['objectid']}",
        "n": title_text,
        "t": kind,
        "ra": region,
        "end": address or None,
        "lat": lat,
        "lon": lon,
        "mods": mods,
        "mods_inferidas": bool(mods),
        "custo": "Gratuito (espaço público)",
        "gratis": True,
        "acc": {},
        "fonte": "IDE-DF / SEDUH – camada Espaços comunitários",
        "url": CAMADA,
        "data": str(year) if isinstance(year, int) and 1990 < year < 2100 else None,
        "geo": "Centroide da poligonal oficial do espaço",
        "area_m2": area,
        "obs": (
            f"Área no cadastro: {area:,} m².".replace(",", ".")
            + ("" if address else " Sem endereço no cadastro; a região vem da poligonal oficial da RA.")
            + " Tipo confirmado pelo Guia dos Espaços Públicos de Lazer do DF (UnB)."
        ),
    }
    return record


def fetch_json(url: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    with urllib.request.urlopen(f"{url}?{query}", timeout=90) as response:
        data = json.load(response)
    if "error" in data:
        raise RuntimeError(f"{url}: {data['error']}")
    return data


def fetch_features(url: str, where: str, fields: str) -> list[dict]:
    features, offset = [], 0
    while True:
        data = fetch_json(url + "/query", {
            "where": where, "outFields": fields, "outSR": 4326, "f": "json",
            "orderByFields": "objectid", "resultOffset": offset, "resultRecordCount": 1000,
        })
        batch = data.get("features", [])
        features += batch
        if not batch or not data.get("exceededTransferLimit"):
            return features
        offset += len(batch)
        time.sleep(0.3)


def read_places(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.PA_LOCAIS\s*=\s*(\[.*\]);?\s*$", text, re.S)
    places = json.loads(match.group(1)) if match else []
    # Os registros deste importador ("epc-") não contam como duplicata de si mesmos:
    # rodar de novo sobre a base já publicada dá o mesmo resultado.
    return [p for p in places if not str(p.get("id", "")).startswith("epc-")]


def build(features: list[dict], regions: list, places: list[dict]) -> list[dict]:
    """Converte e deduplica: contra a base publicada e entre os próprios novos."""
    result: list[dict] = []
    for feature in sorted(features, key=lambda f: f["attributes"]["objectid"]):
        record = to_record(feature, regions, places + result)
        if record:
            result.append(record)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="data/locais.js")
    parser.add_argument("--saida", default="data/curadoria/espacos_comunitarios.json")
    args = parser.parse_args()

    ras = fetch_features(LIMITES_RA, "1=1", "ra_nome")
    regions = [(ra_name(f["attributes"]["ra_nome"]), f["geometry"]["rings"]) for f in ras if f.get("geometry")]
    codes = ",".join(str(c) for c in TIPOS)
    features = fetch_features(CAMADA, f"ec_tipo IN ({codes})", "*")
    places = read_places(Path(args.base))
    records = build(features, regions, places)

    out = Path(args.saida)
    out.write_text(json.dumps(records, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    by_kind: dict[str, int] = {}
    for r in records:
        by_kind[r["t"]] = by_kind.get(r["t"], 0) + 1
    print(f"{len(features)} polígonos lidos; {len(records)} novos locais gravados em {out}: {by_kind}")


if __name__ == "__main__":
    main()
