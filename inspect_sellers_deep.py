#!/usr/bin/env python3
"""Inspección PROFUNDA del muro: atributos de <tr>, hrefs, clases de precio.
11/08/2026 — encontrar la marca real subasta vs buynow.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

html = ms.get_html("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852")
if not html:
    print("sin_html")
    sys.exit()

idx = html.find("<h5>Sellers</h5>")
seccion = html[idx:idx+15000]

# 1) <tr> con sus atributos COMPLETOS
print("=== <tr> CON ATRIBUTOS ===")
for m in re.finditer(r"<tr([^>]*)>", seccion):
    print(repr(m.group(0)))

# 2) todos los hrefs de la seccion
print("\n=== HREFS de la seccion Sellers ===")
for m in re.finditer(r'href="([^"]+)"', seccion):
    print(m.group(1))

# 3) todas las clases de span de precio
print("\n=== SPANS de precio ===")
for m in re.finditer(r'<span class="([^"]*)">\$', seccion):
    print(m.group(1))
