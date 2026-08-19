#!/usr/bin/env python3
"""Busca enlaces de subastas por carta (filtro ,fa) en la pagina de la Purple Shock.
11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

html = ms.get_html("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852")
if not html:
    print("sin_html")
    sys.exit()

print("=== hrefs con ,fa / Auction / fa ===")
for m in re.finditer(r'href="([^"]*)"', html):
    u = m.group(1)
    if ",fa" in u or "uction" in u.lower():
        print(u[:150])

print("\n=== contexto cerca de Sellers (buscar enlaces de subasta junto al muro) ===")
idx = html.find("<h5>Sellers</h5>")
ctx = html[max(0,idx-1500):idx+500]
for m in re.finditer(r'href="([^"]*)"', ctx):
    print(m.group(1)[:120])

print("\n=== onclick/JS con auction ===")
for m in re.finditer(r'onclick="[^"]*[Aa]uction[^"]*"', html):
    print(m.group(0)[:200])
