"""Geocodifica locais nomeados (COPs, parques Ibram, espaços da SEL, paradesporto) via Nominatim/OSM.
Respeita 1 req/s e grava cache em JSON. Uso: python geocode.py <saida.json>
"""
import json, sys, time, urllib.parse, urllib.request, os

UA = "PontoAtivo-prototipo-academico/0.1"
VIEWBOX = "-48.29,-15.49,-47.30,-16.06"  # retângulo do DF

NAMED = [
  # (id, consulta principal, consultas alternativas)
  ("cop-brazlandia", "Centro Olímpico Brazlândia", ["Vila São José Brazlândia"]),
  ("cop-recanto", "Centro Olímpico Recanto das Emas", ["Quadra 604 Recanto das Emas"]),
  ("cop-setor-o", "Centro Olímpico Setor O Ceilândia", ["QNO 9 Ceilândia"]),
  ("cop-santa-maria", "Centro Olímpico Santa Maria", ["Santa Maria Distrito Federal"]),
  ("cop-vaquejada", "Parque da Vaquejada Ceilândia", ["Centro Olímpico Parque da Vaquejada", "QNP 21 Ceilândia"]),
  ("cop-sobradinho", "Centro Olímpico Sobradinho", ["Setor Esportivo Sobradinho"]),
  ("cop-estrutural", "Centro Olímpico Estrutural", ["Vila Estrutural"]),
  ("cop-sao-sebastiao", "Centro Olímpico São Sebastião", ["São Bartolomeu São Sebastião"]),
  ("cop-gama", "Centro Olímpico Gama", ["Setor Central Gama"]),
  ("cop-riacho", "Centro Olímpico Riacho Fundo", ["QS 16 Riacho Fundo"]),
  ("cop-planaltina", "Centro Olímpico Planaltina", ["Planaltina Distrito Federal"]),
  ("cop-samambaia", "Centro Olímpico Samambaia", ["QS 119 Samambaia"]),
  ("sel-ginasio-samambaia", "Ginásio de Esportes Samambaia", ["Ginásio Samambaia"]),
  ("sel-claudio-coutinho", "Parque Aquático Cláudio Coutinho", ["Complexo Aquático Cláudio Coutinho"]),
  ("sel-parque-cidade", "Parque da Cidade Sarah Kubitschek", ["Parque da Cidade Brasília"]),
  ("sel-bezerrao", "Estádio Bezerrão Gama", ["Bezerrão"]),
  ("sel-rorizao", "Estádio Joaquim Domingos Roriz", ["Rorizão Samambaia"]),
  ("sel-augustinho", "Estádio Augustinho Lima Sobradinho", ["Augustinho Lima"]),
  ("sel-abadiao", "Estádio Abadião Ceilândia", ["Abadião"]),
  ("para-cetefe-enap", "Escola Nacional de Administração Pública Brasília", ["ENAP Asa Sul"]),
  ("unb-centro-olimpico", "Centro Olímpico Universidade de Brasília", ["Centro Olímpico UnB"]),
]

def search(q):
  url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
    {"q": q + ", Distrito Federal, Brasil", "format": "json", "limit": 1, "viewbox": VIEWBOX, "bounded": 1})
  req = urllib.request.Request(url, headers={"User-Agent": UA})
  with urllib.request.urlopen(req, timeout=30) as r:
    res = json.load(r)
  time.sleep(1.1)
  return res[0] if res else None

def main(out, extra_names):
  cache = json.load(open(out)) if os.path.exists(out) else {}
  items = NAMED + [(f"ibram-{i}", n, []) for i, n in enumerate(extra_names)]
  for key, q, alts in items:
    if key in cache and cache[key]:
      continue
    hit = None
    for cand in [q] + alts:
      try:
        hit = search(cand)
      except Exception as e:
        print("erro", cand, e)
      if hit:
        cache[key] = {"q": cand, "lat": float(hit["lat"]), "lon": float(hit["lon"]), "osm": hit.get("display_name", "")[:160], "exact": cand == q}
        break
    if not hit:
      cache[key] = None
    print(key, "->", cache[key] and cache[key]["osm"][:80])
    json.dump(cache, open(out, "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
  names = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else []
  main(sys.argv[1], names)
