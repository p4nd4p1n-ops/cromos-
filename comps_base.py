#!/usr/bin/env python3
"""Liquidez de las cartas BASE (Prizm base pura) de los comps.
Vía página de jugador + filtro set → cardId de la base → URL directa.
"""
import json, urllib.request, re, urllib.parse, datetime

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

def base_url_from_player(anio, slug, pid):
    """Página de jugador con filtro set → cardId de la base → URL directa."""
    url = f"https://www.comc.com/Players/Basketball/{slug}/{pid}/Cards/Basketball/{anio}/Panini_Prizm,sh,i100"
    html = get(url)
    # capturar todos los links de la base (con o sin Graded) para extraer el cardId
    pat = re.compile(r'href="(/Cards/Basketball/' + anio + r'/Panini_Prizm_-_Base/(\d+1)/' + slug + r'/(\d+))')
    found = pat.findall(html)
    if not found:
        return None
    # el de menor número = la base pura (.1)
    found.sort(key=lambda x: int(x[1]))
    num, cardid = found[0][1], found[0][2]
    return f"/Cards/Basketball/{anio}/Panini_Prizm_-_Base/{num}/{slug}/{cardid}"

def scan(url):
    html = get("https://www.comc.com" + url)
    m = re.search(r"<title>([^<]+)</title>", html)
    title = m.group(1).strip() if m else "?"
    items = sorted(float(x.group(2).replace(",", "")) for x in re.finditer(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', html))
    sales = re.findall(r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)
    cm = re.search(r"All Sellers.*?qtyforsale.*?\((\d+)\)", html, re.S)
    copias = int(cm.group(1)) if cm else len(items)
    hoy = datetime.date.today()
    v7 = 0
    for f, _ in sales:
        try:
            d = datetime.datetime.strptime(f, "%b %d, %Y").date()
            if (hoy - d).days <= 7:
                v7 += 1
        except ValueError:
            pass
    return {
        "title": title, "min": items[0] if items else None, "seg": items[1] if len(items) > 1 else None,
        "copias": copias, "ventas_7d": v7, "vel": round(v7 / 7, 3),
        "dias_inv": round(copias / (v7 / 7), 1) if v7 else None,
        "turnover": round(v7 / copias * 100, 1) if copias else None,
        "rango": (min(float(p) for _, p in sales), max(float(p) for _, p in sales)) if sales else None,
    }

COMP = [
    ("Jalen Green", "2021-22", "Jalen_Green", "373997"),
    ("Franz Wagner", "2021-22", "Franz_Wagner", "384345"),
    ("Bennedict Mathurin", "2022-23", "Bennedict_Mathurin", "405266"),
    ("Scottie Barnes", "2021-22", "Scottie_Barnes", "383944"),
    ("Amen Thompson", "2023-24", "Amen_Thompson", "387437"),
    ("Paolo Banchero", "2022-23", "Paolo_Banchero", "399070"),
    ("Brandon Miller", "2023-24", "Brandon_Miller", "416640"),
    ("Matas Buzelis", "2024-25", "Matas_Buzelis", "413233"),
    ("Jaylen Wells", "2024-25", "Jaylen_Wells", "464267"),
]

for nombre, anio, slug, pid in COMP:
    print(f"### {nombre} ({anio})")
    base = base_url_from_player(anio, slug, pid)
    if not base:
        print("  base NO encontrada")
        continue
    print("  base:", base)
    r = scan(base)
    print(f"  {r['title'][:70]}")
    print(f"  min={r['min']} seg={r['seg']} copias={r['copias']} ventas7d={r['ventas_7d']} "
          f"vel={r['vel']} dias_inv={r['dias_inv']} turnover={r['turnover']}%")
    if r["rango"]:
        print(f"  rango ventas: ${r['rango'][0]:.2f}-${r['rango'][1]:.2f}")
    print()
