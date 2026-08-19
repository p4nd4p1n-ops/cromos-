#!/usr/bin/env python3
"""PlayerId real de Castle/Sarr + carta base Prizm + recent sales + velocidad."""
import json, urllib.request, re, urllib.parse
from collections import Counter

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

def get(url):
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "ghost", "cookies": COOKIES})
    return d.get("solution", {}).get("response", "")

for nombre in ["Stephon Castle", "Alex Sarr"]:
    print(f"########## {nombre} ##########")
    # 1) buscar playerId
    html = get("https://www.comc.com/Search.aspx?search=" + urllib.parse.quote(nombre))
    m = re.search(r'href="(/Players/Basketball/[^"]+/c\d+)"', html)
    if not m:
        print("  player no encontrado")
        continue
    player_path = m.group(1)
    print("  player:", player_path)
    # 2) página del jugador con set 2024-25 Prizm
    phtml = get("https://www.comc.com" + player_path + "/Cards/Basketball/2024-25/Panini_Prizm,sh,i100")
    # buscar carta base (Rookies / RC / Base sin paralela)
    links = re.findall(r'href="(/Cards/Basketball/2024-25/Panini_Prizm[^"]*)"', phtml)
    base = [l for l in sorted(set(links)) if l.count("/") == 6 and not any(x in l for x in ["Graded", "Variation", "SP_", "Refractor", "Prizm_-"])]
    print("  links base candidatos:", len(base))
    for l in base[:6]:
        print("    ", l)
    if not base:
        print("  (sin base clara; muestro algunos)")
        for l in sorted(set(links))[:6]:
            print("    ", l)
        continue
    # 3) tomar el primer candidato y extraer recent sales
    url_carta = "https://www.comc.com" + base[0]
    chtml = get(url_carta)
    m2 = re.search(r"<title>([^<]+)</title>", chtml)
    print("  carta:", m2.group(1).strip() if m2 else "?")
    sales = re.findall(r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", chtml)
    print("  ventas en pagina:", len(sales))
    for f, p in sales[:15]:
        print(f"    {f}: ${p}")
    print()
