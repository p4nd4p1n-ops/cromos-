#!/usr/bin/env python3
"""Probe final: fresh session, extract cookies, try ASP.NET AJAX POST correctly."""
import json, urllib.request, re, time, sys

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 10).read())

SESSION = "finalprobe"
CARD_URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"
ENDPOINT = "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo"

# Destroy old session
try:
    fs({"cmd": "sessions.destroy", "session": SESSION}, timeout=30000)
except:
    pass
time.sleep(2)

# Step 1: Load the page to get fresh cookies
print("=== STEP 1: Load card page ===", flush=True)
d = fs({"cmd": "request.get", "url": CARD_URL, "maxTimeout": 90000, "session": SESSION})
html = d.get("solution", {}).get("response", "")
cookies_resp = d.get("solution", {}).get("cookies", [])
print("HTML len: {}, cookies: {}".format(len(html), len(cookies_resp)), flush=True)
for c in cookies_resp:
    print("  Cookie: {}={} domain={} httpOnly={}".format(
        c.get("name"), str(c.get("value",""))[:40], c.get("domain"), c.get("httpOnly")), flush=True)

# Step 2: Try the POST with various parameter combos
print("\n=== STEP 2: Try AJAX POST ===", flush=True)

post_cookies = cookies_resp if cookies_resp else []

bodies_to_try = [
    # a: ASP.NET AJAX standard - all 4 params
    {"sourceElement": "hp31038639_0_", "productKey": "31038639 0 ", "itemID": 0},
    # b: Without sourceElement
    {"productKey": "31038639 0 ", "itemID": 0},
    # c: With returnUrl null
    {"sourceElement": "hp31038639_0_", "productKey": "31038639 0 ", "itemID": 0, "returnUrl": None},
    # d: With returnUrl empty
    {"sourceElement": "hp31038639_0_", "productKey": "31038639 0 ", "itemID": 0, "returnUrl": ""},
    # e: productKey no trailing space
    {"sourceElement": "hp31038639_0_", "productKey": "31038639 0", "itemID": 0},
    # f: Just productKey + itemID
    {"productKey": "31038639 0", "itemID": 0},
    # g: Minimal
    {"productKey": "31038639 0 "},
]

for i, body in enumerate(bodies_to_try):
    body_str = json.dumps(body)
    headers = [
        {"name": "Content-Type", "value": "application/json; charset=utf-8"},
        {"name": "X-Requested-With", "value": "XMLHttpRequest"},
        {"name": "Accept", "value": "application/json, text/javascript, */*; q=0.01"},
        {"name": "Referer", "value": CARD_URL},
    ]

    payload = {
        "cmd": "request.post",
        "url": ENDPOINT,
        "maxTimeout": 60000,
        "session": SESSION,
        "postData": body_str,
        "headers": headers,
        "cookies": post_cookies,
    }

    try:
        r = fs(payload, timeout=90000)
        sol = r.get("solution", {})
        resp = sol.get("response", "")
        status = sol.get("status", "?")
        headers_resp = sol.get("headers", {})
        ct_vals = [h.get("value", "") for h in headers_resp if h.get("name", "").lower() == "content-type"]
        print("\n--- Body[{}] {} --- status={} len={}".format(i, body_str[:80], status, len(resp)), flush=True)
        print("  Content-Type: {}".format(ct_vals), flush=True)
        if resp.strip().startswith("{"):
            print("  JSON: {}".format(resp[:800]), flush=True)
        elif resp.strip().startswith("<"):
            title_m = re.search(r'<title>([^<]*)</title>', resp, re.I)
            print("  HTML title: {}".format(title_m.group(1) if title_m else "N/A"), flush=True)
            print("  First 300: {}".format(resp[:300].replace("\n"," ")), flush=True)
        else:
            print("  Raw: {}".format(resp[:500]), flush=True)
    except Exception as e:
        print("--- Body[{}] ERROR: {} ---".format(i, str(e)[:200]), flush=True)
    time.sleep(3)

print("\n=== DONE ===", flush=True)
