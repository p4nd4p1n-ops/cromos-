#!/usr/bin/env python3
"""diag_prtx.py — confirma si la oferta de PRTX560 ($1.49) es subasta:
1) busca indicadores de subasta en la fila allsellers del HTML guardado
2) fetch de la página del vendedor para esa carta y análisis."""
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

# 1) buscar indicadores en el HTML ya guardado (allsellers)
blk = open("/tmp/allsellers.html").read()
i = blk.find("PRTX560")
seg = blk[max(0, i - 300):i + 700]
print("=== SEGMENTO ALLSELLERS PRTX560 ===")
print(re.sub(r"\s+", " ", seg))
for kw in ["auction", "bid", "time left", "ends", "countdown", "puja", "icon"]:
    if kw.lower() in seg.lower():
        print("  >>> contiene:", kw)

# 2) página del vendedor PRTX560 para la carta
url = ("https://www.comc.com/Users/PRTX560/Cards/Basketball/2025-26/"
       "Topps_Chrome_-_Base/2541/Kon_Knueppel/31038641")
d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "ghost", "cookies": COOKIES})
html = d.get("solution", {}).get("response", "")
open("/tmp/prtx560.html", "w").write(html)
print("\n=== PAGINA PRTX560 len:", len(html))

for kw in ["auction", "Auction", "bid", "Bid", "time left", "Time Left", "ends", "Ends",
           "BUY IT NOW", "buy it now", "make offer", "Make Offer", "qtyforsale",
           "quantity", "Quantity", "condition", "Condition", "damaged", "Damaged", "1.49"]:
    n = len(re.findall(re.escape(kw), html))
    print(f"  '{kw}': {n}")

# extract price / title area
m = re.search(r'<title>(.*?)</title>', html, re.S)
if m:
    print("\nTITLE:", m.group(1).strip()[:200])
for mm in list(re.finditer(r"1\.49", html))[:3]:
    s = max(0, mm.start() - 200)
    print("\nCTX 1.49:", re.sub(r"\s+", " ", html[s:mm.start() + 200]))
