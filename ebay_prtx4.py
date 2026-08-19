#!/usr/bin/env python3
"""ebay_prtx4.py — busca en la página de PRTX560 de Knueppel (prtx560.html) si hay link eBay,
y busca la carta en eBay US por subasta."""
import json, urllib.request, re

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

# 1) página PRTX560 de Knueppel: ¿link eBay/subasta para el item?
html = open("/tmp/prtx560.html").read()
print("=== PRTX560 / Knueppel: indicadores ===")
for kw in ["ebay", "Ebay", "eBay", "auction", "Auction", "Promotions", "31038641"]:
    n = len(re.findall(re.escape(kw), html))
    print(f"  '{kw}': {n}")
# contexto de 31038641 (el item id de Knueppel en COMC)
for mm in list(re.finditer(r"31038641", html))[:4]:
    s = max(0, mm.start() - 200)
    e = min(len(html), mm.start() + 200)
    print("\n  CTX:", re.sub(r"\s+", " ", html[s:e]))
# links ebay
for mm in list(re.finditer(r'href="([^"]*ebay[^"]*)"', html, re.I))[:8]:
    print("  ebay link:", mm.group(1)[:150])

# 2) buscar en eBay US subastas de Knueppel Topps Chrome 2025-26
for url in [
    "https://www.ebay.com/sch/i.html?_nkw=Kon+Knueppel+Topps+Chrome+2025-26+base&_sacat=0&LH_Auction=1&_sop=1",
    "https://www.ebay.com/sch/i.html?_nkw=knueppel+topps+chrome+254&LH_Auction=1",
]:
    try:
        d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "ghost"})
        resp = d.get("solution", {}).get("response", "")
        print(f"\n=== EBAY SEARCH len={len(resp)} ===")
        open("/tmp/ebay_search2.html", "w").write(resp)
        items = re.findall(r'<div class="s-item__title"><span[^>]*>(.*?)</span>', resp, re.S)
        prices = re.findall(r'<span class="s-item__price">(.*?)</span>', resp, re.S)
        links = re.findall(r'href="(https://www\.ebay\.com/itm/\d+[^"]*)"', resp)
        sellers = re.findall(r'<span class="s-item__seller-info-text"[^>]*>(.*?)</span>', resp, re.S)
        print("items:", len(items), "prices:", len(prices), "links:", len(links), "sellers:", len(sellers))
        for i in range(min(10, len(items))):
            t = re.sub(r"<[^>]+>", "", items[i]).strip()
            p = re.sub(r"<[^>]+>", "", prices[i]).strip() if i < len(prices) else ""
            s = re.sub(r"<[^>]+>", "", sellers[i]).strip() if i < len(sellers) else ""
            print(f"  [{i}] {t[:60]} | {p} | {s[:35]}")
        break
    except Exception as e:
        print("error:", str(e)[:100])
