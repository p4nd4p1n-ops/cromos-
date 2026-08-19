#!/usr/bin/env python3
"""Verifica la fila de Adv_K_Collects en el HTML de Harper (¿condición rara a $1.49?)."""
import re

html = open("/tmp/harper-muro.html").read()

# Contexto de la fila del vendedor Adv_K_Collects
idx = html.find("Adv_K_Collects")
if idx == -1:
    print("Adv_K_Collects no encontrado")
else:
    s = max(0, idx-700)
    ctx = html[s:idx+400].replace("\n", " ")
    print("=== Contexto Adv_K_Collects ===")
    print(ctx[:900])
    print()

# Condiciones en esa zona
for m in re.finditer(r'Adv_K_Collects', html):
    s = max(0, m.start()-700)
    seg = html[s:m.end()+100]
    cond = re.findall(r'(Poor|Damaged|Fair|EX to NM|\bNM\b|Good|Mint|Rookie|Base)', seg)
    if cond:
        print("Condiciones/etiquetas cerca:", cond[:8])
        break

# ¿Cuántas filas displayprice hay en total y con qué precios?
print("\n=== Todos los precios displayprice en el HTML ===")
precios = re.findall(r'displayprice.*?class="price">\$([\d.]+)', html, re.S)
print(f"Total displayprice: {len(precios)}")
print("Precios:", sorted(set(float(p) for p in precios)))
