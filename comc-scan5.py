#!/usr/bin/env python3
"""Escáner COMC v5 — CON SESIÓN DE PIN: precios reales (los de la app).
Uso: comc-scan5.py <topN>
"""
import json, sys, urllib.request, re, time
from collections import Counter

FS = "http://127.0.0.1:8191/v1"

AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "cart", "value": "46f37386-b228-462d-88a2-51ec385daabc", "domain": "www.comc.com", "path": "/"},
    {"name": "cartInfo", "value": "3", "domain": "www.comc.com", "path": "/"},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

# (nombre, numero, cardId, base_url)
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

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get_pages(base_url, card_id, session):
    """Todas las páginas de listados de la carta, con cookies de sesión."""
    htmls = []
    d = fs({"cmd": "request.get", "url": f"{base_url}/{card_id}", "maxTimeout": 90000,
            "session": session, "cookies": COOKIES})
    h1 = d.get("solution", {}).get("response", "")
    if "Just a moment" in h1:
        return None, "challenge"
    htmls.append(h1)
    m = re.search(r"Page\s+1\s+of\s+(\d+)", h1, re.I)
    total = int(m.group(1)) if m else 1
    for p in range(2, min(total, 15) + 1):
        try:
            d = fs({"cmd": "request.get", "url": f"{base_url}/{card_id},p{p}", "maxTimeout": 90000,
                    "session": session, "cookies": COOKIES})
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

def scan(name, num, cid, base_url, session):
    htmls, err = get_pages(base_url, cid, session)
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
        out["n_cerca"] = sum(1 for p in prices if p <= c1 * 1.10)
    elif prices:
        out["min"] = prices[0]
        out["n_min"] = prices.count(prices[0])
    return out

def main():
    top = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else len(CARDS)
    session = "pincomc"
    # sesión limpia
    try:
        fs({"cmd": "sessions.destroy", "session": session}, timeout=30000)
    except Exception:
        pass
    rows = []
    for name, num, cid, url in CARDS[:top]:
        r = scan(name, num, cid, url, session)
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
