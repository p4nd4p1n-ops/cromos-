#!/usr/bin/env python3
"""ebay_parse5.py — extrae items de la búsqueda eBay con contexto alrededor de /itm/."""
import re

resp = open("/tmp/ebay_search2.html").read()

# links itm con contexto
links = [(m.start(), m.group(1)) for m in re.finditer(r'href="(https://www\.ebay\.com/itm/\d+)[^"]*"', resp)]
print("links itm:", len(links))

vistos = set()
n = 0
for pos, href in links:
    if href in vistos:
        continue
    vistos.add(href)
    chunk = resp[max(0, pos - 300):pos + 1200]
    # precio: buscar patrón $X.XX cerca
    pm = re.search(r'\$([\d,]+\.\d{2})', chunk)
    # título: buscar <h3 ...>...</h3> o role=heading
    tm = re.search(r'<h3[^>]*>(.*?)</h3>', chunk, re.S) or \
         re.search(r'<span[^>]*role="heading"[^>]*>(.*?)</span>', chunk, re.S)
    title = re.sub(r"<[^>]+>", "", tm.group(1)) if tm else "?"
    title = re.sub(r"\s+", " ", title).strip()[:80]
    # vendedor
    sm = re.search(r's-item__seller-info-text[^>]*>(.*?)</', chunk, re.S)
    seller = re.sub(r"<[^>]+>", "", sm.group(1)) if sm else "?"
    seller = re.sub(r"\s+", " ", seller).strip()[:40]
    # ¿subasta? (timer / bids)
    auc = "BID" if re.search(r'bids|bidCount|timeLeft|time-left|s-item__bidCount', chunk) else ""
    print(f"[{n}] {title} | {pm.group(1) if pm else '?'} | {seller} {auc}")
    n += 1
    if n >= 30:
        break
