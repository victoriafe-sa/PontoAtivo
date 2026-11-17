"""Monta data/locais.js (base de locais do PontoAtivo – Brasília/DF) a partir das fontes baixadas.
Uso: python build.py <pasta geo> <ibram_parks.json> <saida.js>
"""
import json, sys, glob, os, re, unicodedata, datetime, math

GEO, IBRAM, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
ACCESSED = "05/11/2026"

def norm(s):
  return unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower().strip()

def title(s):
  small = {"de", "da", "do", "das", "dos", "e"}
  w = (s or "").lower().split()
  return " ".join(x if x in small and i else x.capitalize() for i, x in enumerate(w))

# ---------- Regiões administrativas (polígonos oficiais) ----------
RA_FIX = {"SCIA": "SCIA/Estrutural", "SIA": "SIA", "SOL NASCENTE E POR DO SOL": "Sol Nascente/Pôr do Sol"}
ras = []
for f in json.load(open(os.path.join(GEO, "ras.json")))["features"]:
  name = f["attributes"]["ra_nome"]
  ras.append((RA_FIX.get(name, title(name)), f["geometry"]["rings"]))

def pip(x, y, ring):
  inside = False
  j = len(ring) - 1
  for i in range(len(ring)):
    xi, yi = ring[i]; xj, yj = ring[j]
    if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi:
      inside = not inside
    j = i
  return inside

def ra_of(lon, lat):
  for name, rings in ras:
    c = sum(1 for r in rings if pip(lon, lat, r))
    if c % 2 == 1:
      return name
  return None

def same_ra(expected, found):
  if not expected or not found:
    return False
  e, f = norm(expected), norm(found)
  return e.split("/")[0].split()[0] in f or f.split("/")[0].split()[0] in e

out = []

# ---------- 1) Mobiliário de esporte e lazer (IDE-DF) ----------
TYPE_MAP = [
  ("PEC", "pec", "PEC – Ponto de Encontro Comunitário", ["exercícios ao ar livre", "alongamento", "caminhada"]),
  ("QUADRA POLIESPORTIVA", "quadra", "Quadra poliesportiva", ["futebol", "vôlei", "basquete", "handebol"]),
  ("QUADRA_POLIESPORTIVA", "quadra", "Quadra poliesportiva", ["futebol", "vôlei", "basquete", "handebol"]),
  ("QUADRA DE AREIA", "areia", "Quadra de areia", ["vôlei de areia", "futevôlei", "beach tennis"]),
  ("QUADRA DE TENIS", "tenis", "Quadra de tênis", ["tênis"]),
  ("CAMPO SINTETICO", "campo", "Campo sintético", ["futebol"]),
  ("CAMPO DE GRAMA SINTETICA", "campo", "Campo sintético", ["futebol"]),
  ("CAMPO ILUMINADO", "campo", "Campo de futebol iluminado", ["futebol"]),
  ("CAMPO DE FUTEBOL", "campo", "Campo de futebol", ["futebol"]),
  ("CAMPO TERRA BATIDA", "campo", "Campo de terra batida", ["futebol"]),
  ("CAMPO DE TERRA BATIDA", "campo", "Campo de terra batida", ["futebol"]),
  ("CAMPO_DE_TERRA_BATIDA", "campo", "Campo de terra batida", ["futebol"]),
  ("SKATE PARK", "skate", "Pista de skate", ["skate", "patins"]),
  ("SKATE_PARQUE", "skate", "Pista de skate", ["skate", "patins"]),
  ("APARELHO DE GINASTICA", "ginastica", "Aparelhos de ginástica", ["exercícios ao ar livre"]),
]
tmap = {k: v for k, *v in TYPE_MAP}
seen = set()
for fp in sorted(glob.glob(os.path.join(GEO, "mob_*.json"))):
  for f in json.load(open(fp)).get("features", []):
    a, g = f["attributes"], f.get("geometry")
    tp = (a.get("elm_tp_mobiliario") or "").strip()
    if tp not in tmap or not g:
      continue
    key = (tp, round(g["x"], 5), round(g["y"], 5))
    if key in seen:
      continue
    seen.add(key)
    t, label, mods = tmap[tp]
    end = re.sub(r"_+", " ", a.get("elm_endereco") or "").strip()
    end = re.sub(r"\b(QR|QN|QS|QNM|QNN|QNO|QNP|QE|QI|CJ|SQS|SQN|AE)(\d)", r"\1 \2", end)
    dt = a.get("elm_data_atual")
    data = datetime.datetime.utcfromtimestamp(dt / 1000).strftime("%m/%Y") if dt else None
    ra = ra_of(g["x"], g["y"])
    out.append({
      "id": f"ide-{a['objectid_12']}", "n": f"{label}{' – ' + end if end else ''}", "t": t, "ra": ra,
      "end": end or None, "lat": round(g["y"], 6), "lon": round(g["x"], 6), "mods": mods, "custo": "Gratuito (espaço público)",
      "gratis": True, "cons": (a.get("elm_est_conser") or "").strip().title() or None,
      "luz": {"SIM": True, "NAO": False}.get((a.get("elm_ilum_pub") or "").strip().upper()),
      "acc": {}, "fonte": "IDE-DF / SEDUH – camada Mobiliário Esporte e Lazer (levantamento DIEP/SEGETH)",
      "url": "https://www.geoservicos.ide.df.gov.br/arcgis/rest/services/Publico/EQUIPAMENTOS_URBANOS/MapServer/6",
      "data": data, "mods_inferidas": True,
    })

# ---------- 2) Parques urbanos (IDE-DF) ----------
for f in json.load(open(os.path.join(GEO, "parques.json")))["features"]:
  a, g = f["attributes"], f.get("geometry")
  rings = g.get("rings") if g else None
  if not rings:
    continue
  pts = [p for r in rings for p in r]
  lon = sum(p[0] for p in pts) / len(pts); lat = sum(p[1] for p in pts) / len(pts)
  nome = title(a.get("pqu_nome") or "Parque urbano").replace("Ãº", "ú")
  if "sarah kubitschek" in norm(nome):
    continue  # já incluído pela SEL-DF (Parque da Cidade)
  out.append({
    "id": f"pqu-{a['objectid']}", "n": nome, "t": "parque", "ra": ra_of(lon, lat), "end": None,
    "lat": round(lat, 6), "lon": round(lon, 6), "mods": ["caminhada", "lazer ao ar livre"], "custo": "Gratuito",
    "gratis": True, "acc": {}, "fonte": "IDE-DF / SEDUH – camada Parques Urbanos",
    "url": "https://www.geoservicos.ide.df.gov.br/arcgis/rest/services/Publico/EQUIPAMENTOS_URBANOS/MapServer/7",
    "data": None, "mods_inferidas": True, "obs": "Posição = centro aproximado da poligonal do parque.",
  })

# ---------- 3) Locais nomeados (COPs, SEL, Ibram, paradesporto) ----------
geo = json.load(open(os.path.join(GEO, "geocache.json")))
SEL_COP = "https://www.esporte.df.gov.br/cops"
SEL_ESP = "https://www.esporte.df.gov.br/espacos-esportivos"
COP_MODS = ["várias modalidades olímpicas", "modalidades paralímpicas", "atividades para idosos"]
COP_OBS = ("Programa gratuito da Secretaria de Esporte e Lazer, para público a partir de 4 anos, "
           "incluindo pessoas com deficiência. Matrícula por edital (Edital 001/2026). "
           "Contato geral: (61) 2017-3021 · subcop@esporte.df.gov.br")
NAMED = [
  ("cop-brazlandia", "COP Brazlândia", "cop", "Brazlândia", "Bairro Vila São José, Quadra 35, Área Especial 22", "Ramal 2022"),
  ("cop-recanto", "COP Recanto das Emas", "cop", "Recanto das Emas", "Avenida Ponte Alta, Quadra 604, Área Especial", "Ramal 2037"),
  ("cop-setor-o", "COP Ceilândia – Setor O", "cop", "Ceilândia", "QNO 09, Conjunto 01, Lote 01", "Ramal 2024"),
  ("cop-santa-maria", "COP Santa Maria", "cop", "Santa Maria", "Quadra Central 3, Área Especial 4, Santa Maria Norte", "Ramal 2019"),
  ("cop-vaquejada", "COP Ceilândia – Parque da Vaquejada", "cop", "Sol Nascente", "QNP 21, AE – Setor Habitacional Sol Nascente, Setor P Norte", "Ramal 2026"),
  ("cop-sobradinho", "COP Sobradinho", "cop", "Sobradinho", "Quadra 02, Área Especial de 01 a 05", "Ramal 2027"),
  ("cop-estrutural", "COP Estrutural", "cop", "SCIA/Estrutural", "SCIA, Área Especial 02, Setor Norte", "Ramal 2021"),
  ("cop-sao-sebastiao", "COP São Sebastião", "cop", "São Sebastião", "Quadra 1, Bairro São Bartolomeu", "Ramal 2034"),
  ("cop-gama", "COP Gama", "cop", "Gama", "SCE Quadra 55, 119 Área Especial", "Ramal 2015"),
  ("cop-riacho", "COP Riacho Fundo I", "cop", "Riacho Fundo", "QS 16, Área Especial F", "Ramal 2028"),
  ("cop-planaltina", "COP Planaltina", "cop", "Planaltina", "Setor Recreativo e Cultural, Módulo Esportivo (ao lado do Restaurante Comunitário)", "Ramal 2023"),
  ("cop-samambaia", "COP Samambaia", "cop", "Samambaia", "QS 119, Área Especial 01, Centro Urbano, Samambaia Sul", "Ramal 2036"),
]
for key, nome, t, ra, end, ramal in NAMED:
  out.append({"id": key, "n": nome, "t": t, "ra_fonte": ra, "end": end, "mods": COP_MODS, "custo": "Gratuito (matrícula por edital)",
              "gratis": True, "acc": {"adaptado": "info"}, "fonte": "Secretaria de Esporte e Lazer do DF – Centros Olímpicos e Paralímpicos",
              "url": SEL_COP, "data": ACCESSED, "tel": f"(61) 2017-3021 {ramal}", "obs": COP_OBS, "_geo": key})

SEL = [
  ("sel-parque-cidade", "Parque da Cidade Dona Sarah Kubitschek", "parque", "Plano Piloto", "Asa Sul (Eixo Monumental / SRPS)",
   ["caminhada", "corrida", "ciclismo", "patins", "futebol", "vôlei", "tênis", "basquete"], "Gratuito",
   "Maior parque urbano de Brasília: pistas de caminhada, ciclovia, quadras poliesportivas, de vôlei, tênis e futebol (Wikipedia, dados de 2019). Administrado pela SEL-DF."),
  ("sel-claudio-coutinho", "Parque Aquático Cláudio Coutinho", "estadio", "Plano Piloto", "SRPN, Complexo Esportivo Ayrton Senna",
   ["natação"], "Locação via SEL-DF", "Listado pela SEL-DF como espaço esportivo. A Wikipedia o descreve como interditado; confirme o funcionamento antes de ir."),
  ("sel-bezerrao", "Estádio Bezerrão", "estadio", "Gama", "Avenida JK, Setor Central", ["futebol"], "Locação via SEL-DF", "Espaço esportivo da SEL-DF para eventos (Portaria 264/2023)."),
  ("sel-rorizao", "Estádio Joaquim Domingos Roriz", "estadio", "Samambaia", "Avenida Central, ADE Sul", ["futebol"], "Locação via SEL-DF", "Espaço esportivo da SEL-DF para eventos (Portaria 264/2023)."),
  ("sel-augustinho", "Estádio Augustinho Lima", "estadio", "Sobradinho", "Quadra 14, Vila Dnocs", ["futebol"], "Locação via SEL-DF", "Espaço esportivo da SEL-DF para eventos (Portaria 264/2023)."),
  ("sel-abadiao", "Estádio Maria de Lourdes Abadia (Abadião)", "estadio", "Ceilândia", "QNN 14, Setor N Norte", ["futebol"], "Locação via SEL-DF", "Espaço esportivo da SEL-DF para eventos (Portaria 264/2023)."),
  ("sel-ginasio-samambaia", "Ginásio de Esportes de Samambaia", "estadio", "Samambaia", None, ["futsal", "vôlei", "basquete", "handebol"], "Locação via SEL-DF", "Espaço esportivo da SEL-DF para eventos (Portaria 264/2023)."),
]
for key, nome, t, ra, end, mods, custo, obs in SEL:
  out.append({"id": key, "n": nome, "t": t, "ra_fonte": ra, "end": end, "mods": mods, "custo": custo, "gratis": custo == "Gratuito",
              "acc": {}, "fonte": "Secretaria de Esporte e Lazer do DF – Espaços Esportivos", "url": SEL_ESP, "data": ACCESSED, "obs": obs, "_geo": key})

out.append({"id": "para-cetefe", "n": "CETEFE – Centro de Treinamento de Educação Física Especial", "t": "para", "ra_fonte": "Plano Piloto",
            "end": "Ginásio da Enap (subsolo), Setor de Áreas Isoladas Sul – Asa Sul", "mods": ["16 modalidades adaptadas", "bocha", "atletismo", "goalball", "tênis em cadeira de rodas"],
            "custo": "Informar-se com a entidade", "gratis": False, "acc": {"adaptado": "info"},
            "fonte": "Metrópoles; Agência Gov (2023); Jornal de Brasília", "url": "https://agenciagov.ebc.com.br/noticias/202310/enap-reinaugura-complexo-esportivo-utilizado-por-atletas-paralimpicos-de-alto-nivel",
            "data": ACCESSED, "obs": "ONG de paradesporto, parceira da Secretaria de Educação. Oferece modalidades adaptadas em três turnos, com avaliação funcional na inscrição. Endereço e telefone atuais a confirmar.", "_geo": "para-cetefe-enap"})
out.append({"id": "unb-co", "n": "Centro Olímpico da UnB", "t": "estadio", "ra_fonte": "Plano Piloto", "end": "Campus Darcy Ribeiro, Asa Norte",
            "mods": ["natação", "atletismo", "várias modalidades"], "custo": "Programas da UnB (ver site)", "gratis": False, "acc": {},
            "fonte": "UnB – Coordenação de Esporte e Lazer", "url": "https://esporte.unb.br/programas-e-acoes/", "data": ACCESSED,
            "obs": "Contato: esporte@unb.br", "_geo": "unb-centro-olimpico"})

for i, p in enumerate(json.load(open(IBRAM))):
  ra = p["ra"].replace("Santa maria", "Santa Maria").replace("Sol Nascente/Pôr do sol", "Sol Nascente")
  out.append({"id": f"ibram-{i}", "n": p["nome"].replace("´", "'"), "t": "parque", "ra_fonte": ra, "end": None,
              "mods": ["caminhada", "contato com a natureza"], "custo": "Gratuito", "gratis": True, "acc": {},
              "fonte": f"Brasília Ambiental (Ibram) – tabela de Unidades de Conservação (ago/2026); categoria: {p['categoria']}",
              "url": "https://www.ibram.df.gov.br/unidades-de-conservacao", "data": "08/2026", "mods_inferidas": True,
              "obs": "Infraestrutura (pistas, PEC, quadras) não informada na fonte oficial.", "_geo": f"ibram-{i}"})

import math
APPROX = {"cop-riacho", "cop-samambaia", "cop-brazlandia", "para-cetefe-enap"}
def dist_to_ra(expected, lon, lat):
  best = 1e9
  for name, rings in ras:
    if not same_ra(expected, name):
      continue
    for ring in rings:
      for x, y in ring:
        d = math.hypot((x - lon) * 107.0, (y - lat) * 111.0)
        best = min(best, d)
  return best

# Geolocalização dos nomeados, validada pela RA oficial
pend = 0
for r in out:
  k = r.pop("_geo", None)
  if k is None:
    continue
  hit = geo.get(k)
  r["ra"] = r.pop("ra_fonte")
  if hit:
    found = ra_of(hit["lon"], hit["lat"])
    near = not same_ra(r["ra"], found) and dist_to_ra(r["ra"], hit["lon"], hit["lat"]) < 3.0
    if same_ra(r["ra"], found) or near:
      r["lat"], r["lon"] = round(hit["lat"], 6), round(hit["lon"], 6)
      r["geo"] = "OpenStreetMap (Nominatim), conferido com o limite oficial da RA" + (" (ponto próximo à divisa)" if near else "")
      if k in APPROX:
        r["aprox"] = True
        r["geo"] = "Aproximada: OpenStreetMap localizou apenas o bairro/setor"
      continue
  r["lat"] = r["lon"] = None
  r["geo"] = "Localização exata pendente"
  pend += 1

# ---------- 4) Campos de futebol do OpenStreetMap (complementa a IDE-DF) ----------
# Fonte: Overpass API, leisure=pitch + sport~soccer dentro do DF (ver LEIA-ME). Só entram gramados/terra/sintético
# ou recintos de tamanho de campo; quadras de concreto ficam de fora (já vêm da IDE-DF). Privados são descartados.
OSM = os.path.join(GEO, "osm_pitches.json")
if not os.path.exists(OSM):
  OSM = os.path.join(os.path.dirname(__file__), "osm_pitches.json")
SURF = {"grass": "grama natural", "artificial_turf": "grama sintética", "sand": "areia", "ground": "terra",
        "earth": "terra", "dirt": "terra", "gravel": "terra/cascalho", "unpaved": "terra"}
HARD = {"concrete", "paved", "asphalt", "paving_stones", "wood", "tartan", "acrylic", "rubber"}
def osm_len(e):
  g = e.get("geometry") or []
  if len(g) < 2: return None
  lat0 = math.radians(g[0]["lat"])
  pts = [(q["lon"] * 111320 * math.cos(lat0), q["lat"] * 110540) for q in g if q]
  return max(math.dist(a, b) for a in pts for b in pts)
if os.path.exists(OSM):
  campos_ide = [(r["lat"], r["lon"]) for r in out if r["t"] in ("campo", "quadra") and r.get("lat") is not None]
  added = skipped = 0
  for e in json.load(open(OSM))["elements"]:
    tg = e.get("tags", {})
    sport, surf, acc = tg.get("sport", "").lower(), tg.get("surface", "").lower(), tg.get("access", "").lower()
    if "soccer" not in sport and "futebol" not in sport and "society" not in sport: skipped += 1; continue
    if acc in ("private", "no") or surf in HARD: skipped += 1; continue
    size = osm_len(e)
    if surf not in SURF and (size is None or size < 50): skipped += 1; continue  # sem piso informado: só se tiver porte de campo
    if e["type"] == "node": lat, lon = e["lat"], e["lon"]
    else:
      g = [q for q in e.get("geometry") or [] if q]
      center = e.get("center")
      if g:
        lat, lon = sum(q["lat"] for q in g) / len(g), sum(q["lon"] for q in g) / len(g)
      elif center:
        lat, lon = center["lat"], center["lon"]
      else:
        skipped += 1; continue
    ra = ra_of(lon, lat)
    if not ra: skipped += 1; continue
    if any(math.hypot((la - lat) * 111000, (lo - lon) * 107000) < 70 for la, lo in campos_ide): skipped += 1; continue
    campos_ide.append((lat, lon))
    nome = tg.get("name")
    piso = SURF.get(surf)
    tipo = "Campo society" if size and size < 70 else "Campo de futebol"
    end = " ".join(x for x in [tg.get("addr:street"), tg.get("addr:housenumber")] if x) or None
    paid = acc in ("customers", "permit") or tg.get("fee") == "yes"
    ts = e.get("timestamp", "")
    out.append({
      "id": f"osm-{e['type'][0]}{e['id']}", "n": nome or f"{tipo}{' de ' + piso if piso else ''}", "t": "campo", "ra": ra,
      "end": end, "lat": round(lat, 6), "lon": round(lon, 6),
      "mods": ["futebol"] + (["futebol society"] if tipo == "Campo society" else []),
      "custo": "Pago / para clientes" if paid else ("Gratuito" if tg.get("fee") == "no" else "Acesso não informado"),
      "gratis": True if tg.get("fee") == "no" else None,
      "luz": {"yes": True, "no": False}.get(tg.get("lit")), "acc": {},
      "fonte": "OpenStreetMap (colaboradores) – leisure=pitch, sport=soccer",
      "url": f"https://www.openstreetmap.org/{e['type']}/{e['id']}",
      "data": f"{ts[5:7]}/{ts[:4]}" if ts else None, "mods_inferidas": False,
      "obs": ("Mapeado por voluntários do OpenStreetMap (data = última edição). Pode ficar dentro de escola, clube, "
              "condomínio ou área militar: confirme o acesso antes de ir." + (f" Piso: {piso}." if piso else "")
              + (f" Tamanho aproximado: {int(size)} m na maior dimensão." if size else "")),
    })
    added += 1
  print("OSM campos adicionados:", added, "descartados:", skipped)

# Limpeza de campos vazios
for r in out:
  for k in [k for k, v in r.items() if v in (None, "", [], {}) and k not in ("lat", "lon", "acc")]:
    del r[k]

with open(OUT, "w") as fh:
  fh.write("// Gerado automaticamente – base de locais PontoAtivo (Brasília/DF). Fontes em cada registro.\n")
  fh.write(f"window.PA_META = {json.dumps({'gerado': ACCESSED, 'total': len(out)}, ensure_ascii=False)};\n")
  fh.write("window.PA_LOCAIS = ")
  json.dump(out, fh, ensure_ascii=False, separators=(",", ":"))
  fh.write(";\n")

from collections import Counter
print("total", len(out), "pendentes", pend)
print(Counter(r["t"] for r in out))
print("sem RA:", sum(1 for r in out if not r.get("ra")))
print([ (r["n"], r["ra"]) for r in out if r.get("lat") is None][:60])
