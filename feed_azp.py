#!/usr/bin/env python3
"""Fetch del feed del vendedor azpleasantville (rebajas -11%) para ver precios reales de Bryant/Castle."""
import json, urllib.request, re, sys

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

URL = "https://www.comc.com/SearchFeed.aspx?SportID=8&Owner=azpleasantville&View=Details&Attributes=RC&PageSize=100&Sort%3dr"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

d = fs({"cmd": "request.get", "url": URL, "maxTimeout": 90000, "session": "ghost", "cookies": COOKIES})
html = d.get("solution", {}).get("response", "")
if not html or "SearchResults" not in html and "azpleasantville" not in html:
    print("SIN HTML válido, len:", len(html))
    print(html[:300])
    sys.exit(1)

print("HTML OK, len:", len(html))
# Buscar filas de resultados: patrón típico con título y precio
# El feed tiene items con: <div class="item">... título ... precio
rows = re.findall(r'title="([^"]+)"[^>]*>\s*</a>.*?\$([\d.]+)', html, re.S)
if not rows:
    # patrón alternativo: texto del producto + precio
    rows = re.findall(r'([A-Za-z0-9 .\-\'#]+(?:Bryant|Castle|Riley|Clayton|Flagg|Knueppel|Edgecombe)[A-Za-z0-9 .\-\'#]*)\s*\$([\d.]+)', html)

print("Filas encontradas:", len(rows))
for titulo, precio in rows[:30]:
    print(f"  ${precio:>7} | {titulo[:80]}")

# Guardar html para debug
open("/tmp/feed-azp.html", "w").write(html)
print("\nHTML guardado en /tmp/feed-azp.html")
