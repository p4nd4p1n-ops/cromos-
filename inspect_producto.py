#!/usr/bin/env python3
"""Busca la marca real subasta vs buynow en el bloque de producto de la carta.
Inspecciona: productSpecPrice, pnlDetails, itemDetailsContainer, More Details.
11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

def analizar(url, etiqueta):
    html = ms.get_html(url)
    if not html:
        print(f"{etiqueta}: sin_html")
        return
    print(f"===== {etiqueta} =====")
    # bloque de especificacion del producto
    for blk_id in ["productSpecPrice", "pnlDetails", "itemDetailsContainer"]:
        m = re.search(r'id="[^"]*' + blk_id + r'"[^>]*>(.*?)</div>', html, re.S)
        if m:
            txt = re.sub(r"<[^>]+>", " ", m.group(1))
            txt = re.sub(r"\s+", " ", txt).strip()
            print(f"[{blk_id}]: {txt[:400]}")
    # More Details
    m = re.search(r"<h4>More Details</h4>(.*?)(?:<h4>|<h2>|$)", html, re.S)
    if m:
        txt = re.sub(r"<[^>]+>", " | ", m.group(1))
        txt = re.sub(r"\s+", " ", txt).strip()
        print(f"[More Details]: {txt[:600]}")
    # buscar texto con Auction/Bid cerca del precio del producto
    for kw in ["Current Bid", "Starting Bid", "Min Bid", "Auction ends", "Ends in", "Time Left", "Auction"]:
        for mm in re.finditer(kw, html):
            i = mm.start()
            if i < 150000 or i > 330000:
                continue
            ctx = re.sub(r"\s+", " ", html[max(0,i-200):i+200])
            print(f"[{kw} @ {i}]: {ctx[:300]}")
            break
    print()

analizar("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852", "PURPLE SHOCK (SUBASTA)")
