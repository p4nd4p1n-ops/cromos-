#!/usr/bin/env python3
"""Liquidez de Stephon Castle #228.1 (Topps Chrome Base 2025-26) — la carta de Pin."""
import json, urllib.request, re, datetime

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

url = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2281/Stephon_Castle/31038614"
d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "ghost", "cookies": COOKIES})
html = d.get("solution", {}).get("response", "")
m = re.search(r"<title>([^<]+)</title>", html)
print("title:", m.group(1).strip() if m else "?")
items = sorted(float(x.group(2).replace(",", "")) for x in re.finditer(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', html))
print("listados p1:", len(items), "| min:", f"${items[0]:.2f}" if items else "-")
cm = re.search(r"All Sellers.*?qtyforsale.*?\((\d+)\)", html, re.S)
print("copias totales:", cm.group(1) if cm else "?")
sales = re.findall(r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)
hoy = datetime.date.today()
v7 = 0
for f, p in sales:
    try:
        d2 = datetime.datetime.strptime(f, "%b %d, %Y").date()
        if (hoy - d2).days <= 7:
            v7 += 1
    except ValueError:
        pass
print("ventas página:", len(sales), "| ventas 7d:", v7, "| vel/día:", round(v7 / 7, 3))
if sales:
    precios = [float(p) for _, p in sales]
    print(f"rango: ${min(precios):.2f}-${max(precios):.2f} | media: ${sum(precios)/len(precios):.2f}")
for f, p in sales[:15]:
    print(f"  {f}: ${p}")
