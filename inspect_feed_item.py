#!/usr/bin/env python3
"""Compara el XML crudo de un item SUBATA vs un item BUYNOW en SearchFeed.
11/08/2026 — para encontrar la etiqueta que distingue subasta de compra directa.
"""
import json, urllib.request, re, sys

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def feed(url, etiqueta):
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "ghost"})
    h = d.get("solution", {}).get("response", "")
    items = re.findall(r"<item>(.*?)</item>", h, re.S)
    print(f"===== {etiqueta} — {len(items)} items =====")
    for it in items[:4]:
        t = re.search(r"<title>(.*?)</title>", it, re.S)
        print(f"--- ITEM: {(t.group(1).strip()[:70] if t else '?')}")
        print(it[:2500])
        print()

# 1) La Purple Shock (SUBATA segun Pin) — buscar por nombre exacto
feed("https://www.comc.com/SearchFeed.aspx?SportID=2&PageSize=20&Search=%22Purple+Shock+Prizm%22+%22Jayden+Daniels%22", "PURPLE SHOCK (SUBASTA)")
