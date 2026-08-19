#!/usr/bin/env python3
"""Filtro BUYNOW v3: extrae bloque ItemDetails completo por ctlXX y cruza con muro.
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
    # Dividir por bloques ItemDetails (cada ctlXX tiene Owner, Item, precio, botones)
    partes = re.split(r'rptrViewDetails_ctl\d+_ItemDetails', html)
    info = {}  # owner -> (itemid, precio, buynow, bid)
    for p in partes[1:]:
        # solo bloques que contienen Owner:
        om = re.search(r'Owner:\s*<strong><a href="/Users/([A-Za-z0-9_.-]+)"', p)
        if not om:
            continue
        owner = om.group(1)
        im = re.search(r'Item:\s*(\d+)', p)
        pm = re.search(r'class="price">\$([\d.]+)', p)
        tiene_bin = bool(re.search(r'BuyItNow|buyitnow|class="buyitnow"', p))
        tiene_bid = bool(re.search(r'(?i)(place\s*bid|bid\s*now|current\s*bid|class="bid|btnBid|Start Bid|Minimum Bid|Current Bid|Bid Now)', p))
        info[owner] = {
            "item": im.group(1) if im else "?",
            "precio": float(pm.group(1)) if pm else None,
            "buynow": tiene_bin,
            "bid": tiene_bid,
        }
    print(f"Owners con bloque ItemDetails: {len(info)}")
    # Sellers del muro
    filas = []
    for r in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        if 'class="seller"' in r and 'displayprice' in r and 'soldout' not in r and 'allsellers' not in r:
            pm = re.search(r'class="price">\$([\d.]+)', r)
            vm = re.search(r'/Users/([A-Za-z0-9_.-]+)', r)
            if pm and vm:
                filas.append((float(pm.group(1)), vm.group(1)))
    print("MURO con clasificacion:")
    compra = []
    for p, v in sorted(filas):
        d = info.get(v)
        if d and d["buynow"]:
            print(f"  ${p:.2f} | {v} | BUYNOW item={d['item']}")
            compra.append(p)
        elif d and d["bid"]:
            print(f"  ${p:.2f} | {v} | SUBAS(bid) item={d['item']}")
        elif d:
            print(f"  ${p:.2f} | {v} | item={d['item']} bin={d['buynow']} bid={d['bid']}")
        else:
            print(f"  ${p:.2f} | {v} | SIN-BLOQUE (subasta/eBay)")
    print(f"PRIMER ESCALON BUYNOW: ${min(compra):.2f}" if compra else "SIN BUYNOW")
    print()

analizar("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190", "DANIELS OPTIC BASE #248")
analizar("https://www.comc.com/Cards/Football/2024/Panini_Donruss_-_Base/327/Rated_Rookie_-_Caleb_Williams/27013782", "WILLIAMS DONRUSS BASE #327")
