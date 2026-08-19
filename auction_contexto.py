#!/usr/bin/env python3
"""Compara las apariciones de 'Auction' en la pagina normal vs la ,fa.
11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

def ver(url, etiqueta):
    html = ms.get_html(url)
    if not html:
        print(f"{etiqueta}: sin_html")
        return
    print(f"===== {etiqueta} =====")
    for m in re.finditer(r"Auction", html):
        i = m.start()
        ctx = re.sub(r"\s+", " ", html[max(0,i-200):i+200])
        print(f"@{i}: {ctx[:380]}")
        print()

ver("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852", "PURPLE normal")
