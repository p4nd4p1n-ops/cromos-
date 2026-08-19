#!/usr/bin/env python3
"""Compara filas EXACTAS (repr) de subasta vs buynow en la misma pagina.
mbevilacqua (SUBATA) vs junkwax_champ (BUYNOW) en la Purple.
11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

html = ms.get_html("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852")
if not html:
    print("sin_html")
    sys.exit()

# extraer todas las filas de la tabla Sellers con su <tr> completo (crudo)
idx = html.find("<h5>Sellers</h5>")
seccion = html[idx:idx+12000]
filas = re.findall(r"<tr>.*?</tr>", seccion, re.S)
print(f"Total filas: {len(filas)}")

for f in filas:
    if "mbevilacqua" in f:
        print("===== FILA mbevilacqua (SUBATA) repr =====")
        print(repr(f))
        print()
    if "junkwax_champ" in f:
        print("===== FILA junkwax_champ (BUYNOW) repr =====")
        print(repr(f))
        print()
