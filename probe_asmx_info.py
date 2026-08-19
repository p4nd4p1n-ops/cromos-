#!/usr/bin/env python3
"""Probe the ASMX service homepage and try various POST formats."""
import json, urllib.request

FS = "http://127.0.0.1:8191/v1"
def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout+10).read())

# 1. GET the ASMX service homepage (should show available methods)
d = fs({"cmd": "request.get", 
        "url": "https://www.comc.com/CardPopupService.asmx", 
        "maxTimeout": 60000, "session": "probe_asmx"})
resp = d.get("solution", {}).get("response", "")
print("=== GET CardPopupService.asmx ===")
print(resp[:3000])
print("===")

# 2. Also try the JS proxy
d2 = fs({"cmd": "request.get",
         "url": "https://www.comc.com/CardPopupService.asmx/js",
         "maxTimeout": 60000, "session": "probe_asmx2"})
resp2 = d2.get("solution", {}).get("response", "")
print("=== GET /CardPopupService.asmx/js ===")
print(resp2[:3000])
print("===")

# 3. Try SOAPAction header
d3 = fs({"cmd": "request.get",
         "url": "https://www.comc.com/CardPopupService.asmx?op=GetHistoricalSalesInfo",
         "maxTimeout": 60000, "session": "probe_asmx3"})
resp3 = d3.get("solution", {}).get("response", "")
print("=== GET ?op=GetHistoricalSalesInfo ===")
print(resp3[:3000])
print("===")
