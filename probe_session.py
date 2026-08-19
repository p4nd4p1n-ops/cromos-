#!/usr/bin/env python3
"""Test ASMX endpoint with session cookies from card page load."""
import json, urllib.request, time

FS = "http://127.0.0.1:8191/v1"
def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout+10).read())

SESSION = "asmx_cookie_test"
CARD_URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"

# Clean
try:
    fs({"cmd": "sessions.destroy", "session": SESSION}, timeout=30000)
except:
    pass
time.sleep(1)

# Step 1: Load card page to get session cookies
print("=== Load card page ===", flush=True)
d = fs({"cmd": "request.get", "url": CARD_URL, "maxTimeout": 90000, "session": SESSION})
cookies = d.get("solution", {}).get("cookies", [])
print("Got {} cookies".format(len(cookies)), flush=True)

# Extract key cookies
for c in cookies:
    n = c.get("name")
    if n in ("ASP.NET_SessionId", "__AntiXsrfToken", "cf_clearance", "ARRAffinity", "ARRAffinitySameSite", "AuthCookie"):
        print("  {} = {}...".format(n, str(c.get("value", ""))[:60]), flush=True)

# Step 2: GET .asmx with these cookies
print("\n=== GET CardPopupService.asmx with cookies ===", flush=True)
d2 = fs({"cmd": "request.get",
         "url": "https://www.comc.com/CardPopupService.asmx",
         "maxTimeout": 60000,
         "session": SESSION,
         "cookies": cookies})
resp2 = d2.get("solution", {}).get("response", "")
print("Len: {}, First 500: {}".format(len(resp2), resp2[:500].replace("\n", " ")), flush=True)

# Step 3: POST to GetHistoricalSalesInfo with session cookies
print("\n=== POST GetHistoricalSalesInfo ===", flush=True)
body = json.dumps({"sourceElement": "hp31038639_0_", "productKey": "31038639 0 ", "itemID": 0})
d3 = fs({"cmd": "request.post",
         "url": "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo",
         "maxTimeout": 60000,
         "session": SESSION,
         "postData": body,
         "cookies": cookies,
         "headers": [{"name": "Content-Type", "value": "application/json; charset=utf-8"}]})
resp3 = d3.get("solution", {}).get("response", "")
print("Len: {}, First 500: {}".format(len(resp3), resp3[:500].replace("\n", " ")), flush=True)

# Step 4: What about GET with query string? 
print("\n=== GET with query string ===", flush=True)
import urllib.parse
qs = urllib.parse.urlencode({"productKey": "31038639 0 ", "itemID": 0})
d4 = fs({"cmd": "request.get",
         "url": "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo?" + qs,
         "maxTimeout": 60000,
         "session": SESSION,
         "cookies": cookies,
         "headers": [{"name": "Accept", "value": "application/json, text/javascript, */*"}]})
resp4 = d4.get("solution", {}).get("response", "")
print("Len: {}, First 500: {}".format(len(resp4), resp4[:500].replace("\n", " ")), flush=True)

# Step 5: GET .asmx?op=GetHistoricalSalesInfo (SOAP doc page)
print("\n=== GET .asmx?op=GetHistoricalSalesInfo with cookies ===", flush=True)
d5 = fs({"cmd": "request.get",
         "url": "https://www.comc.com/CardPopupService.asmx?op=GetHistoricalSalesInfo",
         "maxTimeout": 60000,
         "session": SESSION,
         "cookies": cookies})
resp5 = d5.get("solution", {}).get("response", "")
print("Len: {}, First 800: {}".format(len(resp5), resp5[:800].replace("\n", " ")), flush=True)

print("\n=== DONE ===", flush=True)
