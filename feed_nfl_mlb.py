#!/usr/bin/env python3
"""feed_nfl_mlb.py — catálogo de cartas NFL (SportID=2) y MLB (SportID=1) con precio/copias.
17/08/2026. Mismo motor que feed_jugadores.py. Espaciado 35-45s.
Lista aprobada por Pin (10:21 UTC).
"""
import json, urllib.request, re, time, random, sys, html as htmllib, urllib.parse

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"
COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

# (jugador, SportID): NFL=2, MLB=1
JUGADORES = [
    ("Caleb Williams", 2), ("Jayden Daniels", 2), ("Bo Nix", 2), ("Drake Maye", 2),
    ("JJ McCarthy", 2), ("Michael Penix", 2), ("Marvin Harrison Jr.", 2),
    ("Malik Nabers", 2), ("Brock Bowers", 2), ("Travis Hunter", 2),
    ("Paul Skenes", 1), ("Jackson Merrill", 1), ("Wyatt Langford", 1),
    ("Jackson Holliday", 1), ("James Wood", 1), ("Dylan Crews", 1),
]

MAX_PRECIO = 6.0   # 10% bankroll aprox (saldo 49.01 → límite ~4.90, margen a 6)
MIN_COPIAS = 10

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get_feed(jugador, sportid):
    url = ("https://www.comc.com/SearchFeed.aspx?SportID=" + str(sportid) + "&Search="
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

def es_candidata(titulo):
    t = titulo.lower()
    if any(x in t for x in ['psa', 'cga', 'cgc', 'bgs', 'sgc', 'auto', 'relic', 'patch',
                            'gold', 'black', 'cosmic dust', 'gold foil', 'numbered',
                            ' /25', ' /50', ' /99', ' /100', ' /150', ' /199', ' /299']):
        return False
    return True

todas = []
for i, (jug, sp) in enumerate(JUGADORES):
    dep = {2: "NFL", 1: "MLB"}.get(sp, "?")
    print(f"[{i+1}/{len(JUGADORES)}] [{dep}] {jug}...", flush=True)
    try:
        res = get_feed(jug, sp)
        print(f"    {len(res)} items", flush=True)
        for p, q, t, u in res:
            if p <= MAX_PRECIO and q and q >= MIN_COPIAS and es_candidata(t):
                todas.append((jug, dep, p, q, t, u))
    except Exception as e:
        print(f"    ERROR: {e}", flush=True)
    if i < len(JUGADORES) - 1:
        espera = random.randint(35, 45)
        print(f"    esperando {espera}s...", flush=True)
        time.sleep(espera)

print(f"\n=== CANDIDATAS (≤${MAX_PRECIO}, ≥{MIN_COPIAS} copias, sin gradadas/autos/numeradas) — {len(todas)} ===")
todas.sort(key=lambda x: x[2])
for jug, dep, p, q, t, u in todas:
    print(f"  ${p:.2f} x{q:<4} | {dep} {jug:<18} | {t[:60]}")

# guardar snapshot
import datetime
out = f"/root/comc-data/snapshots/feed-nfl-mlb-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
json.dump([{"jugador": j, "deporte": d, "precio": p, "copias": q, "titulo": t, "url": u}
           for j, d, p, q, t, u in todas], open(out, "w"), ensure_ascii=False, indent=1)
print("GUARDADO " + out, flush=True)
