#!/usr/bin/env python3
"""explora_sci.py — explora sportscardinvestor.com vía FlareSolverr:
saca enlaces a sets de basketball y secciones de navegación."""
import json, urllib.request, re, sys

def fs(url, timeout=60000):
    body = json.dumps({"cmd": "request.get", "url": url, "maxTimeout": timeout}).encode()
    req = urllib.request.Request("http://127.0.0.1:8191/v1", data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30000).read())

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.sportscardinvestor.com/"
    d = fs(url)
    hh = d.get("solution", {}).get("response", "")
    print("HTML len:", len(hh))
    t = re.search(r"<title>(.*?)</title>", hh, re.S)
    print("TITLE:", t.group(1).strip()[:120] if t else "?")
    # enlaces a sets de basketball
    links = set(re.findall(r'href="(/sets/[^"]*basketball[^"]*)"', hh, re.I))
    print("\nSets basketball:", len(links))
    for l in sorted(links)[:20]:
        print("  ", l)
    # secciones de navegación
    nav = sorted(set(re.findall(r'href="(/[a-z0-9-]+/)"', hh)))
    print("\nNav:", nav[:30])

if __name__ == "__main__":
    main()
