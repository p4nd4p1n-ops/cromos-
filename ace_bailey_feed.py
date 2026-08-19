#!/usr/bin/env python3
"""Feed completo de Ace Bailey (todas las variantes con precio+copias) — 11/08/2026."""
import json, urllib.request, re, time, sys, html as htmllib

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"
COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

URL = ("https://www.comc.com/SearchFeed.aspx?SportID=8&Search="
       "%22Ace%20Bailey%22&PageSize=100&Sort%3dr")

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

d = fs({"cmd": "request.get", "url": URL, "maxTimeout": 90000, "session": "ghost", "cookies": COOKIES})
html = d.get("solution", {}).get("response", "")
print(f"HTML len: {len(html)}")
open("/tmp/ace-bailey-feed.html", "w").write(html)

# Extraer items RSS: title + description (Sale Price) + guid/link
items = re.findall(r'<item>(.*?)</item>', html, re.S)
print(f"Items RSS: {len(items)}")
resultados = []
for it in items:
    t = re.search(r'<title>(.*?)</title>', it, re.S)
    desc = re.search(r'<description>(.*?)</description>', it, re.S)
    link = re.search(r'<link>(.*?)</link>', it, re.S)
    title = t.group(1).strip() if t else '?'
    dsc = desc.group(1) if desc else ''
    precio_m = re.search(r'Sale Price: \$([\d.]+)', dsc)
    precio = float(precio_m.group(1)) if precio_m else None
    copias_m = re.search(r'Qty: (\d+)', dsc)
    copias = int(copias_m.group(1)) if copias_m else None
    url = htmllib.unescape(link.group(1)) if link else ''
    if precio is not None:
        resultados.append((precio, copias, title, url))

resultados.sort(key=lambda x: x[0])
print(f"\n=== TODAS LAS VARIANTES DE ACE BAILEY ({len(resultados)}) ===")
for precio, copias, title, url in resultados:
    print(f"  ${precio:>8.2f} x{copias if copias is not None else '?'} | {title[:75]}")
