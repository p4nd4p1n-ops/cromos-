#!/usr/bin/env python3
"""Feed por jugador — catálogo de TODAS sus variantes en TODOS los sets.
Para cada jugador top NBA 2026, una petición → 100 items con precio+copias.
11/08/2026. Espaciado 35-45s.
"""
import json, urllib.request, re, time, random, sys, html as htmllib

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"
COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

JUGADORES = [
    "Cooper Flagg", "Dylan Harper", "Ace Bailey", "Kon Knueppel", "Derik Queen",
    # 17/08: limpiada — quitados Edgecombe (vendida) y los de 0 liquidez (L-025)
]

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get_feed(jugador):
    url = ("https://www.comc.com/SearchFeed.aspx?SportID=8&Search="
           + urllib.parse.quote(f'"{jugador}"') + "&PageSize=100&Sort%3dr")
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "ghost", "cookies": COOKIES})
    html = d.get("solution", {}).get("response", "")
    items = re.findall(r'<item>(.*?)</item>', html, re.S)
    res = []
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
            res.append((precio, copias, title, url))
    res.sort(key=lambda x: x[0])
    return res

# Candidatas: precio ≤ 5.05 (10% bankroll), copias ≥ 10, base o inserts baratos
# (sin gradadas, sin autos, sin relics caros)
def es_candidata(titulo):
    t = titulo.lower()
    if any(x in t for x in ['psa', 'cga', 'cgc', 'bgs', 'sgc', 'auto', 'relic', 'patch',
                            'gold', 'black', 'cosmic dust', 'gold foil', 'numbered']):
        return False
    return True

todas = []
for i, jug in enumerate(JUGADORES):
    print(f"[{i+1}/{len(JUGADORES)}] {jug}...", flush=True)
    try:
        res = get_feed(jug)
        print(f"    {len(res)} items", flush=True)
        for p, q, t, u in res:
            if p <= 5.05 and q and q >= 10 and es_candidata(t):
                todas.append((jug, p, q, t, u))
    except Exception as e:
        print(f"    ERROR: {e}", flush=True)
    if i < len(JUGADORES) - 1:
        espera = random.randint(35, 45)
        print(f"    esperando {espera}s...", flush=True)
        time.sleep(espera)

print(f"\n=== CANDIDATAS BARATAS (≤$5.05, ≥10 copias, sin gradadas/autos/relics) — {len(todas)} ===")
todas.sort(key=lambda x: x[1])
for jug, p, q, t, u in todas:
    print(f"  ${p:.2f} x{q:<4} | {jug:<18} | {t[:60]}")
