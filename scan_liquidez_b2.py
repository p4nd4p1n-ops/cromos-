#!/usr/bin/env python3
"""scan_liquidez_b2.py — liquidez de 6 candidatas de colecciones alternativas (12/08 15:30)."""
import json, urllib.request, re, time, random, datetime

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"
COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]
CARTAS = [
    ("Curry Topps #135", "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/135/Stephen_Curry/30579169"),
    ("LeBron Donruss Optic 20-21 #13", "https://www.comc.com/Cards/Basketball/2020-21/Panini_Donruss_Optic_-_Base/13/LeBron_James/17563026"),
    ("Flagg Holiday #H161", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Holiday_-_Base/H161/Cooper_Flagg/30774590"),
    ("Wemby Topps #195", "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/195/Victor_Wembanyama/30579229"),
    ("Bronny Donruss Optic #282", "https://www.comc.com/Cards/Basketball/2024-25/Panini_Donruss_Optic_-_Base/282/Rated_Rookie_-_Bronny_James_Jr/29999249"),
    ("Knueppel Holiday #H164", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Holiday_-_Base/H164/Kon_Knueppel/30774593"),
]
BLOCK = ["access denied", "captcha", "please verify", "unusual traffic", "sign in to continue"]
DATA = "/root/comc-data"

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get_html(url, session="ghost", retries=3, base_wait=20):
    for i in range(retries):
        try:
            d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": session, "cookies": COOKIES})
            hh = d.get("solution", {}).get("response", "")
            if hh and "Just a moment" not in hh and len(hh) > 5000:
                return hh
        except Exception:
            pass
        time.sleep(base_wait * (i + 1) + random.uniform(0, 15))
    return ""

def es_buynow(vendedor, card_path):
    url = f"https://www.comc.com/Users/{vendedor}/Cards/{card_path}"
    html = get_html(url)
    if not html:
        return None
    return bool(re.search(r"BuyItNow|buyitnow", html)) and bool(re.search(r"Add to Cart", html))

def escanear(nombre, url):
    html = get_html(url)
    if not html:
        return {"carta": nombre, "error": "sin_html"}
    low = html.lower()
    for b in BLOCK:
        if b in low:
            return {"carta": nombre, "error": "BLOQUEO:" + b}
    muro_items = []
    for m in re.finditer(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', html):
        muro_items.append({"item_id": m.group(1), "precio": float(m.group(2).replace(",", ""))})
    owners = {}
    for m in re.finditer(r'Owner: <strong><a href="/Users/([^"]+)"[^>]*>([^<]+)</a></strong>.*?Item: (\d+)', html, re.S):
        owners[m.group(3)] = m.group(2)
    for it in muro_items:
        it["owner"] = owners.get(it["item_id"], "?")
    muro_items.sort(key=lambda x: x["precio"])
    resumen = {}
    for it in muro_items:
        p = it["precio"]
        e = resumen.setdefault(p, {"copias": 0, "owners": []})
        e["copias"] += 1
        if it["owner"] not in e["owners"]:
            e["owners"].append(it["owner"])
    sales = [(f, float(p)) for f, p in re.findall(r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)]
    hoy = datetime.date.today()
    v7 = 0
    dias = set()
    for fstr, _ in sales:
        try:
            fecha = datetime.datetime.strptime(fstr, "%b %d, %Y").date()
            if (hoy - fecha).days <= 7:
                v7 += 1
                dias.add(fecha.isoformat())
        except ValueError:
            pass
    primer = next((m for m in muro_items if m["owner"] != "pinchonauta"), None)
    bn = None
    if primer:
        cm = re.search(r"/Cards/(.+?)(?:/Graded|$)", url)
        if cm:
            time.sleep(random.uniform(15, 25))
            bn = es_buynow(primer["owner"], cm.group(1))
        primer["buynow"] = bn
    muro_txt = "; ".join(f"{p}: {e['copias']} ({'/'.join(e['owners'])})" for p, e in sorted(resumen.items()))
    return {"carta": nombre, "min": muro_items[0]["precio"] if muro_items else None,
            "seg": muro_items[1]["precio"] if len(muro_items) > 1 else None,
            "gap": round((muro_items[1]["precio"] - muro_items[0]["precio"]) / muro_items[1]["precio"] * 100, 1) if len(muro_items) > 1 else None,
            "v7d": v7, "dias_venta": len(dias), "vel_dia": round(v7 / 7.0, 3),
            "muro": resumen, "muro_txt": muro_txt[:400],
            "primer": {"precio": primer["precio"], "owner": primer["owner"], "buynow": bn} if primer else None}

def main():
    try:
        fs({"cmd": "sessions.destroy", "session": "ghost"}, timeout=30000)
    except Exception:
        pass
    time.sleep(3 + random.uniform(0, 10))
    out = {"fecha": datetime.datetime.now().strftime("%Y%m%d-%H%M%S"), "tipo": "pm-b2", "cartas": []}
    for nombre, url in CARTAS:
        r = escanear(nombre, url)
        out["cartas"].append(r)
        if "error" in r:
            print(json.dumps({"carta": nombre, "error": r["error"]}, ensure_ascii=False), flush=True)
        else:
            print(json.dumps({"carta": nombre, "min": r["min"], "seg": r["seg"], "gap": r["gap"],
                              "v7d": r["v7d"], "dias": r["dias_venta"], "1er": r["primer"]}, ensure_ascii=False), flush=True)
        time.sleep(random.uniform(25, 45))
    json.dump(out, open(f"{DATA}/pm-b2-{out['fecha']}.json", "w"), ensure_ascii=False, indent=1)
    print("OK", flush=True)

if __name__ == "__main__":
    main()
