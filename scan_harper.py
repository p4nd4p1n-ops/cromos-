#!/usr/bin/env python3
"""Scan puntual de Harper (OP-001) — seguimiento de muro, 11/08/2026."""
import json, urllib.request, re, time, datetime

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get_html(url, session="ghost", retries=3, base_wait=20):
    for i in range(retries):
        try:
            d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": session, "cookies": COOKIES})
            hh = d.get("solution", {}).get("response", "")
            if hh and len(hh) > 2000:
                return hh
            print(f"  intento {i+1}: html corto/vacio ({len(hh)}), esperando {base_wait*(i+1)}s...")
            time.sleep(base_wait*(i+1))
        except Exception as e:
            print(f"  intento {i+1} error: {e}, esperando {base_wait*(i+1)}s...")
            time.sleep(base_wait*(i+1))
    return ""

def parse_muro(html):
    """Extrae escalones del muro de vendedores."""
    # precio + vendedor + copias
    rows = re.findall(r'\$(\d+\.\d{2})[^$]{0,200}?([A-Za-z0-9_\-]{3,30})', html)
    escalones = []
    seen = set()
    for precio, vendedor in rows:
        p = float(precio)
        if p < 0.5 or p > 500:
            continue
        key = (p, vendedor)
        if key in seen:
            continue
        seen.add(key)
        escalones.append((p, vendedor))
    escalones.sort()
    return escalones[:8]

html = get_html(URL)
if not html:
    print("FALLO: sin HTML")
else:
    open("/tmp/harper-muro.html", "w").write(html)
    esc = parse_muro(html)
    print(f"Harper — muro ({len(esc)} escalones únicos):")
    for p, v in esc[:6]:
        print(f"  ${p:.2f} | {v}")
    # detectar si nuestra copia (13.49) sigue
    mios = [p for p, v in esc if abs(p - 13.49) < 0.01]
    print(f"\nNuestra copia a $13.49: {'SIGUE en el muro' if mios else 'NO se ve (¿vendida?)'}")
    # ventas recientes (pills de venta)
    ventas = re.findall(r'(\d+) sold in last 7 days', html, re.I)
    if ventas:
        print(f"Ventas 7d (etiqueta): {ventas[0]}")
    tiempo = datetime.datetime.now().strftime("%H:%M")
    print(f"Hora scan: {tiempo} UTC")
