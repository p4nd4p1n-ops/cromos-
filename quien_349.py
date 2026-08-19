#!/usr/bin/env python3
"""quien_349.py — fetch fresco y busca QUÉ vendedor tiene la copia a $3.49 (allsellers + paralelos)."""
import json, urllib.request, re, html as h, time, random

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

ses = f"kobe{random.randint(1000,9999)}"
url = ("https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2541/"
       "Kon_Knueppel/31038641?_cb=" + str(int(time.time() * 1000)))

d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": ses, "cookies": COOKIES})
html = d.get("solution", {}).get("response", "")
open("/tmp/knueppel8.html", "w").write(html)
print("len:", len(html))

# 1) TODOS los contextos de 3.49
print("\n=== CONTEXTOS '3.49' ===")
for mm in list(re.finditer(r"3\.49", html))[:10]:
    s = max(0, mm.start() - 300)
    e = min(len(html), mm.start() + 300)
    print("...", re.sub(r"\s+", " ", html[s:e])[:600], "...\n")

# 2) tabla allsellers completa (por vendedor)
i = html.find("All Sellers")
j = html.rfind("<table", 0, i)
fin = html.find("</table>", j)
bloque = html[j:fin + 8]
filas = re.findall(r'<tr[^>]*>(.*?)</tr>', bloque, re.S)
print(f"\n=== ALLSELLERS ({len(filas)} filas) — primeras 12 ===")
n = 0
for f in filas:
    sm = re.search(r'class="seller">\s*<a[^>]*>([^<]+)</a>', f)
    pm = re.search(r'class="displayprice">.*?\$([\d,]+\.\d{2})', f, re.S)
    qm = re.search(r'class="qtyforsale">(.*?)</td>', f, re.S)
    if not pm:
        continue
    precio = float(pm.group(1).replace(",", ""))
    seller = h.unescape(sm.group(1)).strip() if sm else "(all sellers)"
    qraw = qm.group(1) if qm else ""
    qn = re.search(r'\((\d+)\)', qraw)
    qty = qn.group(1) if qn else "SUB"
    print(f"  ${precio:.2f} | {seller:24s} | {qty}")
    n += 1
    if n >= 12:
        break
