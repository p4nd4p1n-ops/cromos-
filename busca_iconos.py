#!/usr/bin/env python3
"""Busca iconos/marcas de subasta en todo el HTML de la carta (11/08/2026).
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

html = ms.get_html("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190")
if not html:
    print("sin_html")
    sys.exit()

# 1) iconos (img) en toda la pagina con alt/src raros
print("=== IMGS con alt/src interesantes ===")
for m in re.finditer(r'<img[^>]+>', html):
    tag = m.group(0)
    if any(k in tag.lower() for k in ["auction", "gavel", "hammer", "bid", "clock", "timer"]):
        print(tag[:200])

# 2) clases con icon- (iconos de fuente)
print("\n=== clases icon- ===")
for c in sorted(set(re.findall(r'class="([^"]*icon-[^"]*)"', html))):
    print(c)

# 3) data-attributes en la seccion Sellers
idx = html.find("<h5>Sellers</h5>")
seccion = html[idx:idx+8000]
print("\n=== data-* en Sellers ===")
for m in re.finditer(r'data-[a-z-]+="[^"]*"', seccion):
    print(m.group(0))

# 4) la fila de ClassicSportscards con TODO su contexto (buscar si hay algun span oculto)
i = html.find("ClassicSportscards")
print("\n=== FILA CLASSIC COMPLETA (500 antes / 200 despues) ===")
print(html[i-500:i+200])
