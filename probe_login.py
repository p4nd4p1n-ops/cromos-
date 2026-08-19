#!/usr/bin/env python3
"""Login to COMC via FlareSolverr, capture AuthCookie, then call GetHistoricalSalesInfo."""
import json, urllib.request, re, time, urllib.parse

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 10).read())

SESSION = "loginprobe"
LOGIN_URL = "https://www.comc.com/Account/Login"
CARD_URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"

# Credentials from previous attempts
USER = "dragon941"
PASS = "passkobe1234+"

# Clean up
try:
    fs({"cmd": "sessions.destroy", "session": SESSION}, timeout=30000)
except:
    pass
time.sleep(1)

# Step 1: Load login page to get __RequestVerificationToken and cookies
print("=== STEP 1: Load login page ===", flush=True)
d = fs({"cmd": "request.get", "url": LOGIN_URL, "maxTimeout": 90000, "session": SESSION})
html = d.get("solution", {}).get("response", "")
cookies = d.get("solution", {}).get("cookies", [])
print("HTML len: {}, cookies: {}".format(len(html), len(cookies)), flush=True)

# Extract __RequestVerificationToken
token_m = re.search(r'<input[^>]*name="__RequestVerificationToken"[^>]*value="([^"]*)"', html)
token = token_m.group(1) if token_m else None
print("Token: {}".format(token[:40] if token else "NOT FOUND"), flush=True)

# Also check if there's a returnUrl hidden field
for m in re.finditer(r'name="([^"]*)"[^>]*value="([^"]*)"', html):
    name = m.group(1)
    if "return" in name.lower() or "token" in name.lower():
        print("  Hidden field: {} = {}...".format(name, m.group(2)[:40]), flush=True)

# Step 2: Submit login form
print("\n=== STEP 2: Submit login ===", flush=True)

# Build form data
form_data = {
    "UserName": USER,
    "Password": PASS,
    "RememberMe": "false",
}
if token:
    form_data["__RequestVerificationToken"] = token

# Encode as URL-encoded
form_body = urllib.parse.urlencode(form_data)

r2 = fs({
    "cmd": "request.post",
    "url": LOGIN_URL,
    "maxTimeout": 90000,
    "session": SESSION,
    "postData": form_body,
    "cookies": cookies,
    "headers": [
        {"name": "Content-Type", "value": "application/x-www-form-urlencoded"},
        {"name": "Referer", "value": LOGIN_URL},
        {"name": "Origin", "value": "https://www.comc.com"},
    ]
})

resp = r2.get("solution", {}).get("response", "")
status = r2.get("solution", {}).get("status", "?")
new_cookies = r2.get("solution", {}).get("cookies", [])

print("Status: {}, response len: {}".format(status, len(resp)), flush=True)

# Check for AuthCookie
auth_found = False
for c in new_cookies:
    print("  Cookie: {} = {}...".format(c.get("name"), str(c.get("value", ""))[:50]), flush=True)
    if c.get("name") == "AuthCookie":
        auth_found = True

# Check if login succeeded (look for "Sign Out" or "Log Out" or redirect)
logged_in = bool(re.search(r'Sign\s*Out|Log\s*Out|Welcome|My\s+Account', resp, re.I))
redirected = status in [301, 302, 303]
title_m = re.search(r'<title>([^<]*)</title>', resp, re.I)
print("Title: {}".format(title_m.group(1).strip() if title_m else "N/A"), flush=True)
print("Logged in: {}, Redirected: {}, AuthCookie: {}".format(logged_in, redirected, auth_found), flush=True)

# Check for error messages
for m in re.finditer(r'(?:error|validation|incorrect|invalid)[^<>]*<[^>]*>([^<]{10,200})', resp, re.I):
    print("  Error msg: {}".format(m.group(1)), flush=True)

# Save response for inspection
open("/root/comc-data/login-response.html", "w").write(resp)
print("\nSaved to /root/comc-data/login-response.html", flush=True)

# Step 3: If we got auth, try the AJAX call
if auth_found:
    print("\n=== STEP 3: Try AJAX with fresh AuthCookie ===", flush=True)
    body = json.dumps({"sourceElement": "hp31038639_0_", "productKey": "31038639 0 ", "itemID": 0})
    r3 = fs({
        "cmd": "request.post",
        "url": "https://www.comc.com/CardPopupService.asmx/GetHistoricalSalesInfo",
        "maxTimeout": 60000,
        "session": SESSION,
        "postData": body,
        "cookies": new_cookies,
        "headers": [
            {"name": "Content-Type", "value": "application/json; charset=utf-8"},
            {"name": "X-Requested-With", "value": "XMLHttpRequest"},
        ]
    })
    resp3 = r3.get("solution", {}).get("response", "")
    print("AJAX response len: {}".format(len(resp3)), flush=True)
    if resp3.strip().startswith("{"):
        print("SUCCESS! JSON: {}".format(resp3[:2000]), flush=True)
    else:
        title_m3 = re.search(r'<title>([^<]*)</title>', resp3, re.I)
        print("Title: {}".format(title_m3.group(1).strip() if title_m3 else "N/A"), flush=True)
        print("First 400: {}".format(resp3[:400].replace("\n", " ")), flush=True)
else:
    print("\n=== No AuthCookie obtained ===", flush=True)
    # Check for a redirect URL
    url_m = re.search(r'window\.location\s*=\s*"([^"]*)"', resp)
    if url_m:
        print("Redirect found: {}".format(url_m.group(1)), flush=True)

print("\n=== DONE ===", flush=True)
