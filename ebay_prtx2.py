#!/usr/bin/env python3
"""ebay_prtx2.py — extrae todos los links eBay_Auction del perfil de PRTX560 y sigue los
que puedan ser Knueppel (título). También revisa la fila PRTX560 en allsellers de Knueppel."""
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

# 1) todos los links eBay_Auction del perfil
perfil = open("/tmp/prtx560_profile.html").read()
links = sorted(set(re.findall(r'href="(/Promotions/eBay_Auction/PRTX560/eBay_Auction/\d+)"', perfil)))
print("links eBay_Auction:", len(links))
for l in links:
    print("  ", l)

# 2) ¿la fila PRTX560 en allsellers de Knueppel tiene link de subasta/eBay?
blk = open("/tmp/allsellers.html").read()
i = blk.find("PRTX560")
seg = blk[max(0, i - 200):i + 600]
ebay_links = re.findall(r'href="([^"]*ebay[^"]*)"', seg, re.I)
auction_flags = re.findall(r'[Aa]uction|subast', seg)
print("\nlinks ebay en fila PRTX560 (allsellers):", ebay_links)
print("flags auction en fila:", auction_flags)

# 3) seguir links eBay_Auction hasta encontrar Knueppel (máx 6)
encontrado = None
for l in links[:6]:
    try:
        d = fs({"cmd": "request.get", "url": "https://www.comc.com" + l, "maxTimeout": 90000,
                "session": "ghost", "cookies": COOKIES})
        resp = d.get("solution", {}).get("response", "")
        m = re.search(r"<title>(.*?)</title>", resp, re.S)
        title = m.group(1).strip() if m else "?"
        itm = re.search(r"ebay\.com/itm/(\d+)", resp)
        print(f"\n  {l} -> {title[:90]}  itemId={itm.group(1) if itm else '?'}")
        if "Knueppel" in title:
            encontrado = l
            open("/tmp/ebay_knueppel.html", "w").write(resp)
            print("  >>> ¡ES KNUEPPEL! guardado /tmp/ebay_knueppel.html")
            break
    except Exception as e:
        print(f"  {l}: error {str(e)[:80]}")

print("\nRESULTADO:", encontrado or "no encontrado entre los 6 primeros")
