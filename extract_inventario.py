#!/usr/bin/env python3
"""extract_inventario.py — saca del feed-set los datos de las cartas del inventario:
precio mínimo, qty, URL, para rellenar la hoja Inventario."""
import json, re, sys

d = json.load(open("/root/comc-data/snapshots/feed-set-20260810-043015.json"))
targets = {"251.1": "Cooper Flagg", "271.1": "Will Riley", "268.1": "Walter Clayton Jr.",
           "264": "Carter Bryant", "228.1": "Stephon Castle", "253.1": "VJ Edgecombe",
           "252.1": "Dylan Harper"}

for x in d["items"]:
    t = x["titulo"]
    m = re.search(r"#([\d.]+)", t)
    if not m or m.group(1) not in targets:
        continue
    if "Refractor" in t or "SP" in t or "Image" in t:
        continue
    print(f"{m.group(1):6} | {t[:55]:57} | {x['precio']:7.2f} | qty {x['qty']:3} | {x['url']}")
