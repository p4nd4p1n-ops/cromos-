#!/usr/bin/env python3
"""probe_total_sales.py — comprueba si el HTML de COMC expone el total histórico de ventas.
Busca patrones tipo "sold", "sales", contadores, etc.
"""
import json, urllib.request, re, time

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038608"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

d = fs({"cmd": "request.get", "url": URL, "maxTimeout": 90000, "session": "ghost", "cookies": COOKIES})
html = d.get("solution", {}).get("response", "")
print("HTML len:", len(html))
print("=== patrones de ventas totales ===")
patrones = [
    (r"sold\s*[a-z]*\s*\(?\d+", "sold + num"),
    (r"\d+\s*sold", "num sold"),
    (r"total\s*sales?[^<]{0,40}", "total sales"),
    (r"Sales\s*History[^<]{0,80}", "Sales History"),
    (r"Historical[^<]{0,80}", "Historical"),
    (r"qty(?:Sold|sold)[^<]{0,40}", "qtySold"),
    (r"\d+\s+of\s+\d+\s+sold", "x of y sold"),
    (r"units? sold[^<]{0,40}", "units sold"),
    (r"sales?\s*:\s*\d+", "sales: num"),
    (r">\s*337\s*<", "literal 337"),
    (r"View\s+All\s+Sales[^<]{0,60}", "View All Sales"),
]
for pat, label in patrones:
    m = re.findall(pat, html, re.IGNORECASE)
    print(f"{label}: {m[:5] if m else 'NO'}")

print("=== contexto 'sold' ===")
for m in re.finditer(r".{80}sold.{80}", html, re.IGNORECASE):
    print(repr(m.group(0)[:200]))
    break
print("=== contexto 'sales history' ===")
for m in re.finditer(r".{60}[Ss]ales.{60}", html):
    print(repr(m.group(0)[:200]))
    break
