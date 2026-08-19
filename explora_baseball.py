#!/usr/bin/env python3
"""explora_baseball.py — trae los 3 SearchFeeds de baseball 2026 (Series 1, Series 2, Chrome)
con espaciado anti-rate-limit. Muestra: nº items, rango de precios, rookies candidatos.
"""
import json, urllib.request, re, time, random, sys

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

SETS = [
    ("2026 Topps Series 1 - Base", "https://www.comc.com/SearchFeed.aspx?SportID=0&Search=2026+Topps+Series+1+-+%5bBase%5d&Sort=r"),
    ("2026 Topps Series 2 - Base", "https://www.comc.com/SearchFeed.aspx?SportID=0&Search=2026+Topps+Series+2+-+%5bBase%5d&Sort=r"),
    ("2026 Topps Chrome - Base", "https://www.comc.com/SearchFeed.aspx?SportID=0&Search=2026+Topps+Chrome+-+%5bBase%5d&Sort=r"),
]

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get_feed(url):
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "cookies": COOKIES})
    hh = d.get("solution", {}).get("response", "")
    if not hh or "Just a moment" in hh or len(hh) < 2000:
        return None
    # parsear items: buscar IDs de carta con precio
    items = re.findall(r'Cards/[^"]*?/(\d+)"[^>]*>.*?</a>', hh, re.S)
    precios = [float(p) for p in re.findall(r"\$([\d,]+\.\d{2})", hh)]
    return {"len": len(hh), "precios": precios, "items_raw": items}

def main():
    try:
        fs({"cmd": "sessions.destroy", "session": "ghost"}, timeout=30000)
    except Exception:
        pass
    time.sleep(3)
    for nombre, url in SETS:
        r = get_feed(url)
        if r is None:
            print(json.dumps({"set": nombre, "error": "sin_html/500"}, ensure_ascii=False), flush=True)
        else:
            precios = sorted(r["precios"])
            print(json.dumps({
                "set": nombre, "html_len": r["len"],
                "n_precios": len(precios),
                "min": precios[0] if precios else None,
                "max": precios[-1] if precios else None,
                "primeros": precios[:10],
            }, ensure_ascii=False), flush=True)
        time.sleep(random.uniform(30, 40))
    print("OK", flush=True)

if __name__ == "__main__":
    main()
