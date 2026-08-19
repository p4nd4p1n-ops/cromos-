#!/usr/bin/env python3
"""Barrido FOOTBALL corregido — SportID=2 (Pin me dio la URL 17:37).
Busca candidatas ≤$5.05 con ≥10 copias entre rookies/top NFL y escanea liquidez.
11/08/2026. Espaciado 35-45s.
"""
import json, urllib.request, re, time, random, sys, html as htmllib, datetime

sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"
COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

JUGADORES = ["Jayden Daniels", "Caleb Williams", "CJ Stroud", "Travis Hunter", "Ashton Jeanty",
             "Shedeur Sanders", "Cam Ward", "Patrick Mahomes", "Josh Allen", "Brock Purdy",
             "Justin Jefferson", "Bijan Robinson", "Ja'Marr Chase", "Lamar Jackson", "Joe Burrow"]

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

def escanear(nombre, url):
    html = ms.get_html(url)
    if not html or len(html) < 2000:
        return {"carta": nombre, "error": "sin_html"}
    sales = [(f, float(p)) for f, p in re.findall(
        r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)]
    hoy = datetime.date.today()
    v7, dias = 0, set()
    for f, _ in sales:
        try:
            fd = datetime.datetime.strptime(f, "%b %d, %Y").date()
            if (hoy - fd).days <= 7:
                v7 += 1
                dias.add(fd)
        except ValueError:
            pass
    precios = []
    for r in re.findall(r'<tr>(.*?)</tr>', html, re.S):
        if 'class="seller"' in r and 'displayprice' in r and 'soldout' not in r and 'allsellers' not in r:
            pm = re.search(r'displayprice.*?class="price">\$([\d.]+)', r, re.S)
            if pm:
                precios.append(float(pm.group(1)))
    precios.sort()
    min_p = precios[0] if precios else None
    seg_p = precios[1] if len(precios) > 1 else None
    gap = ((seg_p - min_p) / min_p * 100) if min_p and seg_p else 0
    return {"carta": nombre, "vel_sem": v7, "dias": len(dias),
            "min": min_p, "seg": seg_p, "gap": round(gap, 1)}

todas = {}
for jug in JUGADORES:
    try:
        feed = get_feed(jug)
    except Exception as e:
        print(f"feed {jug} error: {e}", flush=True)
        continue
    for p, q, t, u in feed:
        tl = t.lower()
        if p > 5.05 or not q or q < 10:
            continue
        if any(x in tl for x in ['psa', 'cga', 'cgc', 'bgs', 'sgc', 'auto', 'relic', 'patch']):
            continue
        todas[t] = (p, q, t, u)
    time.sleep(random.randint(25, 35))

print(f"Candidatas NFL (SportID=2, ≤$5.05, ≥10 copias): {len(todas)}", flush=True)
top = sorted(todas.values(), key=lambda x: x[1], reverse=True)[:10]
print("=== TOP 10 POR COPIAS A ESCANEAR ===", flush=True)
for p, q, t, u in top:
    print(f"  ${p:.2f} x{q} | {t[:65]}", flush=True)

print("\n=== ESCANEANDO LIQUIDEZ ===", flush=True)
resultados = []
for i, (p, q, t, u) in enumerate(top):
    print(f"[{i+1}/{len(top)}] {t[:45]}...", flush=True)
    r = escanear(t[:70], u)
    resultados.append(r)
    print(f"    {r}", flush=True)
    if i < len(top) - 1:
        time.sleep(random.randint(35, 45))

print("\n=== FILTRO M-010 (vel/sem ≥ 13 + gap ≥ 5.3%) ===", flush=True)
for r in sorted(resultados, key=lambda x: x.get("vel_sem", -1), reverse=True):
    if "error" in r:
        print(f"  {r['carta'][:45]}: {r['error']}", flush=True)
        continue
    ok = "✅ PASA" if r["vel_sem"] >= 13 and r["gap"] >= 5.3 else "❌"
    print(f"  {ok} | {r['carta'][:42]:<44} vel/sem {r['vel_sem']:>3} ({r['dias']}d) | muro {r['min']}/{r['seg']} | gap {r['gap']}%", flush=True)
