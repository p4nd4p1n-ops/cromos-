#!/usr/bin/env python3
"""diag_prtx2.py — contexto exacto de auction/Bid/Make Offer en la página de PRTX560."""
import re

html = open("/tmp/prtx560.html").read()

for kw in ["auction", "Auction", "Bid", "Make Offer", "qtyforsale"]:
    print(f"\n########## '{kw}' ({len(re.findall(re.escape(kw), html))} apariciones) ##########")
    for mm in list(re.finditer(re.escape(kw), html))[:8]:
        s = max(0, mm.start() - 180)
        e = min(len(html), mm.start() + 180)
        print("  ...", re.sub(r"\s+", " ", html[s:e]), "...")
        print()

# ¿cuántas filas de venta tiene la página del vendedor?
filas = re.findall(r'<td class="seller">.*?</tr>', html, re.S)
print("filas seller en pagina PRTX560:", len(filas))
# precios listados
precios = re.findall(r'<td class="displayprice"><span class="price">\$([\d,]+\.\d{2})</span>', html)
print("precios en pagina PRTX560:", precios[:20])
