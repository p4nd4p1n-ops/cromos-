#!/usr/bin/env python3
"""ebay_prtx.py — sigue los links eBay_Auction de PRTX560 y busca la carta en eBay."""
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

# 1) seguir un link eBay_Auction de PRTX560 (redirección -> eBay)
url = "https://www.comc.com/Promotions/eBay_Auction/PRTX560/eBay_Auction/3089957"
try:
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "ghost", "cookies": COOKIES})
    resp = d.get("solution", {}).get("response", "")
    print("=== LINK eBay_Auction 3089957 ===")
    print("len:", len(resp))
    # ¿es una página de eBay o de COMC?
    if "ebay.com" in resp:
        for mm in list(re.finditer(r'https?://[^"\'\s]*ebay[^"\'\s]*', resp))[:5]:
            print("  eBay URL:", mm.group(0)[:200])
    m = re.search(r"<title>(.*?)</title>", resp, re.S)
    if m:
        print("  TITLE:", m.group(1).strip()[:200])
    # buscar item id ebay
    for mm in list(re.finditer(r'itm/(\d+)', resp))[:5]:
        print("  itemId:", mm.group(1))
except Exception as e:
    print("error link:", str(e)[:120])

# 2) buscar en eBay la carta Knueppel de PRTX560
url2 = ("https://www.ebay.com/sch/i.html?_nkw=Kon+Knueppel+Topps+Chrome+2025-26"
        "+base&_sacat=0&LH_Auction=1")
try:
    d2 = fs({"cmd": "request.get", "url": url2, "maxTimeout": 90000, "session": "ghost"})
    resp2 = d2.get("solution", {}).get("response", "")
    open("/tmp/ebay_search.html", "w").write(resp2)
    print("\n=== BÚSQUEDA EBAY (subastas) len:", len(resp2))
    items = re.findall(r'<div class="s-item__title"><span[^>]*>(.*?)</span>', resp2, re.S)
    prices = re.findall(r'<span class="s-item__price">(.*?)</span>', resp2, re.S)
    sellers = re.findall(r'<span class="s-item__seller-info-text"[^>]*>(.*?)</span>', resp2, re.S)
    links = re.findall(r'href="(https://www\.ebay\.com/itm/\d+[^"]*)"', resp2)
    print("items:", len(items), "prices:", len(prices), "sellers:", len(sellers), "links:", len(links))
    for i in range(min(10, len(items))):
        t = re.sub(r"<[^>]+>", "", items[i]).strip()
        p = re.sub(r"<[^>]+>", "", prices[i]).strip() if i < len(prices) else ""
        s = re.sub(r"<[^>]+>", "", sellers[i]).strip() if i < len(sellers) else ""
        l = links[i] if i < len(links) else ""
        print(f"  [{i}] {t[:70]} | {p} | {s[:40]} | {l[:90]}")
except Exception as e:
    print("error busqueda:", str(e)[:120])
