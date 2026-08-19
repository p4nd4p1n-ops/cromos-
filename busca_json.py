#!/usr/bin/env python3
"""Busca JSON/estado embebido en la pagina de carta con los sellers y su tipo.
11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

html = ms.get_html("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852")
if not html:
    print("sin_html")
    sys.exit()

# 1) variables JS con datos
print("=== var JS con 'Seller'/'Item' ===")
for m in re.finditer(r"var\s+([A-Za-z0-9_]+)\s*=\s*(\{.*?\});", html, re.S):
    var, val = m.group(1), m.group(2)
    if any(k in val.lower() for k in ["seller", "item", "auction", "bid"]):
        print(f"{var} = {val[:300]}")

# 2) arrays JS
print("\n=== arrays JS con datos ===")
for m in re.finditer(r"var\s+([A-Za-z0-9_]+)\s*=\s*(\[.*?\]);", html, re.S):
    var, val = m.group(1), m.group(2)
    if any(k in val.lower() for k in ["seller", "item", "auction", "bid"]):
        print(f"{var} = {val[:300]}")

# 3) __VIEWSTATE con datos? buscar mbevilacqua en viewstate no — buscar en todo el html otras apariciones
print("\n=== apariciones de mbevilacqua ===")
for m in re.finditer("mbevilacqua", html):
    print(m.start(), end=" ")
print()

# 4) buscar si hay un script con json de items
print("\n=== bloques JSON-like con itemid ===")
for m in re.finditer(r'\{[^{}]*"ItemId"[^{}]*\}', html):
    print(m.group(0)[:250])
