#!/usr/bin/env python3
"""comc_help_ebay.py — busca en la Zendesk de COMC info sobre comprar en eBay de COMC."""
import json, urllib.request, re, sys

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=90000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def main():
    url = "https://comc.zendesk.com/hc/en-us/search?query=ebay%20buying"
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 60000})
    hh = d.get("solution", {}).get("response", "")
    print("HTML len:", len(hh))
    open("/root/comc-data/comc-help-ebay.html", "w").write(hh)
    # enlaces de artículos
    arts = re.findall(r'href="(/hc/en-us/articles/[^"]+)"[^>]*>([^<]+)', hh)
    seen = set()
    for a, t in arts:
        if a not in seen and len(t.strip()) > 5:
            seen.add(a)
            print(f"  {a} | {t.strip()[:90]}")
    if not arts:
        # extraer texto visible
        txt = re.sub(r"<[^>]+>", " ", hh)
        txt = re.sub(r"\s+", " ", txt)
        print("TEXTO:", txt[:1500])

if __name__ == "__main__":
    main()
