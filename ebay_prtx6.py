#!/usr/bin/env python3
"""ebay_prtx6.py — items del vendedor PRTX560 en eBay."""
import re

resp = open("/tmp/ebay_prtx560.html").read()

# títulos: buscar h3/span/div con contenido de título
for pat in [r'<h3[^>]*>(.*?)</h3>', r'<span[^>]*role="heading"[^>]*>(.*?)</span>',
            r'class="s-item__title"[^>]*>(.*?)</div>', r'<div class="s-item__title"[^>]*><span[^>]*>(.*?)</span>']:
    ms = re.findall(pat, resp, re.S)
    print(f"patron {pat[:40]}: {len(ms)}")
    if ms:
        for m in ms[:15]:
            t = re.sub(r"<[^>]+>", "", m).strip()
            print("  ", t[:90])
        break

# links itm
links = re.findall(r'href="(https://www\.ebay\.com/itm/\d+)[^"]*"', resp)
print("\nlinks itm:", len(links), links[:10])

# precios
precios = re.findall(r'\$([\d,]+\.\d{2})', resp)
print("precios:", precios[:20])

# contexto: buscar bloques con img alt y precio juntos
bloques = re.split(r'(?=<div class="s-item)', resp)
print("bloques s-item:", len(bloques) - 1)
n = 0
for b in bloques[1:]:
    am = re.search(r'alt="([^"]{10,150})"', b)
    pm = re.search(r'\$([\d,]+\.\d{2})', b)
    lm = re.search(r'href="(https://www\.ebay\.com/itm/\d+)[^"]*"', b)
    print(f"[{n}] {am.group(1)[:70] if am else '?'} | ${pm.group(1) if pm else '?'} | {lm.group(1)[:60] if lm else '?'}")
    n += 1
    if n >= 15:
        break
