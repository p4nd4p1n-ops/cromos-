#!/usr/bin/env python3
"""ebay_parse2.py — parsea la búsqueda eBay guardada: títulos/precios/vendedores + busca Knueppel/PRTX."""
import re

resp = open("/tmp/ebay_search2.html").read()
print("len:", len(resp))
print("¿Knueppel en página?:", resp.count("Knueppel"), resp.count("knueppel"))

# estructura actual de eBay: <a ... href="https://www.ebay.com/itm/xxxx"> con title dentro
items = re.findall(r'<a[^>]*href="(https://www\.ebay\.com/itm/\d+)[^"]*"[^>]*>(.*?)</a>', resp, re.S)
print("items (regex href+inner):", len(items))

vistos = set()
n = 0
for href, inner in items:
    if href in vistos:
        continue
    vistos.add(href)
    # el título suele estar en <div class="s-item__title"><span>...
    t = re.sub(r"<[^>]+>", "", inner)
    t = re.sub(r"\s+", " ", t).strip()
    # buscar precio cerca
    i = resp.find(href)
    chunk = resp[max(0, i - 200):i + 800]
    pm = re.search(r'\$([\d,]+\.\d{2})', chunk)
    sm = re.search(r'class="s-item__seller-info-text"[^>]*>\s*<span[^>]*>([^<]+)</span>', chunk) or \
         re.search(r'([a-zA-Z0-9_\-\.]+)\(\d+\)', chunk)
    print(f"  {t[:80]} | ${pm.group(1) if pm else '?'} | seller={sm.group(1) if sm else '?'}")
    n += 1
    if n >= 20:
        break
