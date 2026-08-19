#!/usr/bin/env python3
"""Rookies draft 2024: playerId → carta base Prizm → recent sales → vel/día y rango."""
import json, urllib.request, re, urllib.parse, datetime
from collections import defaultdict

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

# (nombre, slug, playerId conocido o None)
JUGADORES = [
    ("Stephon Castle", "Stephon_Castle", None),
    ("Alex Sarr", "Alex_Sarr", None),
    ("Donovan Clingan", "Donovan_Clingan", "c421549"),
    ("Matas Buzelis", "Matas_Buzelis", None),
]

def find_player_id(nombre):
    html = get("https://www.comc.com/Search.aspx?search=" + urllib.parse.quote(nombre))
    pat = re.compile(r'href="(/Players/Basketball/' + nombre.replace(" ", "_") + r'/c\d+)"')
    m = pat.search(html)
    if m:
        return m.group(1).split("/")[-1]
    return None

def find_base_prizm(player_path):
    """Página de jugador con filtro 2024-25 Prizm → link carta base."""
    phtml = get("https://www.comc.com" + player_path + "/Cards/Basketball/2024-25/Panini_Prizm,sh,i100")
    links = re.findall(r'href="(/Cards/Basketball/2024-25/Panini_Prizm[^"]*)"', phtml)
    # base = 6 segmentos, sin Graded/SP/Variation/paralela
    base = [l for l in sorted(set(links)) if l.count("/") == 6
            and not any(x in l for x in ["Graded", "Variation", "SP_", "Prizm_-", "Refractor"])]
    return base[0] if base else None

def analyze_card(url):
    html = get(url)
    m = re.search(r"<title>([^<]+)</title>", html)
    title = m.group(1).strip() if m else "?"
    sales = re.findall(r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)
    items = [float(x.group(2).replace(",", "")) for x in re.finditer(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', html)]
    return title, sales, items

for nombre, slug, pid in JUGADORES:
    print(f"########## {nombre} ##########")
    if not pid:
        pid = find_player_id(nombre)
        print("  playerId:", pid)
        if not pid:
            print("  NO ENCONTRADO")
            continue
    player_path = f"/Players/Basketball/{slug}/{pid}"
    base = find_base_prizm(player_path)
    if not base:
        print("  sin carta base Prizm clara")
        continue
    print("  carta base:", base)
    title, sales, items = analyze_card("https://www.comc.com" + base)
    print("  title:", title[:80])
    # velocidad
    hoy = datetime.date.today()
    v7 = 0
    for f, p in sales:
        try:
            d = datetime.datetime.strptime(f, "%b %d, %Y").date()
            if (hoy - d).days <= 7:
                v7 += 1
        except ValueError:
            pass
    precios = [float(p.replace(",", "")) for _, p in sales]
    rango = f"${min(precios):.2f}-${max(precios):.2f}" if precios else "?"
    print(f"  ventas página: {len(sales)} | ventas 7d: {v7} | vel/día: {v7/7:.2f}")
    if items:
        print(f"  listados hoy: {len(items)} | min ${min(items):.2f}")
    if precios:
        print(f"  rango ventas (página): {rango} | media ${sum(precios)/len(precios):.2f}")
    print("  ventas:", [(f, p) for f, p in sales[:12]])
    print()
