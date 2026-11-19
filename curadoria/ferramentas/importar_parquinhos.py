"""Importa os parquinhos (parques infantis) da camada oficial "Mobiliário Esporte e Lazer" (IDE-DF).

A camada (SEDUH, EQUIPAMENTOS_URBANOS/MapServer/6) é a mesma de onde vêm os PECs, as
quadras e os campos do mapa. O tipo "PARQUE INFANTIL" aparece com quatro grafias
(espaço ou sublinhado, às vezes com espaço no fim); todas viram o tipo "parquinho".
O levantamento é da DIEP/SEGETH, quase todo de 2015, por isso cada registro leva a
data e o aviso de confirmar no local.

Saída: data/curadoria/parquinhos.json, no formato dos registros de site/data/locais.js;
ferramentas/gerar_base.py incorpora o arquivo na base candidata.

Uso (na pasta curadoria):
    python3 -B ferramentas/importar_parquinhos.py
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
from pathlib import Path

try:  # executado como script (python3 ferramentas/importar_parquinhos.py)
    from importar_espacos_comunitarios import LIMITES_RA, clean, fetch_features, is_duplicate, ra_name, ra_of
except ImportError:  # importado pelos testes (ferramentas.importar_parquinhos)
    from ferramentas.importar_espacos_comunitarios import (
        LIMITES_RA, clean, fetch_features, is_duplicate, ra_name, ra_of,
    )

CAMADA = "https://www.geoservicos.ide.df.gov.br/arcgis/rest/services/Publico/EQUIPAMENTOS_URBANOS/MapServer/6"
GRAFIAS = ("PARQUE INFANTIL", "PARQUE INFANTIL ", "PARQUE_INFANTIL", "PARQUE_INFANTIL ")
TIPO = "parquinho"
RAIO_DUPLICATA_M = 15  # dois registros do mesmo parquinho no levantamento ficam a poucos metros
RAIO_MESMO_ENDERECO_M = 30  # com o mesmo endereço, registros até 30 m são o mesmo parquinho
PREFIXO = "pin-"


def eh_parquinho(valor) -> bool:
    return " ".join(str(valor or "").replace("_", " ").split()).upper() == "PARQUE INFANTIL"


def endereco(raw) -> str:
    """Padroniza o endereço do cadastro: "QR827" -> "QR 827", "QNG 7/ CNG 1" -> "QNG 7/CNG 1"."""
    texto = clean(raw)
    texto = re.sub(r"\b([A-Z]{1,6})(\d)", r"\1 \2", texto)  # sigla colada no número
    texto = re.sub(r"\s*/\s*", "/", texto)                  # barra sem espaços, como "EQ 208/308"
    texto = re.sub(r"\bS/N\b", "S/N", texto)
    return " ".join(texto.split()).strip(" -–,")


def to_record(feature: dict, regions: list, places: list[dict]) -> dict | None:
    attrs, geom = feature["attributes"], feature.get("geometry") or {}
    if not eh_parquinho(attrs.get("elm_tp_mobiliario")):
        return None
    try:  # um registro do cadastro vem com coordenada "NaN" (sem ponto no mapa): fica de fora
        lat, lon = round(float(geom["y"]), 6), round(float(geom["x"]), 6)
    except (KeyError, TypeError, ValueError):
        return None
    if lat != lat or lon != lon:  # NaN
        return None
    regiao = ra_of(lon, lat, regions)
    if regiao and regiao.casefold() == "sudoeste/octogonal":
        regiao = "Sudoeste/Octogonal"  # o título automático deixaria "octogonal" em minúscula
    end = endereco(attrs.get("elm_endereco"))
    mesmo_endereco = [p for p in places if end and p.get("end") == end]
    if (not regiao or is_duplicate(lat, lon, {TIPO}, RAIO_DUPLICATA_M, places)
            or is_duplicate(lat, lon, {TIPO}, RAIO_MESMO_ENDERECO_M, mesmo_endereco)):
        return None
    quando = attrs.get("elm_data_atual")
    data = datetime.datetime.fromtimestamp(quando / 1000, datetime.timezone.utc).strftime("%m/%Y") if quando else None
    conservacao = clean(attrs.get("elm_est_conser")).title() or None
    record = {
        "id": f"{PREFIXO}{attrs['objectid_12']}",
        "n": f"Parquinho – {end or regiao}",
        "t": TIPO,
        "ra": regiao,
        "end": end or None,
        "lat": lat,
        "lon": lon,
        "mods": ["brincadeiras infantis"],
        "mods_inferidas": True,
        "custo": "Gratuito (espaço público)",
        "gratis": True,
        "luz": {"SIM": True, "NAO": False}.get(clean(attrs.get("elm_ilum_pub")).upper()),
        "acc": {},
        "fonte": "IDE-DF / SEDUH – camada Mobiliário Esporte e Lazer (levantamento DIEP/SEGETH)",
        "url": CAMADA,
        "data": data,
        "reviewed_at": datetime.date.today().isoformat(),  # data desta importação
        "obs": (
            f"Parque infantil do cadastro oficial (levantamento de {data[-4:] if data else 'data não informada'}). "
            "Os brinquedos e o estado atual podem ter mudado: confirme no local."
        ),
    }
    if conservacao:  # como nos PECs, o campo só aparece quando o cadastro informa
        record["cons"] = conservacao
    return record


def read_places(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\.PA_LOCAIS\s*=\s*(\[.*\]);?\s*$", text, re.S)
    places = json.loads(match.group(1)) if match else []
    # Os próprios parquinhos ("pin-") não contam como duplicata: rodar de novo dá o mesmo resultado.
    return [p for p in places if not str(p.get("id", "")).startswith(PREFIXO)]


def build(features: list[dict], regions: list, places: list[dict]) -> list[dict]:
    """Converte e tira duplicatas, contra a base publicada e entre os próprios parquinhos."""
    result: list[dict] = []
    for feature in sorted(features, key=lambda f: f["attributes"]["objectid_12"]):
        record = to_record(feature, regions, places + result)
        if record:
            result.append(record)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="../site/data/locais.js")
    parser.add_argument("--saida", default="data/curadoria/parquinhos.json")
    args = parser.parse_args()

    ras = fetch_features(LIMITES_RA, "1=1", "ra_nome")
    regions = [(ra_name(f["attributes"]["ra_nome"]), f["geometry"]["rings"]) for f in ras if f.get("geometry")]
    grafias = ",".join("'" + g + "'" for g in GRAFIAS)
    features = fetch_features_mobiliario(f"elm_tp_mobiliario IN ({grafias})")
    records = build(features, regions, read_places(Path(args.base)))

    out = Path(args.saida)
    out.write_text(json.dumps(records, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    sem_regiao = len(features) - len(records)
    print(f"{len(features)} parquinhos lidos; {len(records)} gravados em {out} "
          f"({sem_regiao} fora das RAs ou repetidos).")


def fetch_features_mobiliario(where: str) -> list[dict]:
    """A camada 6 ordena por objectid_12 (não tem o campo objectid)."""
    import time
    try:
        from importar_espacos_comunitarios import fetch_json
    except ImportError:
        from ferramentas.importar_espacos_comunitarios import fetch_json
    features, offset = [], 0
    while True:
        data = fetch_json(CAMADA + "/query", {
            "where": where, "outFields": "*", "outSR": 4326, "f": "json",
            "orderByFields": "objectid_12", "resultOffset": offset, "resultRecordCount": 1000,
        })
        batch = data.get("features", [])
        features += batch
        if not batch or not data.get("exceededTransferLimit"):
            return features
        offset += len(batch)
        time.sleep(0.3)


if __name__ == "__main__":
    main()
