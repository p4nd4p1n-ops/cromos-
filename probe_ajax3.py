#!/usr/bin/env python3
"""probe_ajax3.py — POST a GetHistoricalSalesInfo con los 4 parámetros exactos
(sourceElement, productKey, itemID, returnUrl) y token AntiXsrf fresco de sesión."""
import json, urllib.request, re, time

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

CARD_URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"
PRODUCT_KEY = "31038639 0 "

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def main():
    try:
        fs({"cmd": "sessions.destroy", "session": "ajax3"}, timeout=30000)
    except Exception:
        pass
    time.sleep(2)
    # 1) cargar página → cookies frescas de sesión (incluido AntiXsrf)
    d = fs({"cmd": "request.get", "url": CARD_URL, "maxTimeout": 90000,
            "session": "ajax3", "cookies": [
                {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
                {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
                {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
            ]})
    html = d.get("solution", {}).get("response", "")
    print("HTML len:", len(html), flush=True)

    # 2) extraer AntiXsrf fresco del HTML si aparece
    xsrf = None
    m = re.search(r'__AntiXsrfToken["\']?\s*[:=]\s*["\']([a-f0-9]+)["\']', html, re.I)
    if m:
        xsrf = m.group(1)
    m2 = re.search(r'name="__AntiXsrfToken"[^>]*value="([a-f0-9]+)"', html, re.I)
    if m2:
        xsrf = m2.group(1)
    print("AntiXsrf en HTML:", xsrf, flush=True)

    # 3) POST con los 4 parámetros exactos de la firma
    body = json.dumps({
        "sourceElement": None,
        "productKey": PRODUCT_KEY,
        "itemID": 0,
        "returnUrl": ""
    })
    headers = [
        {"name": "Content-Type", "value": "application/json; charset=utf-8"},
        {"name": "X-Requested-With", "value": "XMLHttpRequest"},
        {"name": "Referer", "value": CARD_URL},
        {"name": "Origin", "value": "https://www.comc.com"},
    ]
    if xsrf:
        headers.append({"name": "__AntiXsrfToken", "value": xsrf})
    payload = {"cmd": "request.post",
               "url": "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo",
               "maxTimeout": 60000, "session": "ajax3",
               "cookies": [
                   {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
                   {"name": "__AntiXsrfToken", "value": xsrf or "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
                   {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
                   {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
               ],
               "headers": headers,
               "postData": body}
    try:
        r = fs(payload, timeout=90000)
        resp = r.get("solution", {}).get("response", "")
        status = r.get("solution", {}).get("status", "?")
        print("--- POST status:", status, "len:", len(resp), "---", flush=True)
        # si es JSON, mostrarlo; si es HTML de error, indicarlo
        if resp.strip().startswith("{"):
            print(resp[:1500], flush=True)
        else:
            titulo = re.search(r"<title>(.*?)</title>", resp, re.S)
            print("HTML:", titulo.group(1).strip() if titulo else resp[:300], flush=True)
    except Exception as e:
        print("ERROR:", str(e)[:150], flush=True)
    print("FIN", flush=True)

if __name__ == "__main__":
    main()
