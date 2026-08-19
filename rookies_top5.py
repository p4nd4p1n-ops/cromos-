#!/usr/bin/env python3
"""Rookies top 5 de 5 temporadas (2021-22..2025-26): USG% + medias reales.
Compara perfiles y encuentra los 3 rookies históricos más parecidos a cada
rookie actual del punto de mira (por distancia euclidiana normalizada).
"""
import re, json, math

ANIOS = [2022, 2023, 2024, 2025, 2026]
CAMPOS = ["player", "g", "mp", "pts", "trb", "ast", "stl", "blk",
          "pts_per_g", "trb_per_g", "ast_per_g", "stl_per_g", "blk_per_g", "mp_per_g"]
ADV = ["name_display", "usg_pct", "ts_pct", "per", "bpm"]

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
                val = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                row[c] = val
        if "player" in row and row["player"] or "name_display" in row and row["name_display"]:
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
    return n.replace("*", "").strip()

# 1) top 5 rookies por año (per game + totales)
rookies = {}
for y in ANIOS:
    rows = parse_table(open(f"/tmp/rookies_{y}.html").read(), CAMPOS)
    clean = []
    for r in rows:
        d = {"player": norm(r.get("player", ""))}
        for c in CAMPOS[1:]:
            d[c] = f(r.get(c, ""))
        if d["g"] and d["pts"]:
            clean.append(d)
    clean.sort(key=lambda r: r["pts"], reverse=True)
    rookies[y] = clean[:5]

# 2) advanced: USG/TS/PER/BPM
adv = {}
for y in ANIOS:
    rows = parse_table(open(f"/tmp/adv_{y}.html").read(), ADV)
    for r in rows:
        nombre = norm(r.get("name_display", ""))
        if nombre:
            adv.setdefault(y, {})[nombre] = {c: f(r.get(c, "")) for c in ADV[1:]}

# 3) fusionar
dataset = {}
for y in ANIOS:
    for r in rookies[y]:
        n = r["player"]
        a = adv.get(y, {}).get(n, {})
        r["usg"] = a.get("usg_pct")
        r["ts"] = a.get("ts_pct")
        r["per"] = a.get("per")
        r["bpm"] = a.get("bpm")
        r["anio"] = y
        dataset[f"{n}|{y}"] = r

print("=== TOP 5 ROOKIES POR AÑO (con USG%) ===")
for y in ANIOS:
    for r in rookies[y]:
        print(f"  {y-1}-{str(y)[2:]}: {r['player']:22s} G={r['g']:.0f} USG={r['usg'] if r['usg'] is not None else 0:5.1f} "
              f"PTS={r['pts_per_g']:5.1f} TRB={r['trb_per_g']:4.1f} AST={r['ast_per_g']:4.1f} "
              f"STL={r['stl_per_g']:4.1f} BLK={r['blk_per_g']:4.1f} MPG={r['mp_per_g']:5.1f} TS={r['ts'] if r['ts'] is not None else 0:.3f}")

json.dump(dataset, open("/tmp/rookies_top5_full.json", "w"), ensure_ascii=False, indent=1)
print("\nguardado /tmp/rookies_top5_full.json")
