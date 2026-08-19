#!/usr/bin/env python3
"""Fecha release 2026-27 Topps Chrome Basketball — DDG SIN cookies de COMC."""
import json, urllib.request, re, html as h, urllib.parse

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get(url, session="q"):
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": session})
    return d.get("solution", {}).get("response", "")

queries = [
    "2026-27 Topps Chrome Basketball release date",
    "Topps Chrome Basketball 2026-27 checklist release",
]
for q in queries:
    print(f"=== {q} ===")
    try:
        html = get("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q))
        found = 0
        for m in re.finditer(r'result__a[^>]*>(.*?)</a>.*?result__snippet[^>]*>(.*?)</a>', html, re.S):
            t = re.sub(r"<[^>]+>", "", m.group(1) + " || " + m.group(2))
            t = re.sub(r"\s+", " ", h.unescape(t))
            print("*", t[:280])
            found += 1
            if found >= 6:
                break
        if not found:
            print("sin resultados; raw:", len(html))
    except Exception as e:
        print("error:", str(e)[:120])
    print()
