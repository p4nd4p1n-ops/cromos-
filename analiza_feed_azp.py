#!/usr/bin/env python3
"""Analiza /tmp/feed-azp.html (feed de azpleasantville) — ¿descuento general o selectivo?"""
import re, sys

html = open('/tmp/feed-azp.html').read()
print("HTML len:", len(html))

# Buscar estructura de items del SearchFeed. Patrones típicos:
# <div class="item"> ... <a ...>Title</a> ... <span class="price">$X.XX</span>
# o "price" con "sale" / descuento
# Primero, buscar menciones de descuento / sale
sales = re.findall(r'(?i)(sale|discount|% off|rebaja)', html)
print("Menciones sale/discount:", len(sales))

# Intentar extraer bloques de items
# Patrón A: href a tarjetas con título
items = re.findall(r'Cards/[^"]+"[^>]*title="([^"]+)"', html)
print("Items por title attr:", len(items))

# Patrón B: buscar precios con etiqueta
prices = re.findall(r'\$(\d+\.\d{2})', html)
print("Precios encontrados:", len(prices), "| primeros 20:", prices[:20])

# Buscar títulos con nombres de jugadores relevantes
for name in ['Bryant', 'Castle', 'Riley', 'Clayton', 'Edgecombe', 'Knueppel', 'Flagg', 'Harper', 'Bailey']:
    n = html.count(name)
    if n:
        print(f"  '{name}' aparece {n} veces")

# Extraer contexto alrededor de Bryant
idx = html.find('Bryant')
if idx > 0:
    print("\n--- Contexto Bryant ---")
    print(html[max(0,idx-500):idx+200].replace('\n',' ')[:700])

idx = html.find('Castle')
if idx > 0:
    print("\n--- Contexto Castle ---")
    print(html[max(0,idx-500):idx+200].replace('\n',' ')[:700])

# Buscar el patrón de precio de venta vs precio original (tachado)
striked = re.findall(r'(?i)(strike|was|original|reg\.?\s*\$|\$[\d.]+\s*\$)', html)
print("\nMarcas de precio original/tachado:", len(striked))
