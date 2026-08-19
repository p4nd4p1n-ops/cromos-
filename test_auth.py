#!/usr/bin/env python3
"""Test AuthCookie de Pin contra Queen (debe dar $0.80 si la sesión funciona)."""
import json, urllib.request, re

FS = "http://127.0.0.1:8191/v1"
AUTH = "e7DEU7b1HYgq-Ixju4vc7WLmIze-5-VxUrNFu1NzcciMVg9c6YnS3OU5p-cw5n9YU2ar4Oddhft_y1n9tD8RRQ11_vMvh2Zl27RAc3P8d6ok6csQSEyUULfUqc-l4eLd1X5OuHx6baeviCPMTDR9zzh8Q1i_kUcf1xPeAQDyf4-I1pPVLgscKkBQ8D-1K6t95MTPldENazdKxCn7Y_wzwE36ds97txCHROl75OFZZGZl7vPxlEIa9KPEhEjACZy54mWVrxQCx_hdZMnRIDkQtbw0xR2SDc2THSSzppVrp-09mQaUlhf-NxqGVgvHkCjNA03y7fnc-f31R6L2CTp6p4PDsOa1o33j8BGZjnrwlaLayFQ6SPIDCwAfuUy-6HOlEt5B6CQq57eRFBcEpMm9wamevfJEJxcqP5imUZSbq1QFwAa_r0HuUDZbBWLcNzo8UJJ9tpPYQAECwWxyttBwSI2zqOxfSc5iIcpqt1pIAICnkfIXzJdi1F1GEc4DgVZjEE7D2RWgSZKaBkOuQRJ2ilJYf8Ns78TUzs0hzyjOsA6NRCq758lNLcLdaSFUz2wdZEvZPXeHGEmIHdw-lxnzsOkZdq_c_R8WHvsPoM__FKEFyleWbT7voOUDxRxEAp1WL45qppLNehPcJzjRd5w8GnTg5LY5RGHeUcf5AAKDgBH2zT0LBHrH6OqgojH7ZVd9SGWPQlSTiQfhilU1q0WyUlVPW5C9tuClIbutNq7ITsbS2j1rUh-1p84vaX6kPq0aJlflWEDI82TOCQt5tsElJADTjbJBezyA5WjwUjFiKTylLwRFFSvxeFzczCpRZuIM4GfQYUv8_5BoZuNu34P1gf0tTBN8kckQVjHjF7soG1cyePWBpD5Ql_VsmurfHrNaYkShLTvgNuWBTjxd27iJqA"

def fs_get(url, headers=None, timeout=60000):
    payload = {"cmd": "request.get", "url": url, "maxTimeout": timeout}
    if headers:
        payload["headers"] = headers
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

COOKIE = ("AuthCookie=" + AUTH +
          "; __AntiXsrfToken=957fc2df480843859e9fa1bac46db545" +
          "; ASP.NET_SessionId=t2ghz14y2gxy5uvgz4m0k0rp" +
          "; cart=46f37386-b228-462d-88a2-51ec385daabc" +
          "; SiteAffinity=legacy")

url = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2631/Derik_Queen/31038651"
d = fs_get(url, {"Cookie": COOKIE})
html = d.get("solution", {}).get("response", "")
open("/tmp/queen_auth.html", "w").write(html)
print("tam:", len(html))
print("logueado:", bool(re.search(r"Sign Out|Log Out", html, re.I)))
print("tiene 0.80:", bool(re.search(r"\$0\.80", html)))
print("tiene 1.17:", bool(re.search(r"\$1\.17", html)))
# tabla allsellers
for m in re.finditer(r'<td class="seller">\s*<a[^>]*>([^<]+)</a>.*?<td class="displayprice"><span class="price">\$([\d,]+\.\d{2})', html, re.S):
    print("seller:", m.group(1).strip(), "| precio:", m.group(2))
