"""Cruza parques pendentes com polígonos oficiais Ibram/ONDA."""
from __future__ import annotations
import argparse, json, re, unicodedata
from pathlib import Path

ALIASES = {"irmao afonso haus":"irmaos afonso haus", "cachoeirinha e coqueirao":"cachoeirinha", "coqueirao e cachoeirinha":"cachoeirinha"}

def _plain(value):
    return unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode().lower()

def normalize_park_name(value):
    value = re.sub(r"\([^)]*\)", "", value or "")
    value = re.sub(r"\b(parque|ecologico|distrital|vivencial|urbano|e\s+de\s+uso\s+multiplo|de uso multiplo)\b", " ", _plain(value))
    value = re.sub(r"\b(da|de|do|das|dos)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value).strip()
    return ALIASES.get(value, value)

def point_in_ring(x, y, ring):
    inside, j = False, len(ring) - 1
    for i, (xi, yi) in enumerate(ring):
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj-xi)*(y-yi)/(yj-yi or 1e-15)+xi:
            inside = not inside
        j = i
    return inside

def point_in_geometry(x, y, geometry):
    return sum(point_in_ring(x, y, ring) for ring in geometry.get("rings", [])) % 2 == 1

def representative_point(geometry):
    rings = geometry.get("rings") or []
    points = [point for ring in rings for point in ring]
    if not points: raise ValueError("geometria sem pontos")
    minx, maxx = min(p[0] for p in points), max(p[0] for p in points)
    miny, maxy = min(p[1] for p in points), max(p[1] for p in points)
    candidates = [(sum(p[0] for p in points)/len(points), sum(p[1] for p in points)/len(points)), ((minx+maxx)/2,(miny+maxy)/2)]
    for steps in (20, 50, 100):
        candidates.extend((minx+(maxx-minx)*(i+.5)/steps, miny+(maxy-miny)*(j+.5)/steps) for i in range(steps) for j in range(steps))
        inside = [p for p in candidates if point_in_geometry(*p, geometry)]
        if inside:
            center = ((minx+maxx)/2,(miny+maxy)/2)
            return min(inside, key=lambda p:(p[0]-center[0])**2+(p[1]-center[1])**2)
    raise ValueError("não foi possível encontrar ponto interno")

def match_pending_parks(pending, features):
    index = {}
    for feature in features:
        attrs = feature.get("attributes", feature.get("properties", {}))
        name = attrs.get("nome") or attrs.get("NOME") or ""
        index.setdefault(normalize_park_name(name), []).append((name, feature))
    report = {"matched":[], "ambiguous":[], "unmatched":[]}
    for park in pending:
        key = normalize_park_name(park.get("name") or park.get("n"))
        hits = index.get(key, [])
        if len(hits) == 1:
            source_name, feature = hits[0]
            lon, lat = representative_point(feature["geometry"])
            report["matched"].append({**park,"source_name":source_name,"longitude":round(lon,6),"latitude":round(lat,6),"precision":"representative_point","source_id":"ibram_onda"})
        elif len(hits) > 1: report["ambiguous"].append(park.get("id"))
        else: report["unmatched"].append(park.get("id"))
    return report

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("features"); parser.add_argument("pending"); parser.add_argument("output")
    args=parser.parse_args()
    features=json.loads(Path(args.features).read_text())["features"]
    pending=json.loads(Path(args.pending).read_text())
    Path(args.output).write_text(json.dumps(match_pending_parks(pending,features),ensure_ascii=False,indent=2)+"\n")

if __name__ == "__main__": main()
