#!/usr/bin/env python3
"""Liquidez y precio de los comps de Knueppel (Wagner 21-22, Mathurin 22-23, Green 21-22)
en su año rookie vs Knueppel 2025-26. Carta base del set flagship de cada año.
"""
import json, urllib.request, re, urllib.parse, datetime
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

def find_player_id(nombre):
    html = get("https://www.comc.com/Search.aspx?search=" + urllib.parse.quote(nombre))
    slug = nombre.replace(" ", "_")
    m = re.search(r"/Players/Basketball/" + slug + r"/c(\d+)", html)
    return m.group(1) if m else None

def find_base_card(player_path, set_url, anio, slug):
    """Página de jugador con filtro de set → link de la carta BASE pura del Prizm."""
    phtml = get("https://www.comc.com" + player_path + set_url)
    pat = re.compile(r'href="(/Cards/Basketball/' + anio + r'/Panini_Prizm_-_Base/[^"]*' + slug + r'[^"]*)"')
    links = pat.findall(phtml)
    # quitar gradadas, aftermarket y paralelas (el base puro es el de menor longitud)
    limpios = [l for l in sorted(set(links))
               if "/Graded/" not in l and "/Aftermarket" not in l
               and not re.search(r'_-_Base_-_', l)]
    if not limpios:
        return None
    limpios.sort(key=len)
    return limpios[0]

def scan_card(url):
    html = get(url)
    m = re.search(r"<title>([^<]+)</title>", html)
    title = m.group(1).strip() if m else "?"
    items = sorted(float(x.group(2).replace(",", "")) for x in re.finditer(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', html))
    sales = re.findall(r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)
    copias_m = re.search(r"All Sellers.*?qtyforsale.*?\((\d+)\)", html, re.S)
    copias = int(copias_m.group(1)) if copias_m else len(items)
    hoy = datetime.date.today()
    v7 = 0
    for f, p in sales:
        try:
            d = datetime.datetime.strptime(f, "%b %d, %Y").date()
            if (hoy - d).days <= 7:
                v7 += 1
        except ValueError:
            pass
    return {
        "title": title, "min": items[0] if items else None, "seg": items[1] if len(items) > 1 else None,
        "copias": copias, "n_items": len(items), "ventas_7d": v7,
        "vel": round(v7 / 7, 3),
        "dias_inv": round(copias / (v7 / 7), 1) if v7 else None,
        "turnover": round(v7 / copias * 100, 1) if copias else None,
        "rango_sales": (min(float(p) for _, p in sales), max(float(p) for _, p in sales)) if sales else None,
    }

# (nombre, set_url del año rookie, anio set)
COMP = [
    # comps de Knueppel
    ("Jalen Green", "/Cards/Basketball/2021-22/Panini_Prizm,sh,i100", "2021-22"),
    ("Franz Wagner", "/Cards/Basketball/2021-22/Panini_Prizm,sh,i100", "2021-22"),
    ("Bennedict Mathurin", "/Cards/Basketball/2022-23/Panini_Prizm,sh,i100", "2022-23"),
    # comps de Edgecombe
    ("Scottie Barnes", "/Cards/Basketball/2021-22/Panini_Prizm,sh,i100", "2021-22"),
    ("Amen Thompson", "/Cards/Basketball/2023-24/Panini_Prizm,sh,i100", "2023-24"),
    # comps de Flagg
    ("Paolo Banchero", "/Cards/Basketball/2022-23/Panini_Prizm,sh,i100", "2022-23"),
    ("Brandon Miller", "/Cards/Basketball/2023-24/Panini_Prizm,sh,i100", "2023-24"),
    # comps de Harper
    ("Matas Buzelis", "/Cards/Basketball/2024-25/Panini_Prizm,sh,i100", "2024-25"),
    ("Jaylen Wells", "/Cards/Basketball/2024-25/Panini_Prizm,sh,i100", "2024-25"),
]

for nombre, set_url, anio in COMP:
    print(f"########## {nombre} ##########")
    pid = find_player_id(nombre)
    print("  playerId:", pid)
    if not pid:
        continue
    path = f"/Players/Basketball/{nombre.replace(' ', '_')}/{pid}"
    base = find_base_card(path, set_url, anio, nombre.replace(" ", "_"))
    print("  base:", base)
    if not base:
        continue
    r = scan_card("https://www.comc.com" + base)
    print(f"  carta: {r['title'][:80]}")
    print(f"  min={r['min']} seg={r['seg']} copias={r['copias']} ventas7d={r['ventas_7d']} "
          f"vel={r['vel']} dias_inv={r['dias_inv']} turnover={r['turnover']}%")
    if r["rango_sales"]:
        print(f"  rango ventas página: ${r['rango_sales'][0]:.2f}-${r['rango_sales'][1]:.2f}")
    print()
