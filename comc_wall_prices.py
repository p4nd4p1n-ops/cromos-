#!/usr/bin/env python3
"""
WORKAROUND: Extraer precios del muro como proxy de "comps"

No requiere login ni History Points.
Usa FlareSolverr (127.0.0.1:8191) para cargar la pagina de la carta
y extrae los precios del muro de venta (los "asking prices").

Los precios del muro son asking prices, no precios de venta reales,
pero sirven COMO REFERENCIA de mercado para flipping. El precio mas
bajo del muro ($10.03 en Harper base) es un floor price.

Tambien extrae cuantas copias hay a la venta (liquidez).
"""

import json, urllib.request, re, time, sys

FS = "http://127.0.0.1:8191/v1"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=timeout+10).read())
    except Exception as e:
        return {"solution": {"status": -1, "response": str(e), "cookies": []}}

def scrape_card_wall(card_url, session="comc_wall"):
    """Extrae precios del muro y metadata de la carta."""
    
    # Cargar pagina
    print("Cargando {}...".format(card_url), flush=True)
    try:
        fs({"cmd": "sessions.destroy", "session": session}, timeout=30000)
    except:
        pass
    time.sleep(1)
    
    d = fs({"cmd": "request.get", "url": card_url, "maxTimeout": 120000, "session": session})
    html = d.get("solution", {}).get("response", "")
    if not html or len(html) < 100:
        return {"error": "Pagina no cargada ({} bytes). FlareSolverr caido?".format(len(html))}
    
    result = {}
    
    # Titulo
    title_m = re.search(r'<title>([^<]*)</title>', html)
    if title_m:
        result["title"] = title_m.group(1).strip()
    
    # Precio mas bajo del muro (floor price)
    price_matches = re.findall(r'<a[^>]*onclick="historicalSaleInfo\.get[^"]*"[^>]*>\$([\d.]+)', html)
    if price_matches:
        prices = [float(p) for p in price_matches]
        prices.sort()
        result["wall_prices"] = prices
        result["floor_price"] = min(prices)
        result["median_price"] = prices[len(prices)//2]
        result["num_sellers"] = len(prices)
    
    # Link "4 year sales" (confirma que la pagina cargo bien)
    result["has_sales_link"] = "4 year sales" in html
    
    # Parallels table
    parallels = re.findall(r'<a[^>]*href="[^"]*/\d+/\d+/\d+/\d+/(\d+)"[^>]*class="[^"]*selected[^"]*"[^>]*>.*?<span class="parallelname">([^<]*)</span>.*?<span class="price">\$([\d.]+)</span>.*?\((\d+)\)', html, re.DOTALL)
    if parallels:
        result["parallels"] = []
        for p in parallels:
            result["parallels"].append({
                "id": p[0],
                "name": p[1].strip(),
                "price": float(p[2]),
                "qty": int(p[3])
            })
    
    # Card metadata
    result["card_id_match"] = bool(re.search(r'31038639', html))
    
    return result

if __name__ == "__main__":
    card_url = sys.argv[1] if len(sys.argv) > 1 else \
        "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"
    
    data = scrape_card_wall(card_url)
    print(json.dumps(data, indent=2))
