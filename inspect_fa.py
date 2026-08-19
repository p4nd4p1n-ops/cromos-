#!/usr/bin/env python3
"""Inspecciona la pagina de subastas activas /Cards,fa — como lista las subastas.
11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

html = ms.get_html("https://www.comc.com/Cards,fa")
if not html:
    print("sin_html")
    sys.exit()
print("len:", len(html))
t = re.search(r"<title>(.*?)</title>", html, re.S)
print("title:", t.group(1).strip()[:100] if t else "?")

# estructura de items
print("\n=== hrefs de cartas ===")
for m in re.finditer(r'href="(/Cards/[^"]+)"', html):
    print(m.group(1)[:130])

print("\n=== clases raras ===")
for c in sorted(set(re.findall(r'class="([^"]+)"', html))):
    if any(k in c.lower() for k in ["auction", "bid", "price", "item", "card"]):
        print(c)
