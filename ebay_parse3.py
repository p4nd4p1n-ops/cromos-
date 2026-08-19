#!/usr/bin/env python3
"""ebay_parse3.py — parser robusto de la búsqueda eBay guardada (bloques s-item)."""
import re

resp = open("/tmp/ebay_search2.html").read()

print("¿PRTX560 en página?:", resp.count("PRTX560"))
for mm in list(re.finditer(r"PRTX560", resp))[:3]:
    s = max(0, mm.start() - 150)
    print("  CTX:", re.sub(r"\s+", " ", resp[s:mm.start() + 150]))

# dividir por items
bloques = re.split(r'<li class="s-item', resp)
print("\nbloques s-item:", len(bloques) - 1)

n = 0
for b in bloques[1:]:
    href = re.search(r'href="(https://www\.ebay\.com/itm/\d+)[^"]*"', b)
    if not href:
        continue
    # título: <div class="s-item__title"><span ...>TEXT</span></div>
    tm = re.search(r'class="s-item__title"[^>]*>(?:<span[^>]*>)?(.*?)</(?:span|div)>', b, re.S)
    title = re.sub(r"<[^>]+>", "", tm.group(1)) if tm else "?"
    title = re.sub(r"\s+", " ", title).strip()
    # precio
    pm = re.search(r'class="s-item__price"[^>]*>(.*?)</span>', b, re.S)
    price = re.sub(r"<[^>]+>", "", pm.group(1)) if pm else "?"
    price = re.sub(r"\s+", " ", price).strip()
    # vendedor
    sm = re.search(r'class="s-item__seller-info-text"[^>]*>\s*<span[^>]*>([^<]+)</span>', b) or \
         re.search(r"\((\d+)\)", b)
    seller = sm.group(1).strip() if sm and sm.group(1) else "?"
    print(f"[{n}] {title[:75]} | {price} | {seller}")
    n += 1
    if n >= 25:
        break
