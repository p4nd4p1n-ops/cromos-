#!/usr/bin/env python3
"""Busca la marca REAL de subasta: contexto crudo de ClassicSportscards (subasta)
y dobiscollecting (buynow) en la misma pagina. 11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

html = ms.get_html("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190")
if not html:
    print("sin_html")
    sys.exit()

for nombre in ["ClassicSportscards", "dobiscollecting"]:
    print(f"########## {nombre} ##########")
    for m in re.finditer(nombre, html):
        i = m.start()
        print(f"--- pos {i} ---")
        # contexto crudo SIN normalizar, 800 antes / 300 despues
        print(html[max(0,i-800):i+300])
        print()
