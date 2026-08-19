#!/usr/bin/env python3
"""Inspecciona la estructura REAL del muro en el HTML de Harper guardado."""
import re

html = open("/tmp/harper-muro.html").read()

# 1) ¿Qué elementos tienen class con 'seller'?
print("=== Elementos con 'seller' en class ===")
for m in re.finditer(r'<(\w+)[^>]*class="([^"]*seller[^"]*)"', html):
    tag, cls = m.groups()
    s = max(0, m.start()-60)
    print(f"<{tag}> class=\"{cls}\"")
    print(f"   ctx: {html[s:m.end()+80].replace(chr(10),' ')[:180]}")
    print()

# 2) displayprice: contexto
print("=== displayprice (primeros 5) ===")
for i, m in enumerate(re.finditer(r'displayprice', html)):
    if i >= 5: break
    s = max(0, m.start()-120)
    print(f"[{i}] {html[s:m.end()+120].replace(chr(10),' ')[:240]}")
    print()

# 3) ¿El muro está en un bloque con 'allsellers'?
m = re.search(r'allsellers', html)
if m:
    s = max(0, m.start()-100)
    print("=== allsellers ctx ===")
    print(html[s:m.end()+300].replace(chr(10),' ')[:400])
