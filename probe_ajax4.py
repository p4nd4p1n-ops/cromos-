#!/usr/bin/env python3
"""probe_ajax4.py — POST con AuthCookie fresco de la sesión pincomc4.
El AuthCookie hardcodeado está caducado; este usa el que FlareSolverr
devolvió en el GET de la sesión pincomc4 (extraído previamente)."""
import json, urllib.request, re

FS = "http://127.0.0.1:8191/v1"
XSRF = "957fc2df480843859e9fa1bac46db545"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
CARD_URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"
AUTH_FRESCO = "e7DEU7b1HYgq-Ixju4vc7WLmIze-5-VxUrNFu1NzcciMVg9c6YnS3OU5p-cw5n9YU2ar4Oddhft_y1n9tD8RRQ11_vMvh2Zl27RAc3P8d6ok6csQSEyUULfUqc-l4eLd1X5OuHx6baeviCPMTDR9zzh8Q1i_kUcf1xPeAQDyf4-I1pPVLgscKkBQ8D-1K6t95MTPldENazdKxCn7Y_wzwE36ds97txCHROl75OFZZGZl7vPxlEIa9KPEhEjACZy54mWVrxQCx_hdZMnRIDkQtbw0xR2SDc2THSSzppVrp-09mQaUlhf-NxqGVgvHkCjNA03y7fnc-f31R6L2CTp6p4PDsOa1o33j8BGZjnrwlaLayFQ6SPIDCwAfuUy-6HOlEt5B6CQq57eRFBcEpMm9wamevfJEJxcqP5imUZSbq1QFwAa_r0HuUDZbBWLcNzo8UJJ9tpPYQAECwWxyttBwSI2zqOxfSc5iIcpqt1pIAICnkfIXzJdi1F1GE"

cookies = [
    {"name": "AuthCookie", "value": AUTH_FRESCO, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": XSRF, "domain": "www.comc.com", "path": "/"},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 10).read())

bodies = [
    '{"sourceElement":null,"productKey":"31038639 0 ","itemID":0,"returnUrl":null}',
    '{"sourceElement":"hp31038639_0_","productKey":"31038639 0 ","itemID":0,"returnUrl":""}',
    '{"productKey":"31038639 0 ","itemID":0}',
    '{"productKey":"","itemID":326870496}',
]
for i, body in enumerate(bodies):
    payload = {"cmd": "request.post",
               "url": "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo",
               "maxTimeout": 60000, "session": "pincomc4", "cookies": cookies,
               "headers": [
                   {"name": "Content-Type", "value": "application/json; charset=utf-8"},
                   {"name": "X-Requested-With", "value": "XMLHttpRequest"},
                   {"name": "Origin", "value": "https://www.comc.com"},
                   {"name": "Referer", "value": CARD_URL},
                   {"name": "Accept", "value": "application/json"},
                   {"name": "User-Agent", "value": UA},
               ],
               "postData": body}
    try:
        r = fs(payload, timeout=90000)
        resp = r.get("solution", {}).get("response", "")
        es_json = resp.strip().startswith("{")
        tipo = "JSON" if es_json else "HTML"
        print("--- body %d: len %d %s ---" % (i, len(resp), tipo), flush=True)
        if es_json:
            print(resp[:1000], flush=True)
        else:
            m = re.search(r"<title>(.*?)</title>", resp, re.S)
            print("title:", m.group(1).strip() if m else resp[:150], flush=True)
    except Exception as e:
        print("body %d ERROR: %s" % (i, str(e)[:100]), flush=True)
print("FIN", flush=True)
