#!/usr/bin/env python3
"""Escáner COMC v6 — LOS 50 RC del set (lista de Pin): resuelve cardId base por jugador y escanea.
Uso: comc-scan6.py [inicio] [fin]
"""
import json, sys, urllib.request, re, time

FS = "http://127.0.0.1:8191/v1"

AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

# (nombre, playerId) — lista de Pin (RC del set)
PLAYERS = [
    ("Kon Knueppel", "c469745"), ("Cooper Flagg", "c465571"), ("Derik Queen", "c469128"),
    ("VJ Edgecombe", "c467242"), ("Cedric Coward", "c491823"), ("Noa Essengue", "c495117"),
    ("Ace Bailey", "c469725"), ("Jeremiah Fears", "c491773"), ("Tyrese Proctor", "c420694"),
    ("Dylan Harper", "c421184"), ("Tre Johnson", "c433088"), ("Alijah Martin", "c436911"),
    ("Rocco Zikarsky", "c446060"), ("Walter Clayton Jr.", "c484938"), ("Kasparas Jakucionis", "c487680"),
    ("Yang Hansen", "c491759"), ("Will Riley", "c491761"), ("Nique Clifford", "c491762"),
    ("Rasheer Fleming", "c491826"), ("Noah Penda", "c494758"), ("Ben Saraf", "c495084"),
    ("Danny Wolf", "c495086"), ("Jamir Watkins", "c495116"), ("Javon Small", "c499958"),
    ("Micah Peavy", "c396353"), ("Johni Broome", "c436873"), ("Ryan Kalkbrenner", "c436885"),
    ("Alex Toohey", "c446055"), ("Brooks Barnhizer", "c455179"), ("Carter Bryant", "c467241"),
    ("Khaman Maluach", "c467251"), ("Liam McNeeley", "c469126"), ("Drake Powell", "c469127"),
    ("Kam Jones", "c469358"), ("Asa Newell", "c469744"), ("Nolan Traore", "c478773"),
    ("Sion James", "c478777"), ("Koby Brea", "c491671"), ("Chaz Lanier", "c491824"),
    ("Maxime Raynaud", "c491825"), ("Will Richard", "c492151"), ("Hugo Gonzalez", "c493645"),
    ("Jase Richardson", "c494757"), ("Joan Beringer", "c494974"), ("Adou Thiero", "c495085"),
    ("Collin Murray-Boyles", "c495115"), ("Egor Demin", "c495118"), ("Thomas Sorber", "c495119"),
    ("Yanic Konan-Niederhauser", "c495120"), ("Amari Williams", "c499959"),
]

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def slug(nombre):
    return nombre.replace(" ", "_").replace("_Jr.", "_Jr.").replace(".", "_")

def get_html(url, session="ghost"):
    d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": session, "cookies": COOKIES})
    return d.get("solution", {}).get("response", "")

def resolve_base_card(nombre, player_id):
    """Fetch página de jugador → cardId de la carta BASE (#XXX.1, sin SP/Graded)."""
    url = f"https://www.comc.com/Players/Basketball/{nombre.replace(' ', '_')}/{player_id}/Cards/Basketball/2025-26/Topps_Chrome_-_Base,sh,_RC,i100"
    html = get_html(url)
    if "Just a moment" in html:
        return None, "challenge"
    # base = /Cards/.../{n}1/{nombre}/{cardId} (sin /Graded/ y sin SP_Image_Variation)
    pat = re.compile(r'href="(/Cards/Basketball/2025-26/Topps_Chrome_-_Base/(\d+)1/[^"/]+/(\d+))"')
    cands = []
    for full, num, cid in pat.findall(html):
        if "SP" not in full and "Graded" not in full:
            cands.append((int(num), cid, full))
    if not cands:
        return None, "sin_base"
    cands.sort()
    return cands[0][1], cands[0][2]

def scan_card(card_id, base_path, nombre, session="ghost"):
    base_url = "https://www.comc.com" + base_path
    htmls = []
    h1 = get_html(base_url, session)
    if "Just a moment" in h1:
        return {"nombre": nombre, "error": "challenge"}
    htmls.append(h1)
    m = re.search(r"Page\s+1\s+of\s+(\d+)", h1, re.I)
    total = int(m.group(1)) if m else 1
    for p in range(2, min(total, 15) + 1):
        try:
            hp = get_html(f"{base_url},p{p}", session)
            if "Just a moment" not in hp:
                htmls.append(hp)
        except Exception:
            pass
        time.sleep(1.5)
    prices = []
    for t in htmls:
        for mm in re.finditer(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', t):
            prices.append(float(mm.group(2).replace(",", "")))
    prices.sort()
    out = {"nombre": nombre, "cardId": card_id, "total": len(prices)}
    if len(prices) >= 2:
        c1, c2 = prices[0], prices[1]
        out.update(min=c1, seg=c2, gap=round((c2 - c1) / c2 * 100, 1),
                   n_min=prices.count(c1), pct_min=round(prices.count(c1) / len(prices) * 100, 1),
                   n_cerca=sum(1 for p in prices if p <= c1 * 1.10))
    elif prices:
        out.update(min=prices[0], n_min=prices.count(prices[0]))
    return out

def main():
    a = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    b = int(sys.argv[2]) if len(sys.argv) > 2 else len(PLAYERS)
    rows = []
    for nombre, pid in PLAYERS[a:b]:
        cid, path = resolve_base_card(nombre, pid)
        if not cid:
            print(json.dumps({"nombre": nombre, "error": path}, ensure_ascii=False), flush=True)
            continue
        r = scan_card(cid, path, nombre)
        r["num"] = re.search(r"/(\d+)1/", path).group(1) if re.search(r"/(\d+)1/", path) else ""
        rows.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)
        time.sleep(2)
    print("=== CSV ===")
    print("nombre;num;cardId;min;seg;gap%;total;n_min;pct_min;n_cerca")
    for r in rows:
        if "error" in r:
            print(f"{r['nombre']};{r.get('num','')};{r.get('cardId','')};ERROR:{r['error']}")
        else:
            print(f"{r['nombre']};{r['num']};{r['cardId']};{r.get('min','')};{r.get('seg','')};{r.get('gap','')};{r.get('total','')};{r.get('n_min','')};{r.get('pct_min','')};{r.get('n_cerca','')}")

if __name__ == "__main__":
    main()
