#!/usr/bin/env python3
"""urls_nfl2.py — saca URLs exactas de Williams Bowman Univ #50.1 y Daniels Prizm #347.
Método verificado 11/08: SearchFeed con SportID=2 y Search= solo (sin corchetes). 12/08."""
import json, urllib.request, urllib.parse, re, html as htmllib, time, random

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"
COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get_feed(jugador):
    url = ("https://www.comc.com/SearchFeed.aspx?SportID=2&PageSize=100&Search="
           + urllib.parse.quote(f'"{jugador}"') + "&Sort%3dr")
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "ghost", "cookies": COOKIES})
    html = d.get("solution", {}).get("response", "")
    items = re.findall(r'<item>(.*?)</item>', html, re.S)
    res = []
    for it in items:
        t = re.search(r'<title>(.*?)</title>', it, re.S)
        link = re.search(r'<link>(.*?)</link>', it, re.S)
        if t and link:
            res.append((t.group(1).strip(), htmllib.unescape(link.group(1))))
    return res

# Buscar las 2 cartas exactas
objetivo = [
    ("2022 Bowman University Chrome", "50.1", "Caleb Williams"),
    ("2024 Panini Prizm", "#347", "Jayden Daniels"),
]
for jug in ["Caleb Williams", "Jayden Daniels"]:
    try:
        feed = get_feed(jug)
    except Exception as e:
        print(f"{jug} error: {e}", flush=True)
        continue
    for titulo, url in feed:
        for set_, num, _ in objetivo:
            if set_ in titulo and num in titulo:
                print(f"FOUND | {titulo} | {url}", flush=True)
    time.sleep(random.uniform(25, 35))
print("FIN", flush=True)
