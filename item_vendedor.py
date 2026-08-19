#!/usr/bin/env python3
"""Pide la pagina del ITEM del vendedor (subasta) vs (buynow) para ver el boton.
11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

urls = [
    ("ITEM mbevilacqua (SUBATA)", "https://www.comc.com/Users/mbevilacqua/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852"),
    ("ITEM dobiscollecting (BUYNOW)", "https://www.comc.com/Users/dobiscollecting/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190"),
]
for etiqueta, url in urls:
    html = ms.get_html(url)
    if not html:
        print(f"{etiqueta}: sin_html")
        continue
    print(f"===== {etiqueta} =====")
    print("len:", len(html))
    # buscar botones
    for kw in ["BuyItNow", "buyitnow", "Add to Cart", "Place Bid", "Bid Now", "Current Bid", "Make Offer", "Auction"]:
        n = len(re.findall(re.escape(kw), html))
        if n:
            print(f"  {kw}: {n}")
    # el boton de accion principal
    m = re.search(r'class="actionarea">(.*?)(?=<div|</div>)', html, re.S)
    if m:
        txt = re.sub(r"<[^>]+>", " ", m.group(1))
        txt = re.sub(r"\s+", " ", txt).strip()
        print("  actionarea:", txt[:200])
    # buscar texto de subasta cerca
    for kw in ["Bid", "bid", "Auction ends", "Time left", "Ends in"]:
        for mm in re.finditer(re.escape(kw), html):
            i = mm.start()
            if i < 200000 or i > 380000:
                continue
            ctx = re.sub(r"\s+", " ", html[max(0,i-150):i+150])
            print(f"  [{kw}@{i}]: {ctx[:250]}")
            break
    print()
