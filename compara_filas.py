#!/usr/bin/env python3
"""Compara filas del muro: subasta (mbevilacqua) vs buynow (junkwax_champ).
Busca la diferencia EXACTA en el HTML. 11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

html = ms.get_html("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852")
if not html:
    print("sin_html")
    sys.exit()

# Extraer TODAS las filas del muro (seccion Sellers)
idx = html.find("<h5>Sellers</h5>")
seccion = html[idx:idx+12000]
filas = re.findall(r"<tr>(.*?)</tr>", seccion, re.S)
print(f"Filas en muro: {len(filas)}")

for f in filas:
    vm = re.search(r'/Users/([A-Za-z0-9_.-]+)', f)
    if vm and vm.group(1) in ("mbevilacqua", "junkwax_champ"):
        print(f"===== FILA {vm.group(1)} =====")
        print(f.strip())
        print()
