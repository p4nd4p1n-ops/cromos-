#!/usr/bin/env python3
"""Verifica el patrón BuyItNow vs subasta en muro COMC (11/08/2026).
Los vendedores con bloque 'Owner: X / Item: N' + BuyItNow = compra directa.
Los que NO tienen bloque (solo fila en Sellers) = subasta → filtrar.
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
    # 1) Sellers del muro (filas) con su precio
    filas = []
    for r in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        if 'class="seller"' in r and 'displayprice' in r and 'soldout' not in r:
            pm = re.search(r'class="price">\$([\d.]+)', r)
            vm = re.search(r'/Users/([A-Za-z0-9_.-]+)', r)
            if pm and vm:
                filas.append((float(pm.group(1)), vm.group(1)))
    # 2) Owners con bloque ItemDetails (compra directa con BuyItNow)
    owners = {}
    for m in re.finditer(r'Owner:\s*<strong><a href="/Users/([A-Za-z0-9_.-]+)".*?ItemDetails_UpdatePanel1">(.*?)(?=rptrViewDetails_ctl\d+_ItemDetails|$)', html, re.S):
        o, b = m.group(1), m.group(2)
        owners.setdefault(o, False)
        if re.search(r'BuyItNow|buyitnow', b):
            owners[o] = True
    print("Sellers del muro:")
    for p, v in sorted(filas):
        es_bin = owners.get(v, False)
        estado = "BUYNOW" if es_bin else "SUBASTA/OTRO"
        print(f"  ${p:.2f} | {v} | {estado}")
    # 3) Resumen: primer escalón buy-now real
    compra = [p for p, v in filas if owners.get(v, False)]
    print(f"Primer escalón BUYNOW real: ${min(compra):.2f}" if compra else "Sin escalones buynow")
    print()

analizar("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190", "DANIELS OPTIC BASE #248")
analizar("https://www.comc.com/Cards/Football/2024/Panini_Donruss_-_Base/327/Rated_Rookie_-_Caleb_Williams/27013782", "WILLIAMS DONRUSS BASE #327")
