#!/usr/bin/env python3
"""datos_mcgonigle.py — todos los items de Kevin McGonigle desde su feed, ordenados.
Muestra: set, carta, precio, copias. Marca candidatas (≤$5.05 y ≥10 copias)."""
import sys
sys.path.insert(0, "/root/comc-scripts")
import player_scan as ps

URL = "https://www.comc.com/SearchFeed.aspx?SportID=0&Search=Kevin+McGonigle&Sort%3dr"

hh = ps.get_feed(URL.replace("%3dr", "r"))
if not hh:
    print("sin_html")
    sys.exit(1)
items = ps.parse_feed(hh)
items = [it for it in items if it["precio"] is not None]
items.sort(key=lambda x: x["precio"])

print(f"Total items con precio: {len(items)}\n")
print("=== TODOS ORDENADOS POR PRECIO ===")
for it in items:
    cand = it["precio"] <= 5.05 and (it["qty"] or 0) >= 10
    print(f"  ${it['precio']:7.2f} | qty {str(it['qty']):4} | {it['titulo'][:75]} {'✅' if cand else ''}")

print("\n=== SOLO CANDIDATAS (≤$5.05, ≥10 copias) ===")
for it in items:
    if it["precio"] <= 5.05 and (it["qty"] or 0) >= 10:
        print(f"  ${it['precio']:7.2f} | qty {it['qty']:4} | {it['titulo'][:75]}")
