#!/usr/bin/env python3
"""prep_top50.py — precargar en scan-top50 los 3 ya escaneados hoy (Flagg, Knueppel, Castle)
desde scan-2026-08-07.json, para que comc-scan50 solo escanee los 42 restantes.
"""
import json, os, datetime

DATA_DIR = "/root/comc-data"
hoy = datetime.date.today().isoformat()
out_file = f"{DATA_DIR}/scan-top50-{hoy}.json"

prev = {}
try:
    for r in json.load(open(f"{DATA_DIR}/scan-2026-08-07.json")):
        prev[r["nombre"]] = r
except Exception as e:
    print("sin scan previo:", e)

paths = json.load(open(f"{DATA_DIR}/top50-paths.json"))
rows = {}
if os.path.exists(out_file):
    for r in json.load(open(out_file)):
        rows[r["nombre"]] = r

YA = ["Cooper Flagg", "Kon Knueppel", "Stephon Castle"]
for j in YA:
    if j in prev and j in paths and j not in rows:
        r = dict(prev[j])
        r["num"] = paths[j]["num"]
        r["es_sp"] = paths[j].get("es_sp", False)
        rows[j] = r
        print(f"precargado: {j} (ventas_7d={r.get('ventas_7d')})")

json.dump(list(rows.values()), open(out_file, "w"), ensure_ascii=False, indent=1)
print(f"total precargados: {len(rows)} — pendientes de escanear: {len(paths) - len(rows)}")
