#!/usr/bin/env python3
"""Obtener lista top 50 NBA consensuada (HoopsHype) vía FlareSolverr."""
import json, urllib.request, re, html as h

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get(url, session="q"):
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": session})
    return d.get("solution", {}).get("response", "")

url = "https://hoopshype.com/lists/top-100-nba-players-2025-26/"
html = get(url)
print("len:", len(html))
txt = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
txt = re.sub(r"<style.*?</style>", " ", txt, flags=re.S)
# Patrón HoopsHype: filas con enlace a /player/slug/
slugs = re.findall(r'https://hoopshype\.com/player/([a-z0-9-]+)/', txt)
seen, names = [], []
for s in slugs:
    if s not in seen:
        seen.append(s)
        names.append(s.replace("-", " ").title())
print("nombres únicos:", len(names))
for i, n in enumerate(names[:70], 1):
    print(f"{i:2d}. {n}")
