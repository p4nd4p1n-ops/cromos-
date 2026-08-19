#!/usr/bin/env python3
"""probe_ajax5.py — busca la definición del objeto JS historicalSaleInfo en el HTML
de la página (revela la llamada AJAX exacta: endpoint, parámetros, headers)."""
import json, urllib.request, re

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 10).read())

d = fs({"cmd": "request.get",
        "url": "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639",
        "maxTimeout": 90000, "session": "pincomc4"})
html = d.get("solution", {}).get("response", "")
open("/root/comc-data/harper-ajax.html", "w").write(html)

# buscar TODAS las apariciones de historicalSaleInfo con contexto
idx = 0
while True:
    i = html.find("historicalSaleInfo", idx)
    if i < 0:
        break
    ctx = html[max(0, i - 150):i + 350]
    # filtrar las que son solo onclick (ya conocidas)
    if "onclick" not in ctx[:60]:
        print("CTX:", repr(ctx), flush=True)
        print("===", flush=True)
    idx = i + 1

# buscar la definición: "var historicalSaleInfo" o "historicalSaleInfo ="
for m in re.finditer(r"(?:var\s+)?historicalSaleInfo\s*=\s*", html):
    s = m.start()
    print("DEF INI:", repr(html[s:s+600]), flush=True)
    print("---", flush=True)

# buscar en scripts externos que pueda cargar
for m in re.finditer(r'src="([^"]*\.js[^"]*)"', html):
    src = m.group(1)
    if "sale" in src.lower() or "popup" in src.lower() or "card" in src.lower():
        print("JS CANDIDATO:", src, flush=True)
print("FIN", flush=True)
