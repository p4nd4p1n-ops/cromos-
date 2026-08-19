#!/usr/bin/env python3
"""Compara el muro de la pagina NORMAL vs la pagina ,fa (subastas activas).
Si ,fa muestra solo subastas, la diferencia nos da el filtro. 11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

def muro(url, etiqueta):
    html = ms.get_html(url)
    if not html:
        print(f"{etiqueta}: sin_html")
        return []
    print(f"===== {etiqueta} =====")
    idx = html.find("<h5>Sellers</h5>")
    if idx == -1:
        print("  NO hay seccion Sellers")
        return []
    seccion = html[idx:idx+8000]
    filas = []
    for r in re.findall(r"<tr>(.*?)</tr>", seccion, re.S):
        if 'class="seller"' in r and 'displayprice' in r and 'soldout' not in r and 'allsellers' not in r:
            pm = re.search(r'class="price">\$([\d.]+)', r)
            vm = re.search(r'/Users/([A-Za-z0-9_.-]+)', r)
            if pm and vm:
                filas.append((float(pm.group(1)), vm.group(1)))
    for p, v in sorted(filas)[:20]:
        print(f"  ${p:.2f} | {v}")
    return filas

base = "https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190"
n = muro(base, "NORMAL")
f = muro(base + ",fa", "CON ,fa")

if n and f:
    sn = set(v for _, v in n)
    sf = set(v for _, v in f)
    print("\nSellers SOLO en normal (no subasta?):", sn - sf)
    print("Sellers SOLO en ,fa (subastas?):", sf - sn)
