#!/usr/bin/env python3
"""
P-001 DIAGNÓSTICO — Inspecciona la estructura de un HTML de COMC.
NO es un parser. Solo imprime clases, estructura y posibles precios.
Uso: python3 inspect_html.py <archivo.html>
"""
import sys, re
from bs4 import BeautifulSoup

html = open(sys.argv[1]).read()
soup = BeautifulSoup(html, 'html.parser')

print("=" * 60)
print("P-001 DIAGNÓSTICO DE ESTRUCTURA HTML")
print("=" * 60)

# 1. Buscar todas las clases CSS únicas
classes = {}
for tag in soup.find_all(True):
    if tag.get('class'):
        for c in tag['class']:
            classes[c] = classes.get(c, 0) + 1

print("\n--- CLASES CSS (ordenadas por frecuencia) ---")
for c, count in sorted(classes.items(), key=lambda x: -x[1]):
    print(f"  .{c} → {count} elementos")

# 2. Estructura de sellers
print("\n--- ESTRUCTURA SELLERS ---")
for tag in soup.find_all(['tr', 'td', 'div'], class_=re.compile(r'seller|price|qty|display', re.I)):
    cls = ' '.join(tag.get('class', []))
    text = tag.get_text(strip=True)[:80]
    print(f"  <{tag.name} class='{cls}'> → {text}")

# 3. Buscar precios
print("\n--- POSIBLES PRECIOS ($XX.XX) ---")
for tag in soup.find_all(text=re.compile(r'\$\d+\.?\d*')):
    parent = tag.parent.name if tag.parent else '?'
    parent_cls = ' '.join(tag.parent.get('class', [])) if tag.parent else ''
    txt = tag.strip()[:100]
    print(f"  [{parent}.{parent_cls}] {txt}")

# 4. Buscar "remote"/"remoto"
print("\n--- ¿HAY REMOTOS? ---")
remote_count = 0
for tag in soup.find_all(text=re.compile(r'remote|remoto|Shipping', re.I)):
    remote_count += 1
    print(f"  → {tag.strip()[:100]}")
if remote_count == 0:
    print("  ❌ No se encontraron indicadores de 'remote'.")
print(f"  Total: {remote_count} ocurrencias")

# 5. Buscar enlaces de vendedores
print("\n--- VENDEDORES (/Users/...) ---")
for a in soup.find_all('a', href=re.compile(r'/Users/')):
    print(f"  {a.get_text(strip=True)[:40]} → {a['href']}")

# 6. Resumen de tags
print("\n--- RESUMEN DE TAGS HTML ---")
tag_counts = {}
for tag in soup.find_all(True):
    tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1
for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
    print(f"  <{tag}> → {count}")

print("\n" + "=" * 60)
print("DIAGNÓSTICO COMPLETO. Ahora escribe el parser CON estos datos.")
print("=" * 60)
