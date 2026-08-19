#!/usr/bin/env python3
"""Comparar rookies del punto de mira (2025-26) contra top 5 históricos (2021-22..2024-25).
Métricas: USG%, PTS/G, TRB/G, AST/G, STL/G, BLK/G, MPG, TS% — solo medias reales y totales.
Distancia euclidiana sobre z-scores del pool histórico.
"""
import re, json, math

CAMPOS = ["player", "g", "mp", "pts", "trb", "ast", "stl", "blk",
          "pts_per_g", "trb_per_g", "ast_per_g", "stl_per_g", "blk_per_g", "mp_per_g"]
ADV = ["name_display", "usg_pct", "ts_pct", "per", "bpm"]
METRICAS = ["usg", "pts_per_g", "trb_per_g", "ast_per_g", "stl_per_g", "blk_per_g", "mp_per_g", "ts"]

def parse_table(html, campos):
    rows = []
    for tr in re.finditer(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        block = tr.group(1)
        if "<td" not in block:
            continue
        row = {}
        for c in campos:
            m = re.search(r'<t[dh][^>]*data-stat="' + c + r'"[^>]*>(.*?)</t[dh]>', block, re.S)
            if m:
                row[c] = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if ("player" in row and row["player"]) or ("name_display" in row and row["name_display"]):
            rows.append(row)
    return rows

def f(x):
    if x is None:
        return None
    x = x.replace(",", "")
    try:
        return float(x)
    except (ValueError, AttributeError):
        return None

def norm(n):
    n = n.replace("*", "").strip()
    return n.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ñ","n").replace("Á","A").replace("É","E").replace("Í","I").replace("Ó","O").replace("Ú","U").replace("Ñ","N").replace("Ş","S").replace("ğ","g").replace("ü","u")

# cargar pool histórico completo (2021-22 a 2024-25), top 5 por PTS
hist = []
for y in [2022, 2023, 2024, 2025]:
    rows = parse_table(open(f"/tmp/rookies_{y}.html").read(), CAMPOS)
    clean = []
    for r in rows:
        d = {"player": norm(r.get("player", "")), "anio": y}
        for c in CAMPOS[1:]:
            d[c] = f(r.get(c, ""))
        if d["g"] and d["pts"]:
            clean.append(d)
    clean.sort(key=lambda r: r["pts"], reverse=True)
    adv = {}
    for r in parse_table(open(f"/tmp/adv_{y}.html").read(), ADV):
        n = norm(r.get("name_display", ""))
        if n:
            adv[n] = {c: f(r.get(c, "")) for c in ADV[1:]}
    for r in clean[:5]:
        a = adv.get(r["player"], {})
        r["usg"] = a.get("usg_pct")
        r["ts"] = a.get("ts_pct")
        r["per"] = a.get("per")
        r["bpm"] = a.get("bpm")
        hist.append(r)

# rookies 2025-26: los del punto de mira (Flagg, Knueppel, Edgecombe, Hugo, Harper)
# top 5 + buscar Hugo y Harper en la tabla completa
rows26 = parse_table(open("/tmp/rookies_2026.html").read(), CAMPOS)
cur = []
for r in rows26:
    d = {"player": norm(r.get("player", "")), "anio": 2026}
    for c in CAMPOS[1:]:
        d[c] = f(r.get(c, ""))
    if d["g"] and d["pts"]:
        cur.append(d)
adv26 = {}
for r in parse_table(open("/tmp/adv_2026.html").read(), ADV):
    n = norm(r.get("name_display", ""))
    if n:
        adv26[n] = {c: f(r.get(c, "")) for c in ADV[1:]}
for r in cur:
    a = adv26.get(r["player"], {})
    r["usg"] = a.get("usg_pct")
    r["ts"] = a.get("ts_pct")

objetivo = ["Kon Knueppel", "Cooper Flagg", "VJ Edgecombe", "Hugo Gonzalez", "Dylan Harper"]
act = [r for r in cur if r["player"] in objetivo]

# z-scores sobre pool histórico
def zscore(v, vals):
    if v is None:
        return None
    vs = [x for x in vals if x is not None]
    mu = sum(vs) / len(vs)
    sd = math.sqrt(sum((x - mu) ** 2 for x in vs) / len(vs)) or 1
    return (v - mu) / sd

hist_vals = {m: [r[m] for r in hist if r.get(m) is not None] for m in METRICAS}

def vector(r):
    return [zscore(r.get(m), hist_vals[m]) for m in METRICAS]

def dist(a, b):
    d = 0
    for x, y in zip(a, b):
        if x is None or y is None:
            continue
        d += (x - y) ** 2
    return math.sqrt(d)

print("=== LOS 3 ROOKIES HISTÓRICOS MÁS PARECIDOS A CADA UNO DEL PUNTO DE MIRA ===\n")
for r in act:
    v = vector(r)
    scores = []
    for h in hist:
        d = dist(v, vector(h))
        if d < 1e9:
            scores.append((d, h))
    scores.sort(key=lambda x: x[0])
    print(f"🎯 {r['player']} ({r['anio']-1}-{str(r['anio'])[2:]}) — USG {r['usg']:.1f} | {r['pts_per_g']:.1f}pts {r['trb_per_g']:.1f}reb {r['ast_per_g']:.1f}ast {r['stl_per_g']:.1f}stl {r['blk_per_g']:.1f}blk {r['mp_per_g']:.0f}min")
    for d, h in scores[:3]:
        print(f"   #{scores.index((d,h))+1} {h['player']} ({h['anio']-1}-{str(h['anio'])[2:]}) — USG {h['usg']:.1f} | {h['pts_per_g']:.1f}pts {h['trb_per_g']:.1f}reb {h['ast_per_g']:.1f}ast | dist {d:.2f}")
    print()
