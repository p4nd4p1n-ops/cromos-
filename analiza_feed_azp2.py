#!/usr/bin/env python3
"""Analiza feed RSS de azpleasantville: ¿descuento GENERAL o selectivo?
El feed es RSS: <item> con <title>, <description> (Sale Price), <guid>, <link>."""
import re, sys
from collections import Counter

html = open('/tmp/feed-azp.html').read()

# Extraer items RSS
items = re.findall(r'<item>(.*?)</item>', html, re.S)
print(f"Items RSS encontrados: {len(items)}\n")

con_sale = 0
sin_sale = 0
precios = []
bryant = []
castle = []
otros_2026 = []

for it in items:
    title = re.search(r'<title>(.*?)</title>', it, re.S)
    desc = re.search(r'<description>(.*?)</description>', it, re.S)
    guid = re.search(r'<guid>(.*?)</guid>', it, re.S)
    t = title.group(1).strip() if title else '?'
    d = desc.group(1) if desc else ''
    # precio: "Sale Price: $X.XX" o "Price: $X.XX"
    m = re.search(r'Sale Price: \$([\d.]+)', d)
    m2 = re.search(r'Price: \$([\d.]+)', d)
    precio = float(m.group(1)) if m else (float(m2.group(1)) if m2 else None)
    es_sale = bool(m)
    if es_sale:
        con_sale += 1
    else:
        sin_sale += 1
    if precio:
        precios.append(precio)
    if 'Bryant' in t:
        bryant.append((precio, es_sale, t))
    if 'Castle' in t:
        castle.append((precio, es_sale, t))
    if '2025-26 Topps Chrome' in t and ('2026' in t):
        otros_2026.append((precio, es_sale, t))

print(f"Con 'Sale Price': {con_sale} | Sin sale (precio normal): {sin_sale}")
if precios:
    print(f"Precios: min ${min(precios):.2f} · max ${max(precios):.2f} · media ${sum(precios)/len(precios):.2f}")
print(f"\nProporción con descuento: {con_sale/(con_sale+sin_sale)*100:.0f}% de {con_sale+sin_sale} items\n")

print("=== BRYANT en su tienda ===")
for p, s, t in bryant:
    print(f"  ${p:.2f} {'SALE' if s else 'normal'} | {t[:70]}")
print("\n=== CASTLE en su tienda ===")
for p, s, t in castle:
    print(f"  ${p:.2f} {'SALE' if s else 'normal'} | {t[:70]}")
print(f"\n=== Muestra de Topps Chrome 2025-26 ({len(otros_2026)} items) ===")
for p, s, t in otros_2026[:15]:
    print(f"  ${p:.2f} {'SALE' if s else 'normal'} | {t[:70]}")
