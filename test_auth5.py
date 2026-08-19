#!/usr/bin/env python3
"""Test 5: depuración completa — cookies exactas de la tabla de Pin (dominios reales)."""
import json, urllib.request, re, time

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

AUTH = "e7DEU7b1HYgq-Ixju4vc7WLmIze-5-VxUrNFu1NzcciMVg9c6YnS3OU5p-cw5n9YU2ar4Oddhft_y1n9tD8RRQ11_vMvh2Zl27RAc3P8d6ok6csQSEyUULfUqc-l4eLd1X5OuHx6baeviCPMTDR9zzh8Q1i_kUcf1xPeAQDyf4-I1pPVLgscKkBQ8D-1K6t95MTPldENazdKxCn7Y_wzwE36ds97txCHROl75OFZZGZl7vPxlEIa9KPEhEjACZy54mWVrxQCx_hdZMnRIDkQtbw0xR2SDc2THSSzppVrp-09mQaUlhf-NxqGVgvHkCjNA03y7fnc-f31R6L2CTp6p4PDsOa1o33j8BGZjnrwlaLayFQ6SPIDCwAfuUy-6HOlEt5B6CQq57eRFBcEpMm9wamevfJEJxcqP5imUZSbq1QFwAa_r0HuUDZbBWLcNzo8UJJ9tpPYQAECwWxyttBwSI2zqOxfSc5iIcpqt1pIAICnkfIXzJdi1F1GEc4DgVZjEE7D2RWgSZKaBkOuQRJ2ilJYf8Ns78TUzs0hzyjOsA6NRCq758lNLcLdaSFUz2wdZEvZPXeHGEmIHdw-lxnzsOkZdq_c_R8WHvsPoM__FKEFyleWbT7voOUDxRxEAp1WL45qppLNehPcJzjRd5w8GnTg5LY5RGHeUcf5AAKDgBH2zT0LBHrH6OqgojH7ZVd9SGWPQlSTiQfhilU1q0WyUlVPW5C9tuClIbutNq7ITsbS2j1rUh-1p84vaX6kPq0aJlflWEDI82TOCQt5tsElJADTjbJBezyA5WjwUjFiKTylLwRFFSvxeFzczCpRZuIM4GfQYUv8_5BoZuNu34P1gf0tTBN8kckQVjHjF7soG1cyePWBpD5Ql_VsmurfHrNaYkShLTvgNuWBTjxd27iJqA"

# Dominios EXACTOS de la tabla que pegó Pin
cookies = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "ai_user", "value": "cuFR2|2026-08-07T10:41:06.515Z", "domain": "www.comc.com", "path": "/"},
    {"name": "cart", "value": "46f37386-b228-462d-88a2-51ec385daabc", "domain": "www.comc.com", "path": "/"},
    {"name": "cartInfo", "value": "3", "domain": "www.comc.com", "path": "/"},
    {"name": "ARRAffinity", "value": "b098ca8f7329f613b0444fe2e36518169fa3aa6be5697a00461cd33c61ddf9af", "domain": ".www.comc.com", "path": "/"},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
    {"name": "_fbp", "value": "fb.1.1786099266530.898341706512927956", "domain": ".comc.com", "path": "/"},
]

# limpiar
for s in ["pincomc", "pincomc2", "pincomc3"]:
    try:
        fs({"cmd": "sessions.destroy", "session": s}, timeout=30000)
    except Exception:
        pass
time.sleep(1)

# crear sesión con cookies
try:
    d = fs({"cmd": "sessions.create", "session": "pincomc3", "cookies": cookies}, timeout=60000)
    print("create:", d.get("status"), d.get("message", ""))
except Exception as e:
    print("create error:", str(e)[:300])

time.sleep(2)

# ver cookies de la sesión (sessions.get?)
try:
    d = fs({"cmd": "sessions.get", "session": "pincomc3"}, timeout=30000)
    print("sessions.get:", json.dumps(d, ensure_ascii=False)[:500])
except Exception as e:
    print("sessions.get error:", str(e)[:150])

# request a la carta
url = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2631/Derik_Queen/31038651"
try:
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "pincomc3"})
    html = d.get("solution", {}).get("response", "")
    open("/tmp/queen_ses4.html", "w").write(html)
    print("tam:", len(html))
    print("logueado:", bool(re.search(r"Sign Out|Log Out", html, re.I)))
    print("tiene 0.80:", bool(re.search(r"\$0\.80", html)))
    print("tiene 1.17:", bool(re.search(r"\$1\.17", html)))
    m = re.search(r"<title>([^<]+)</title>", html)
    print("title:", m.group(1).strip() if m else "?")
except Exception as e:
    print("request error:", str(e)[:300])
