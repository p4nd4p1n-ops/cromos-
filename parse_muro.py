#!/usr/bin/env python3
"""Parser del muro de vendedores de una carta COMC (v2 — filtra vendidas).
Estructura REAL (11/08): <tr> con <td class="seller"> (link /Users/NOMBRE),
<td class="displayprice"> (<span class="price">$X.XX</span>) y <td class="qtyforsale">.
⚠️ Filtrar: class="price soldout" (vendidas) y class="allsellers" (resumen).
Uso: python3 parse_muro.py <archivo.html> [precio_buscar]"""
import re, sys

html = open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/harper-muro.html').read()

rows = re.findall(r'<tr>(.*?)</tr>', html, re.S)
escalones = []
for r in rows:
    if 'class="seller"' not in r or 'displayprice' not in r:
        continue
    if 'allsellers' in r:          # resumen "All Sellers", no es un vendedor
        continue
    if 'soldout' in r:             # carta VENDIDA, no está en el muro activo
        continue
    vend_m = re.search(r'/Users/([A-Za-z0-9_\-]+)', r)
    precio_m = re.search(r'displayprice.*?class="price">\$([\d.]+)', r, re.S)
    qty_m = re.search(r'qtyforsale.*?\((\d+)', r, re.S)
    if vend_m and precio_m:
        escalones.append((float(precio_m.group(1)), vend_m.group(1),
                          int(qty_m.group(1)) if qty_m else 1))

escalones.sort()
print(f"MURO ACTIVO ({len(escalones)} vendedores, vendidas excluidas):")
for p, v, q in escalones:
    print(f"  ${p:.2f} | {v} | x{q}")

if len(sys.argv) > 2:
    objetivo = float(sys.argv[2])
    mios = [e for e in escalones if abs(e[0]-objetivo) < 0.02]
    print(f"\nPrecio ${objetivo:.2f}: {'ENCONTRADO — ' + str(mios) if mios else 'NO en el muro activo'}")
