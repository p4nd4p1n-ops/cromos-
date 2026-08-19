#!/usr/bin/env python3
"""probe_ajax.py — investiga el endpoint AJAX del historial de ventas de COMC.
Pista: el HTML llama historicalSaleInfo.get(this, "31038608 0 ", 0) y en TOOLS.md
consta que el endpoint es CardPopupService.asmx/GetHistoricalSalesInfo con
productKey="<cardId> 0 " (pendiente de resolver: daba error).
Este probe: 1) busca en el HTML la URL exacta del servicio, 2) prueba el POST
con varias variantes (JSON / form, con y sin cookies) y muestra qué devuelve.
"""
import json, urllib.request, re, time

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

CARD_URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"
CARD_ID = "31038639"
PRODUCT_KEY = "31038639 0 "

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def main():
    # 1) sesión: cargar la página de la carta primero (para cookies de sesión válidas)
    try:
        fs({"cmd": "sessions.destroy", "session": "ajax"}, timeout=30000)
    except Exception:
        pass
    time.sleep(2)
    d = fs({"cmd": "request.get", "url": CARD_URL, "maxTimeout": 90000,
            "session": "ajax", "cookies": COOKIES})
    html = d.get("solution", {}).get("response", "")
    print("HTML len:", len(html), flush=True)

    # 2) buscar la URL exacta del servicio en el HTML (pistas: asmx, CardPopup, SalesInfo)
    pistas = re.findall(r'(https?://[^"\']*?(?:CardPopup|SalesInfo|\.asmx)[^"\']*)', html)
    print("pistas de endpoint en HTML:", pistas[:10], flush=True)
    for m in re.finditer(r'([A-Za-z0-9_]+\.asmx/[A-Za-z0-9_]+)', html):
        print("ASMX:", m.group(1), flush=True)

    # 3) probar el POST al endpoint conocido, variantes
    endpoints = [
        "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo",
        "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfoPopup",
        "https://www.comc.com/Services/CardPopupService.asmx/GetHistoricalSalesInfo",
    ]
    cuerpos = [
        {"cmd": "request.post", "url": endpoints[0], "maxTimeout": 60000,
         "session": "ajax", "cookies": COOKIES,
         "postData": json.dumps({"productKey": PRODUCT_KEY}),
         "headers": [{"name": "Content-Type", "value": "application/json; charset=utf-8"}]},
        {"cmd": "request.post", "url": endpoints[0], "maxTimeout": 60000,
         "session": "ajax", "cookies": COOKIES,
         "postData": f"productKey={urllib.parse.quote(PRODUCT_KEY)}",
         "headers": [{"name": "Content-Type", "value": "application/x-www-form-urlencoded"}]},
        {"cmd": "request.post", "url": endpoints[1], "maxTimeout": 60000,
         "session": "ajax", "cookies": COOKIES,
         "postData": json.dumps({"productKey": PRODUCT_KEY}),
         "headers": [{"name": "Content-Type", "value": "application/json; charset=utf-8"}]},
    ]
    for i, payload in enumerate(cuerpos):
        try:
            r = fs(payload, timeout=90000)
            sol = r.get("solution", {})
            resp = sol.get("response", "")
            status = sol.get("status", "?")
            print(f"--- POST {i}: status {status}, len {len(resp)} ---", flush=True)
            print(resp[:500].replace("\n", " "), flush=True)
        except Exception as e:
            print(f"--- POST {i}: ERROR {str(e)[:120]} ---", flush=True)
        time.sleep(5)

    print("FIN", flush=True)

if __name__ == "__main__":
    main()
