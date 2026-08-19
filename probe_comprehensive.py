#!/usr/bin/env python3
"""Comprehensive probe: use FlareSolverr and also try request.post with execute to call the JS method."""
import json, urllib.request, re, time

FS = "http://127.0.0.1:8191/v1"
def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout+10).read())
    except Exception as e:
        return {"solution": {"status": -1, "response": str(e), "cookies": []}}

SESSION = "salesprobe4"
CARD_URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"

try:
    fs({"cmd": "sessions.destroy", "session": SESSION}, timeout=30000)
except:
    pass
time.sleep(2)

# 1. Load card page
print("=== Loading card page ===", flush=True)
d = fs({"cmd": "request.get", "url": CARD_URL, "maxTimeout": 120000, "session": SESSION})
html = d.get("solution", {}).get("response", "")
cookies = d.get("solution", {}).get("cookies", [])
print("HTML len: {}, cookies: {}".format(len(html), len(cookies)), flush=True)

# 2. Search for ALL script blocks with sales-related code
print("\n=== Searching for sales data in HTML ===", flush=True)

# Look for script blocks that define sales/sparkline data
for m in re.finditer(r'<script[^>]*>([\s\S]*?)</script>', html):
    script = m.group(1)
    if any(kw in script.lower() for kw in ['historicalsale', 'sparkline', 'saleinfo', 'salesdata', 'quarterly', 'spark', 'chart']):
        print("FOUND relevant script ({} chars):".format(len(script)), flush=True)
        print(script[:2000], flush=True)
        print("---", flush=True)

# Also look for data- attributes with sales data
for m in re.finditer(r'data-[^=]*=[\"\']([^\"\']*sale[^\"\']*|\{[^}]*\})[\"\']', html, re.I):
    print("Data attribute:", m.group()[:200], flush=True)

# 3. Try FlareSolverr's request.post with different approach
print("\n=== Try POST with the card page's exact cookies ===", flush=True)
# Use the HTML page's own cookies for POST
# Build cookie dict from FlareSolverr response
cookie_objects = []
for c in cookies:
    cookie_objects.append({
        "name": c.get("name"),
        "value": c.get("value"),
        "domain": c.get("domain", "www.comc.com"),
        "path": c.get("path", "/"),
    })
    if c.get("httpOnly"):
        cookie_objects[-1]["httpOnly"] = True
    if c.get("secure"):
        cookie_objects[-1]["secure"] = True

body = json.dumps({"sourceElement": "hp31038639_0_", "productKey": "31038639 0 ", "itemID": 0})

# Print cookies being sent
for c in cookies:
    n = c.get("name","")
    if n in ("ASP.NET_SessionId", "__AntiXsrfToken", "ARRAffinity", "cf_clearance", "AuthCookie"):
        print("  Cookie {}: {}...".format(n, str(c.get("value",""))[:40]), flush=True)

d2 = fs({"cmd": "request.post",
         "url": "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo",
         "maxTimeout": 60000,
         "session": SESSION,
         "postData": body,
         "cookies": cookies,
         "headers": [
             {"name": "Content-Type", "value": "application/json; charset=utf-8"},
             {"name": "X-Requested-With", "value": "XMLHttpRequest"},
             {"name": "Accept", "value": "application/json, text/javascript, */*; q=0.01"},
             {"name": "Referer", "value": CARD_URL},
             {"name": "Origin", "value": "https://www.comc.com"},
         ]})
resp2 = d2.get("solution", {}).get("response", "")
status2 = d2.get("solution", {}).get("status", "?")
print("POST status: {}, len: {}".format(status2, len(resp2)), flush=True)
if resp2.strip().startswith("{"):
    print("SUCCESS:", resp2[:2000], flush=True)
else:
    title = re.search(r'<title>([^<]*)</title>', resp2, re.I)
    print("Title:", title.group(1).strip() if title else "N/A", flush=True)

# 4. Try with the page html's __AntiXsrfToken as header AND cookie
print("\n=== Try POST with __RequestVerificationToken ===", flush=True)
anti_xsrf = None
for c in cookies:
    if c.get("name") == "__AntiXsrfToken":
        anti_xsrf = c.get("value")

headers3 = [
    {"name": "Content-Type", "value": "application/json; charset=utf-8"},
    {"name": "X-Requested-With", "value": "XMLHttpRequest"},
    {"name": "Accept", "value": "application/json, text/javascript, */*; q=0.01"},
    {"name": "Referer", "value": CARD_URL},
]
if anti_xsrf:
    headers3.append({"name": "__RequestVerificationToken", "value": anti_xsrf})
    headers3.append({"name": "RequestVerificationToken", "value": anti_xsrf})

d3 = fs({"cmd": "request.post",
         "url": "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo",
         "maxTimeout": 60000,
         "session": SESSION,
         "postData": body,
         "cookies": cookies,
         "headers": headers3})
resp3 = d3.get("solution", {}).get("response", "")
print("POST len:", len(resp3), flush=True)
if resp3.strip().startswith("{"):
    print("SUCCESS:", resp3[:2000], flush=True)
else:
    title = re.search(r'<title>([^<]*)</title>', resp3, re.I)
    print("Title:", title.group(1).strip() if title else "N/A", flush=True)

# 5. Also search for any chart API endpoint
print("\n=== Searching for chart/sales endpoints ===", flush=True)
for pat in [r'/api/[^"\'\s]+', r'/[Cc]hart[^"\'\s]*', r'/[Hh]istory[^"\'\s]*', 
             r'/Services/[^"\'\s]*\.(asmx|svc|ashx)[^"\'\s]*', r'/Ajax[^"\'\s]*']:
    for m in re.finditer(pat, html[:100000]):
        url = m.group()
        if len(url) > 10:
            print("  Found:", url, flush=True)

print("\n=== DONE ===", flush=True)
