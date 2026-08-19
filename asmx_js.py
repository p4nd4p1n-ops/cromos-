#!/usr/bin/env python3
"""Obtiene el JS del CardPopupService.asmx/js (proxy de metodos AJAX de COMC).
11/08/2026.
"""
import json, urllib.request, re, sys

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

d = fs({"cmd": "request.get", "url": "https://www.comc.com/CardPopupService.asmx/js", "maxTimeout": 60000})
h = d.get("solution", {}).get("response", "")
print("len:", len(h))
print(h[:3000])
