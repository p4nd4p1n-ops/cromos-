#!/usr/bin/env python3
"""Use existing pincomc4 session which might have a logged-in AuthCookie."""
import json, urllib.request, re, time

FS = "http://127.0.0.1:8191/v1"
def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout+10).read())
    except urllib.error.HTTPError as e:
        return {"solution": {"status": e.code, "response": e.read().decode("utf-8","replace"), "cookies": []}}
    except Exception as e:
        return {"solution": {"status": -1, "response": str(e), "cookies": []}}

SESSIONS = ["pincomc4", "pincomc", "kobe2118", "kobe4141", "kobe5392", "kobe9858"]
CARD_URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"

for sess in SESSIONS:
    print("\n=== Testing session: {} ===".format(sess), flush=True)
    
    # Get session cookies
    try:
        cookies_req = fs({"cmd": "request.get", "url": CARD_URL, "maxTimeout": 60000, "session": sess, "returnCookies": True})
    except Exception as e:
        print("  ERROR loading page: {}".format(str(e)[:100]), flush=True)
        continue
    
    cookies = cookies_req.get("solution", {}).get("cookies", [])
    html = cookies_req.get("solution", {}).get("response", "")
    
    print("  HTML len: {}, cookies: {}".format(len(html), len(cookies)), flush=True)
    
    # Check for auth
    auth_found = False
    for c in cookies:
        n = c.get("name","")
        if n == "AuthCookie":
            auth_found = True
            print("  AuthCookie: {}...".format(str(c.get("value",""))[:50]), flush=True)
        if n in ("__AntiXsrfToken", "ASP.NET_SessionId"):
            print("  {}: {}...".format(n, str(c.get("value",""))[:30]), flush=True)
    
    # Check if logged in
    logged_in = bool(re.search(r'Sign\s*Out|Log\s*Out|My\s+Account|Welcome', html, re.I))
    print("  Logged in: {}, AuthCookie: {}".format(logged_in, auth_found), flush=True)
    
    # Check for "View Chart" vs actual sparkline data
    view_chart = re.search(r'View Chart', html)
    sparkline_data = re.findall(r'sparkline[^"]*"[^"]*"', html[:50000])
    print("  Has 'View Chart' link: {}".format(bool(view_chart)), flush=True)
    print("  Sparkline refs: {}".format(len(sparkline_data)), flush=True)
    
    if logged_in:
        # Look for sales data in HTML
        for pat in [r'(?:sales|chart|history|quarterly)[^<]*data[^<]*<[^>]*>([^<]+)',
                     r'historicalSaleInfo[^<]*',
                     r'salesCount[^<]*',
                     r'totalSales[^<]*']:
            for m in re.finditer(pat, html, re.I):
                print("  FOUND: {}".format(m.group()[:100]), flush=True)
        
        # If logged in, try the AJAX call
        print("  Trying AJAX with this session's cookies...", flush=True)
        body = json.dumps({"sourceElement": "hp31038639_0_", "productKey": "31038639 0 ", "itemID": 0})
        d2 = fs({"cmd": "request.post",
                 "url": "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo",
                 "maxTimeout": 60000,
                 "session": sess,
                 "postData": body,
                 "cookies": cookies,
                 "headers": [{"name": "Content-Type", "value": "application/json; charset=utf-8"}]})
        resp2 = d2.get("solution", {}).get("response", "")
        if resp2.strip().startswith("{"):
            print("  AJAX SUCCESS! Data: {}".format(resp2[:500]), flush=True)
        else:
            title_m = re.search(r'<title>([^<]+)</title>', resp2, re.I)
            print("  AJAX response: {}".format(title_m.group(1).strip() if title_m else "no title"), flush=True)
    
    time.sleep(2)

# Also try: Get the full detail page for the card and look for embedded JSON data
print("\n=== Checking for embedded sales data on card page ===", flush=True)
d = fs({"cmd": "request.get", "url": CARD_URL, "maxTimeout": 90000, "session": "datacheck"})
html = d.get("solution", {}).get("response", "")

# Search for any JSON-like data structures containing sales info
for m in re.finditer(r'(?:sales|history|chart|price)[^"]*', html[:80000], re.I):
    if len(m.group()) > 30:
        nearby = html[max(0,m.start()-100):m.end()+300]
        # Look for JSON objects nearby
        json_match = re.search(r'\{[^}]+(?:price|sale|date|amount)[^}]+\}', nearby, re.I)
        if json_match:
            print("Potential data near '{}': {}".format(m.group()[:60], json_match.group()[:200]), flush=True)

# Also: search for "sales-count" or similar
for m in re.finditer(r'sales-count[^>]*>([^<]+)', html, re.I):
    print("Sales count: {}".format(m.group(1).strip()), flush=True)

print("\n=== DONE ===", flush=True)
