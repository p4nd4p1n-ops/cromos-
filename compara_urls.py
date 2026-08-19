#!/usr/bin/env python3
"""compara_urls.py — compara la URL de Pin con la generada por el sistema para McGonigle,
y extrae los items de la que funcione."""
import sys, re, json
sys.path.insert(0, "/root/comc-scripts")
import player_scan as ps

URL_PIN = "https://www.comc.com/SearchFeed.aspx?SportID=0&Search=Kevin+McGonigle&Sort%3dr"
URL_SISTEMA = ps.feed_url("Kevin McGonigle")

print("URL de Pin:    ", URL_PIN)
print("URL del sistema:", URL_SISTEMA)
print("¿Coinciden? ", "SÍ" if URL_PIN == URL_SISTEMA else "NO")
print("Diferencias: Pin sin PageSize; sistema con PageSize=100\n")

# normalizar para comparar resultados: probar ambas
for nombre, url in [("PIN", URL_PIN.replace("%3dr", "r")), ("SISTEMA", URL_SISTEMA)]:
    hh = ps.get_feed(url)
    if not hh:
        print(f"{nombre}: sin_html")
        continue
    items = ps.parse_feed(hh)
    print(f"{nombre}: {len(items)} items | HTML {len(hh)}")
    ids = [it["id"] for it in items[:20]]
    print(f"  primeros IDs: {ids}")

# extraer items de la URL de Pin (normalizada Sort=r)
hh = ps.get_feed(URL_PIN.replace("%3dr", "r"))
items = ps.parse_feed(hh)
print(f"\n=== ITEMS McGonigle (URL Pin) — {len(items)} ===")
for it in items:
    cand = it["precio"] is not None and it["precio"] <= 5.05 and (it["qty"] or 0) >= 10
    print(f"  {it['titulo'][:65]:67} | ${it['precio']} | qty {it['qty']} | {'CANDIDATA' if cand else ''}")
