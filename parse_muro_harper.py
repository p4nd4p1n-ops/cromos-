#!/usr/bin/env python3
"""Parser correcto del muro de Harper desde /tmp/harper-muro.html (ya guardado).
Estructura COMC: filas con class='seller' / displayprice / listprice."""
import re, sys

html = open('/tmp/harper-muro.html').read()

# 1) Buscar el bloque del muro de vendedores (allsellers o la tabla)
# Las filas típicas: <tr class="seller"> ... <span class="displayprice">$X.XX</span> ... vendedor
filas = re.findall(r'<tr[^>]*class="[^"]*seller[^"]*"[^>]*>(.*?)</tr>', html, re.S)
print(f"Filas seller encontradas: {len(filas)}")

escalones = []
for f in filas:
    precio_m = re.search(r'displayprice[^>]*>\s*\$?([\d.]+)', f)
    precio_m2 = re.search(r'listprice[^>]*>\s*\$?([\d.]+)', f)
    precio = precio_m.group(1) if precio_m else (precio_m2.group(1) if precio_m2 else None)
    # vendedor: link a /Users/
    vend_m = re.search(r'/Users/([A-Za-z0-9_\-]+)', f)
    vendedor = vend_m.group(1) if vend_m else '?'
    # copias: "x2" o qty
    qty_m = re.search(r'(\d+)\s*(?:cop|Cop|available|Available)', f)
    qty = qty_m.group(1) if qty_m else '1'
    # remoto?
    remoto = 'remoto' in f.lower() or 'remote' in f.lower()
    if precio:
        escalones.append((float(precio), vendedor, qty, remoto))

escalones.sort()
print(f"\nMURO DE HARPER ({len(escalones)} vendedores):")
for p, v, q, r in escalones[:10]:
    tag = " [REMOTO]" if r else ""
    print(f"  ${p:.2f} | {v} | x{q}{tag}")

# 2) Buscar ventas 7d / stats
for pat in [r'(\d+)\s+sold', r'(\d+)\s+ventas', r'Sold in last 7 days[^<]*<[^>]*>(\d+)']:
    m = re.search(pat, html, re.I)
    if m:
        print(f"\nVentas: {m.group(1)}")

# 3) Nuestra copia a 13.49 — buscar en el muro
mios = [e for e in escalones if abs(e[0]-13.49) < 0.02]
print(f"\nNuestra copia $13.49: {'ENCONTRADA en el muro' if mios else 'NO está en las filas seller'}")
print(f"Ocurrencias de '13.49' en HTML: {html.count('13.49')}")
