#!/usr/bin/env python3
"""Extraer URL real de la página 'Get Suggested Prices' de COMC desde DDG."""
import json, urllib.request, re, urllib.parse

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get(url, session="q"):
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": session})
    return d.get("solution", {}).get("response", "")

html = get("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote("COMC Get Suggested Prices SRP"))
pat = re.compile(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)
for m in pat.findall(html):
    url, titulo = m[0], re.sub(r"<[^>]+>", "", m[1]).strip()
    if "comc.com" in url:
        print("URL:", url)
        print("  título:", titulo[:80])
