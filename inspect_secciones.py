#!/usr/bin/env python3
"""Lista TODAS las secciones/encabezados de la página de carta para ver dónde
se renderizan las subastas activas vs buy now. 11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

html = ms.get_html("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852")
if not html:
    print("sin_html")
    sys.exit()

print("=== ENCABEZADOS h1-h6 ===")
for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", html, re.S):
    texto = re.sub(r"<[^>]+>", "", m.group(2)).strip()
    texto = re.sub(r"\s+", " ", texto)
    print(f"h{m.group(1)}: {texto[:80]}")

print("\n=== IDs de secciones principales ===")
for m in re.finditer(r'id="([^"]+)"', html):
    i = m.group(1)
    if any(k in i.lower() for k in ["auction", "bid", "seller", "detail", "item", "price", "buy"]):
        print(i)

print("\n=== Botones (class= con buy/bid/offer) ===")
for m in re.finditer(r'class="([^"]*(?:buy|bid|offer|cart)[^"]*)"', html, re.I):
    print(m.group(1))
