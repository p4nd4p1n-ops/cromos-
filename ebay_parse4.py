#!/usr/bin/env python3
"""ebay_parse4.py — inspecciona la estructura del HTML de búsqueda eBay."""
import re

resp = open("/tmp/ebay_search2.html").read()

# buscar claves típicas
for kw in ["itemTitle", "itemPrice", "sellerName", "__NEXT_DATA__", "srp-results", "s-item",
           "Kon Knueppel", "viewitem", "vi-lnk"]:
    n = len(re.findall(re.escape(kw), resp))
    print(f"'{kw}': {n}")

# contexto de los primeros "Kon Knueppel" (título enlace)
for mm in list(re.finditer(r"Kon Knueppel", resp))[:3]:
    s = max(0, mm.start() - 200)
    e = min(len(resp), mm.start() + 300)
    print("\nCTX:", re.sub(r"\s+", " ", resp[s:e])[:500])

# ¿hay JSON embebido?
m = re.search(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', resp, re.S)
if m:
    print("\nJSON-LD encontrado, len:", len(m.group(1)))
    open("/tmp/ebay_ld.json", "w").write(m.group(1))
    for mm in list(re.finditer(r'"name":"([^"]{10,120})"', m.group(1)))[:10]:
        print("  name:", mm.group(1))
