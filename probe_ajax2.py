#!/usr/bin/env python3
"""probe_ajax2.py — 1) descarga el proxy JS de CardPopupService.asmx/js para ver
los métodos exactos del servicio, 2) reintenta el POST con headers XHR reales."""
import json, urllib.request, re, time, urllib.parse

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

CARD_URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"
PRODUCT_KEY = "31038639 0 "

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def main():
    try:
        fs({"cmd": "sessions.destroy", "session": "ajax2"}, timeout=30000)
    except Exception:
        pass
    time.sleep(2)
    # 1) cargar página para sesión
    fs({"cmd": "request.get", "url": CARD_URL, "maxTimeout": 90000,
        "session": "ajax2", "cookies": COOKIES})
    time.sleep(2)

    # 2) descargar el proxy JS del servicio
    d = fs({"cmd": "request.get", "url": "https://www.comc.com/CardPopupService.asmx/js",
            "maxTimeout": 60000, "session": "ajax2", "cookies": COOKIES})
    js = d.get("solution", {}).get("response", "")
    print("JS len:", len(js), flush=True)
    open("/root/comc-data/cardpopup-proxy.js", "w").write(js)
    # extraer nombres de métodos y firmas
    metodos = re.findall(r"(\w+)\s*=\s*function\s*\([^)]*\)", js)
    print("métodos en proxy:", metodos[:30], flush=True)
    # mostrar las llamadas al servicio (ServiceMethod)
    for m in re.finditer(r"(?:ServiceMethod|\.asmx/)(\w+)", js):
        pass
    for m in re.finditer(r'"(https?://[^"]*CardPopupService[^"]*)"', js):
        print("URL servicio:", m.group(1), flush=True)
    # buscar GetHistoricalSalesInfo y su firma
    i = js.find("GetHistoricalSalesInfo")
    if i >= 0:
        print("--- firma GetHistoricalSalesInfo ---", flush=True)
        print(js[max(0,i-300):i+700], flush=True)

    # 3) POST con headers XHR + AntiXsrf
    headers = [
        {"name": "Content-Type", "value": "application/json; charset=utf-8"},
        {"name": "X-Requested-With", "value": "XMLHttpRequest"},
        {"name": "Referer", "value": CARD_URL},
        {"name": "Origin", "value": "https://www.comc.com"},
        {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545"},
    ]
    payload = {"cmd": "request.post",
               "url": "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo",
               "maxTimeout": 60000, "session": "ajax2", "cookies": COOKIES,
               "headers": headers,
               "postData": json.dumps({"productKey": PRODUCT_KEY})}
    try:
        r = fs(payload, timeout=90000)
        resp = r.get("solution", {}).get("response", "")
        print("--- POST XHR len:", len(resp), "---", flush=True)
        print(resp[:800], flush=True)
    except Exception as e:
        print("ERROR POST:", str(e)[:150], flush=True)

    print("FIN", flush=True)

if __name__ == "__main__":
    main()
