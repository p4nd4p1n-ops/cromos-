#!/usr/bin/env python3
"""Prueba la URL de carta con filtro ,fa (subastas activas) — 11/08/2026.
Si /Cards/...,fa lista las subastas activas del producto, ese es el filtro real.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

urls = [
    ("PURPLE ,fa", "https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852,fa"),
    ("BASE ,fa", "https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190,fa"),
]
for etiqueta, url in urls:
    html = ms.get_html(url)
    if not html:
        print(f"{etiqueta}: sin_html")
        continue
    print(f"===== {etiqueta} =====")
    print("len:", len(html))
    t = re.search(r"<title>(.*?)</title>", html, re.S)
    print("title:", t.group(1).strip()[:100] if t else "?")
    # sellers en esta pagina
    filas = re.findall(r'<td class="seller">\s*<a[^>]*href="/Users/([A-Za-z0-9_.-]+)"[^>]*>', html)
    print("sellers:", filas[:10])
    # buscar Auction en el html
    print("Auction:", len(re.findall(r"Auction", html)))
    print()
