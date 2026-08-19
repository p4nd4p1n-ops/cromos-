#!/usr/bin/env python3
"""muro_knueppel4.py — parsea TODAS las filas del allsellers del HTML fresco (knueppel3.html)."""
import re, html as h

html = open("/tmp/knueppel3.html").read()

# extraer el bloque de la tabla allsellers
m = re.search(r'<table[^>]*class="[^"]*allsellers[^"]*".*?</table>', html, re.S) or \
    re.search(r'class="allsellers".*?</table>', html, re.S)
if not m:
    # buscar cualquier bloque con filas seller
    print("no tabla allsellers; busco filas sueltas")
    bloque = html
else:
    bloque = m.group(0)
    print("tabla allsellers len:", len(bloque))

# filas <tr> dentro del bloque
filas = re.findall(r'<tr[^>]*>(.*?)</tr>', bloque, re.S)
print("filas:", len(filas))

out = []
for f in filas:
    sm = re.search(r'class="seller">\s*<a[^>]*>([^<]+)</a>', f)
    pm = re.search(r'class="displayprice">.*?\$([\d,]+\.\d{2})', f, re.S)
    qm = re.search(r'class="qtyforsale">(.*?)</td>', f, re.S)
    if not pm:
        continue
    precio = float(pm.group(1).replace(",", ""))
    seller = h.unescape(sm.group(1)).strip() if sm else "(all sellers)"
    qraw = qm.group(1) if qm else ""
    qty = None
    qn = re.search(r'\((\d+)\)', qraw)
    if qn:
        qty = int(qn.group(1))
    sub = "SUB" if qty is None and "auction" in qraw.lower() or (qty is None and qraw.strip() == "") else ""
    out.append((precio, seller, qty, qraw.strip()[:40]))
    print(f"  ${precio:.2f} | {seller:24s} | qty={qty if qty is not None else '—'} | {qraw.strip()[:30]}")

print("\nTOTAL filas precio:", len(out))
print("primeros 8:", [(p, s, q) for p, s, q, _ in out[:8]])
