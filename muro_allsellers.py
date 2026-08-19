#!/usr/bin/env python3
"""muro_allsellers.py — extrae el muro (vendedor/precio/copias) de Durant y Wemby y lo guarda en JSON."""
import json, urllib.request, re, html as h

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

CARTAS = [
    ("Kevin Durant", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/1551/Kevin_Durant/31038541"),
    ("Victor Wembanyama", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038608"),
]

out = {}
for nombre, url in CARTAS:
    try:
        d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "ghost", "cookies": COOKIES})
        html = d.get("solution", {}).get("response", "")
        filas = re.findall(
            r'<td class="seller">\s*<a[^>]*>([^<]+)</a>.*?'
            r'<td class="displayprice"><span class="price">\$([\d,]+\.\d{2})</span>.*?'
            r'<td class="qtyforsale">(?:\s*<span[^>]*>\s*)?(?:&nbsp;)?\(?(\d+)\)?',
            html, re.S)
        muro = []
        vistos = set()
        for seller, precio, qty in filas:
            seller = h.unescape(seller).strip()
            if (seller, precio) in vistos:
                continue
            vistos.add((seller, precio))
            muro.append({"vendedor": seller, "precio": float(precio.replace(",", "")), "copias": int(qty)})
        # agregar por precio (sumar copias del mismo precio)
        por_precio = {}
        for m in muro:
            por_precio.setdefault(m["precio"], 0)
            por_precio[m["precio"]] += m["copias"]
        out[nombre] = {
            "url": url,
            "muro": muro,
            "por_precio": {f"{p:.2f}": c for p, c in sorted(por_precio.items())},
            "total_copias": sum(m["copias"] for m in muro),
            "n_vendedores": len(muro),
        }
        print(f"{nombre}: {out[nombre]['total_copias']} copias, {out[nombre]['n_vendedores']} ofertas")
        for p, c in out[nombre]["por_precio"].items():
            print(f"   ${p} x {c}")
    except Exception as e:
        print(f"{nombre}: error {str(e)[:120]}")

json.dump(out, open("/root/comc-data/muro-2026-08-08.json", "w"), ensure_ascii=False, indent=1)
print("guardado: /root/comc-data/muro-2026-08-08.json")
