#!/usr/bin/env python3
"""FILTRO BUYNOW DEFINITIVO: divide por class="ownerdetails" (un bloque por item).
Cada bloque tiene Owner + Item + botones. BuyItNow=True => compra directa.
Los sellers del muro SIN bloque ownerdetails => subasta activa. 11/08/2026.
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
    # bloques ownerdetails
    bloques = re.findall(r'class="ownerdetails">(.*?)(?=class="ownerdetails"|$)', html, re.S)
    info = {}
    for b in bloques:
        om = re.search(r'/Users/([A-Za-z0-9_.-]+)', b)
        im = re.search(r'Item:\s*(\d+)', b)
        pm = re.search(r'class="price">\$([\d.]+)', b)
        tiene_bin = bool(re.search(r'BuyItNow|buyitnow', b))
        tiene_bid = bool(re.search(r'(?i)(place\s*bid|bid\s*now|current\s*bid|btnBid|Start Bid|Minimum Bid|bid now)', b))
        if om:
            info[om.group(1)] = {"item": im.group(1) if im else "?", "buynow": tiene_bin, "bid": tiene_bid,
                                 "precio": pm.group(1) if pm else "?"}
    print(f"Bloques ownerdetails: {len(info)}")
    # sellers del muro
    filas = []
    for r in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        if 'class="seller"' in r and 'displayprice' in r and 'soldout' not in r and 'allsellers' not in r:
            pm = re.search(r'class="price">\$([\d.]+)', r)
            vm = re.search(r'/Users/([A-Za-z0-9_.-]+)', r)
            if pm and vm:
                filas.append((float(pm.group(1)), vm.group(1)))
    print("MURO clasificado:")
    compra = []
    for p, v in sorted(filas):
        d = info.get(v)
        if d and d["buynow"]:
            estado = f"BUYNOW item={d['item']}"
            compra.append(p)
        elif d and d["bid"]:
            estado = f"SUBAS(bid) item={d['item']}"
        elif d:
            estado = f"item={d['item']} bin={d['buynow']} bid={d['bid']}"
        else:
            estado = "SIN-BLOQUE -> SUBASTA/eBay"
        print(f"  ${p:.2f} | {v} | {estado}")
    print(f"PRIMER ESCALON BUYNOW REAL: ${min(compra):.2f}" if compra else "SIN BUYNOW")
    print()

analizar("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190", "DANIELS OPTIC BASE #248")
analizar("https://www.comc.com/Cards/Football/2024/Panini_Donruss_-_Base/327/Rated_Rookie_-_Caleb_Williams/27013782", "WILLIAMS DONRUSS #327")
