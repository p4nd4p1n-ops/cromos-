#!/usr/bin/env python3
"""Filtro BUYNOW robusto: mapea itemid->BuyItNow y itemid->vendedor (11/08/2026).
Compra directa = item con boton BuyItNow. Subasta = item sin boton.
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
    # 1) itemids con BuyItNow: javascript:BuyItNow(123, '' )
    bin_ids = set(re.findall(r"javascript:BuyItNow\((\d+)", html))
    print(f"itemids con BuyItNow: {len(bin_ids)} -> {sorted(bin_ids)[:12]}")
    # 2) mapear itemid -> vendedor: Owner: <a href=/Users/X>...</a>...Item: N
    item_owner = {}
    for m in re.finditer(r'Owner:\s*<strong><a href="/Users/([A-Za-z0-9_.-]+)".*?Item:\s*(\d+)', html, re.S):
        item_owner[int(m.group(2))] = m.group(1)
    print(f"items mapeados a owner: {len(item_owner)}")
    # 3) sellers del muro con precio
    filas = []
    for r in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        if 'class="seller"' in r and 'displayprice' in r and 'soldout' not in r and 'allsellers' not in r:
            pm = re.search(r'class="price">\$([\d.]+)', r)
            vm = re.search(r'/Users/([A-Za-z0-9_.-]+)', r)
            if pm and vm:
                filas.append((float(pm.group(1)), vm.group(1)))
    # 4) para cada seller: es buynow si su nombre esta entre los owners con item en bin_ids
    print("Muro con filtro BUYNOW:")
    compra = []
    for p, v in sorted(filas):
        es_bin = False
        for iid, owner in item_owner.items():
            if owner == v and iid in bin_ids:
                es_bin = True
                break
        print(f"  ${p:.2f} | {v} | {'BUYNOW' if es_bin else 'SUBASTA/OTRO'}")
        if es_bin:
            compra.append(p)
    print(f"PRIMER ESCALON BUYNOW REAL: ${min(compra):.2f}" if compra else "SIN ESCALONES BUYNOW")
    print()

analizar("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190", "DANIELS OPTIC BASE #248")
analizar("https://www.comc.com/Cards/Football/2024/Panini_Donruss_-_Base/327/Rated_Rookie_-_Caleb_Williams/27013782", "WILLIAMS DONRUSS BASE #327")
