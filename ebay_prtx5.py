#!/usr/bin/env python3
"""ebay_prtx5.py — 1) estructura precio/vendedor en búsqueda guardada 2) página vendedor PRTX560 en eBay."""
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

# 1) estructura de precio/vendedor en la búsqueda guardada
resp = open("/tmp/ebay_search2.html").read()
i = resp.find("Kon Knueppel #254 (RC)")
# buscar alrededor el primer s-item completo: desde el <li hasta </li>
m = re.search(r'<li class="s-item[^>]*>.*?</li>', resp[i:i + 30000], re.S)
if m:
    b = m.group(0)
    print("=== PRIMER s-item (1500 chars) ===")
    print(b[:1500])
    # precio
    pm = re.search(r'class="[^"]*price[^"]*"[^>]*>(.*?)</', b, re.S)
    print("\nprecio raw:", pm.group(1) if pm else "NO")
    # seller
    sm = re.search(r'seller[^>]*>(.*?)</', b, re.S)
    print("seller raw:", sm.group(1)[:300] if sm else "NO")

# 2) página del vendedor PRTX560 en eBay US
url = "https://www.ebay.com/sch/i.html?_nkw=&_ssn=PRTX560"
try:
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "ghost"})
    r2 = d.get("solution", {}).get("response", "")
    open("/tmp/ebay_prtx560.html", "w").write(r2)
    print("\n=== EBAY VENDEDOR PRTX560 len:", len(r2))
    print("¿PRTX560 mencionado?:", r2.count("PRTX560"))
    m = re.search(r"<title>(.*?)</title>", r2, re.S)
    if m:
        print("TITLE:", m.group(1).strip()[:120])
    # items del vendedor
    titulos = re.findall(r'alt="([^"]{10,150})"', r2)
    print("títulos alt:", len(titulos))
    for t in titulos[:20]:
        print("  ", t[:80])
    # ¿tiene Knueppel?
    print("¿Knueppel?:", r2.count("Knueppel"))
except Exception as e:
    print("error vendedor:", str(e)[:120])
