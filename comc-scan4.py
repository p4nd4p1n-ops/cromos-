#!/usr/bin/env python3
"""Escáner COMC v4 — 10 rookies Chrome Base: min, 2º, gap%, liquidez (total listados, copias al min).
Uso: comc-scan4.py <topN|all>
"""
import json, sys, urllib.request, re, html as h, time

FS = "http://127.0.0.1:8191/v1"

# (nombre, numero, cardId_guess, base_url)
CARDS = [
    ("Cooper Flagg", 251, 31038638, "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2511/Cooper_Flagg"),
    ("Dylan Harper", 252, 31038639, "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper"),
    ("VJ Edgecombe", 253, 31038640, "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2531/VJ_Edgecombe"),
    ("Kon Knueppel", 254, 31038641, "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2541/Kon_Knueppel"),
    ("Ace Bailey", 255, 31038642, "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2551/Ace_Bailey"),
    ("Khaman Maluach", 260, 31038648, "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2601/Khaman_Maluach"),
    ("Noa Essengue", 262, 31038650, "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2621/Noa_Essengue"),
    ("Derik Queen", 263, 31038651, "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2631/Derik_Queen"),
    ("Walter Clayton Jr.", 268, 31038656, "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2681/Walter_Clayton_Jr."),
    ("Will Riley", 271, 31038659, "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2711/Will_Riley"),
]

def fs_get(url, timeout=60000, retries=3):
    last = None
    for i in range(retries):
        try:
            body = json.dumps({"cmd": "request.get", "url": url, "maxTimeout": timeout}).encode()
            req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
            return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())
        except Exception as e:
            last = e
            time.sleep(5 * (i + 1))
    raise last

def get_pages(base_url, card_id):
    htmls = []
    try:
        d = fs_get(f"{base_url}/{card_id}")
    except Exception as e:
        return None, f"error_p1: {str(e)[:60]}"
    h1 = d.get("solution", {}).get("response", "")
    if "Just a moment" in h1:
        return None, "challenge"
    htmls.append(h1)
    m = re.search(r"Page\s+1\s+of\s+(\d+)", h1, re.I)
    total = int(m.group(1)) if m else 1
    for p in range(2, min(total, 15) + 1):
        try:
            d = fs_get(f"{base_url}/{card_id},p{p}")
            hp = d.get("solution", {}).get("response", "")
            if "Just a moment" not in hp:
                htmls.append(hp)
        except Exception:
            pass
        time.sleep(1.5)
    return htmls, None

def parse_items(htmls):
    items = []
    for t in htmls:
        for m in re.finditer(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', t):
            items.append(float(m.group(2).replace(",", "")))
    return items

def parse_title(htmls):
    for t in htmls:
        m = re.search(r"<title>([^<]+)</title>", t)
        if m:
            return m.group(1).strip()
    return "?"

def scan(name, num, cid, base_url):
    htmls, err = get_pages(base_url, cid)
    if err:
        return {"nombre": name, "num": num, "error": err}
    title = parse_title(htmls)
    prices = sorted(parse_items(htmls))
    out = {"nombre": name, "num": num, "title": title[:60], "total": len(prices)}
    if len(prices) >= 2:
        c1, c2 = prices[0], prices[1]
        out["min"] = c1
        out["seg"] = c2
        out["gap"] = round((c2 - c1) / c2 * 100, 1)
        out["n_min"] = prices.count(c1)
        out["pct_min"] = round(prices.count(c1) / len(prices) * 100, 1)
        # liquidez: listados en rango +10% del min
        out["n_cerca"] = sum(1 for p in prices if p <= c1 * 1.10)
    elif prices:
        out["min"] = prices[0]
        out["n_min"] = prices.count(prices[0])
    return out

def main():
    top = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else len(CARDS)
    rows = []
    for name, num, cid, url in CARDS[:top]:
        r = scan(name, num, cid, url)
        rows.append(r)
        time.sleep(2)
        print(json.dumps(r, ensure_ascii=False), flush=True)
    print("=== CSV ===")
    print("nombre;num;min;seg;gap%;total;n_min;pct_min;n_cerca")
    for r in rows:
        if "error" in r:
            print(f"{r['nombre']};{r['num']};ERROR:{r['error']}")
        else:
            print(f"{r['nombre']};{r['num']};{r.get('min','')};{r.get('seg','')};{r.get('gap','')};{r.get('total','')};{r.get('n_min','')};{r.get('pct_min','')};{r.get('n_cerca','')}")

if __name__ == "__main__":
    main()
