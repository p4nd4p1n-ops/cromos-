#!/usr/bin/env python3
"""diag_auction.py — inspecciona el HTML guardado: contexto de 'auction' y fila PRTX560."""
import re

html = open("/tmp/knueppel.html").read()

# contexto de cada aparición de auction
for mm in re.finditer(r"auction", html, re.I):
    s = max(0, mm.start() - 250)
    e = min(len(html), mm.start() + 250)
    print("=== AUCTION ===")
    print(re.sub(r"\s+", " ", html[s:e]))
    print()

# bloque allsellers: fila PRTX560 completa + las 3 filas siguientes
blk = open("/tmp/allsellers.html").read()
i = blk.find("PRTX560")
print("=== CONTEXTO FILA PRTX560 (bloque allsellers) ===")
print(re.sub(r"\s+", " ", blk[max(0, i - 1500):i + 800]))
