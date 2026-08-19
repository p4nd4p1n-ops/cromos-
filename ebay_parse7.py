#!/usr/bin/env python3
"""ebay_parse7.py — parser para la nueva estructura eBay: alt=imagen, precio, vendedor, y busca COMC/PRTX."""
import re

resp = open("/tmp/ebay_search2.html").read()

print("PRTX560:", resp.count("PRTX560"), "| COMC en pagina:", resp.count("COMC"), resp.count("comc"))

# items por data-hscroll con itm id
items = re.findall(r'"itm"\s*:\s*"(\d+)"', resp)
print("item ids (data-hscroll):", len(items), items[:10])

# capturar bloques de item: desde <a ... itm/ID ... hasta </li>
bloques = re.split(r'(?=<a[^>]*href="https://www\.ebay\.com/itm/)', resp)
print("bloques a-itm:", len(bloques) - 1)

n = 0
vistos = set()
for b in bloques[1:]:
    hm = re.search(r'href="(https://www\.ebay\.com/itm/(\d+))[^"]*"', b)
    if not hm:
        continue
    iid = hm.group(2)
    if iid in vistos:
        continue
    vistos.add(iid)
    # título desde alt de imagen o role heading
    am = re.search(r'alt="([^"]{10,150})"', b)
    title = am.group(1) if am else "?"
    title = title.replace(" Image 1 of", "").strip()[:75]
    # precio
    pm = re.search(r'\$([\d,]+\.\d{2})', b)
    price = pm.group(1) if pm else "?"
    # vendedor: buscar span con nombre + feedback
    sm = re.search(r's-item__seller[^>]*>.*?([a-zA-Z0-9_\-\.]+)\s*\(', b, re.S) or \
         re.search(r'data-seller="([^"]+)"', b)
    seller = sm.group(1) if sm else "?"
    # pujas / tiempo
    auc = "BID" if re.search(r'bidCount|bids\b|time-left|timeLeft|s-item__bidCount', b) else ""
    print(f"[{n}] {title} | ${price} | {seller} {auc}")
    n += 1
    if n >= 25:
        break
