#!/usr/bin/env python3
"""Try POST with __RequestVerificationToken header, and also try SOAP request."""
import json, urllib.request, time

FS = "http://127.0.0.1:8191/v1"
def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout+10).read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"solution": {"status": e.code, "response": body, "cookies": []}}

SESSION = "antiforgerytest"
CARD_URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"

try:
    fs({"cmd": "sessions.destroy", "session": SESSION}, timeout=30000)
except:
    pass
time.sleep(1)

# Load card page
print("Loading card page...", flush=True)
d = fs({"cmd": "request.get", "url": CARD_URL, "maxTimeout": 90000, "session": SESSION})
cookies = d.get("solution", {}).get("cookies", [])
html = d.get("solution", {}).get("response", "")

# Extract __AntiXsrfToken from cookies
anti_xsrf = None
for c in cookies:
    if c.get("name") == "__AntiXsrfToken":
        anti_xsrf = c.get("value")
        print("AntiXsrfToken:", anti_xsrf[:40] if anti_xsrf else "NONE", flush=True)

# Also look for it in HTML (hidden field or meta)
import re
m = re.search(r'name="__AntiXsrfToken"[^>]*value="([^"]*)"', html)
if m:
    print("AntiXsrfToken in HTML:", m.group(1)[:40], flush=True)

ENDPOINT = "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo"
body = json.dumps({"sourceElement": "hp31038639_0_", "productKey": "31038639 0 ", "itemID": 0})

# Try 1: with __RequestVerificationToken header
headers1 = [
    {"name": "Content-Type", "value": "application/json; charset=utf-8"},
    {"name": "X-Requested-With", "value": "XMLHttpRequest"},
]
if anti_xsrf:
    headers1.append({"name": "__RequestVerificationToken", "value": anti_xsrf})

d2 = fs({"cmd": "request.post", "url": ENDPOINT, "maxTimeout": 60000, "session": SESSION,
         "postData": body, "cookies": cookies, "headers": headers1})
resp2 = d2.get("solution", {}).get("response", "")
print("\n=== Try 1: with __RequestVerificationToken header ===")
print("Len:", len(resp2), "First 200:", resp2[:200].replace("\n", " "), flush=True)

# Try 2: SOAP request (Content-Type: text/xml)
soap_body = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <GetHistoricalSalesInfo xmlns="http://comc.com/">
      <productKey>31038639 0 </productKey>
      <itemID>0</itemID>
    </GetHistoricalSalesInfo>
  </soap:Body>
</soap:Envelope>"""

headers2 = [
    {"name": "Content-Type", "value": "text/xml; charset=utf-8"},
    {"name": "SOAPAction", "value": "http://comc.com/GetHistoricalSalesInfo"},
]
if anti_xsrf:
    headers2.append({"name": "__RequestVerificationToken", "value": anti_xsrf})

d3 = fs({"cmd": "request.post", "url": "https://www.comc.com/CardPopupService.asmx", "maxTimeout": 60000, "session": SESSION,
         "postData": soap_body, "cookies": cookies, "headers": headers2})
resp3 = d3.get("solution", {}).get("response", "")
print("\n=== Try 2: SOAP request ===")
print("Len:", len(resp3), "First 200:", resp3[:200].replace("\n", " "), flush=True)

# Try 3: request.post with returnCookies=true to capture ANY auth cookies from page load
print("\n=== Cookies from session ===")
all_session_cookies = fs({"cmd": "request.get", "url": CARD_URL, "maxTimeout": 90000, "session": SESSION + "_c", "returnCookies": True})
for c in all_session_cookies.get("solution", {}).get("cookies", []):
    n = c.get("name", "")
    if n in ("AuthCookie", ".ASPXAUTH", "__AntiXsrfToken", "ASP.NET_SessionId"):
        print("  {} = {}...".format(n, str(c.get("value", ""))[:60]), flush=True)

# Try 4: search HTML for alternative sales data endpoint
print("\n=== Alternative endpoints in HTML ===")
for pat in [r'/api/[^"\']*', r'/Services/[^"\']*', r'/Ajax[^"\']*', r'/Chart[^"\']*', r'/History[^"\']*', r'/SalesData[^"\']*']:
    for m in re.finditer(pat, html[:50000]):
        print("  Found:", m.group()[:100], flush=True)

print("\n=== DONE ===", flush=True)
