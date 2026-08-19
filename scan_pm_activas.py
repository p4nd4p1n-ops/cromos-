#!/usr/bin/env python3
"""scan_pm_activas.py — scan fino de las cartas ACTIVAS del punto de mira (12/08/2026).
Mismo motor que muro_fino_inventario.py: sleeps largos + BuyItNow del 1er escalón (L-022).
Guarda: /root/comc-data/pm-activas-<timestamp>.json + pm-activas-ultimo.json
"""
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
    ("Harper Bowman Univ BUC24-22-B", "https://www.comc.com/Cards/Basketball/2024-25/Bowman_University_Chrome_-_Base/22/Dylan_Harper/28629778"),
    ("Wemby Chrome TC25-2211-B", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038608"),
    ("Flagg Topps T25-201-B", "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/201/Cooper_Flagg/30579235"),
    ("Flagg Living TLS25-11-B", "https://www.comc.com/Cards/Basketball/2025-26/Topps_NBA_Living_Set_-_Online_Exclusive_Base/11/Cooper_Flagg/31620410"),
    ("Knueppel Topps T25-204-B", "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/204/Kon_Knueppel/30579238"),
]

BLOCK_INDICATORS = ["access denied", "captcha", "please verify", "unusual traffic", "sign in to continue"]
DATA_DIR = "/root/comc-data"

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

def check_blocked(html):
    low = html.lower()
    for ind in BLOCK_INDICATORS:
        if ind in low:
            return ind
    return None

def parse_card(html):
    items = sorted(float(m.group(2).replace(",", "")) for m in re.finditer(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', html))
    out = {"total_items": len(items)}
    if len(items) >= 2:
        c1, c2 = items[0], items[1]
        out.update(min=c1, seg=c2, gap=round((c2 - c1) / c2 * 100, 1),
                   n_min=items.count(c1), n_cerca=sum(1 for p in items if p <= c1 * 1.10))
    elif items:
        out.update(min=items[0], n_min=items.count(items[0]))
    m = re.search(r'class="allsellers"[^>]*>.*?qtyforsale[^>]*>\s*&nbsp;?\((\d+)\)', html, re.S)
    if not m:
        m = re.search(r"All Sellers.*?qtyforsale.*?\((\d+)\)", html, re.S)
    out["copias"] = int(m.group(1)) if m else out.get("total_items", 0)
    out["sales"] = [(f, float(p)) for f, p in re.findall(
        r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)]
    m2 = re.search(r'sparkline_sparkline"[^>]*>.*?</span>\s*<span>(\d+)</span>', html, re.S)
    if m2:
        out["total_hist"] = int(m2.group(1))
    m3 = re.search(r'sparkline\(\[([0-9,\s]+)\]', html)
    if m3:
        out["quarterly"] = [int(x) for x in m3.group(1).split(",") if x.strip()]
        if "total_hist" not in out:
            out["total_hist"] = sum(out["quarterly"])
    return out

def parse_muro(html):
    items = re.findall(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', html)
    owners = {}
    for m in re.finditer(r'Owner: <strong><a href="/Users/([^"]+)"[^>]*>([^<]+)</a></strong>.*?Item: (\d+)', html, re.S):
        owners[m.group(3)] = m.group(2)
    muro = []
    for item_id, precio_txt in items:
        muro.append({"item_id": item_id, "precio": float(precio_txt.replace(",", "")),
                     "owner": owners.get(item_id, "?")})
    muro.sort(key=lambda x: x["precio"])
    return muro

def es_buynow(vendedor, card_path):
    url = f"https://www.comc.com/Users/{vendedor}/Cards/{card_path}"
    html = get_html(url)
    if not html:
        return None
    tiene_bin = bool(re.search(r"BuyItNow|buyitnow", html))
    tiene_cart = bool(re.search(r"Add to Cart", html))
    return bool(tiene_bin and tiene_cart)

def resumir_muro(muro):
    resumen = {}
    for m in muro:
        p = m["precio"]
        e = resumen.setdefault(p, {"copias": 0, "owners": []})
        e["copias"] += 1
        if m["owner"] not in e["owners"]:
            e["owners"].append(m["owner"])
    for e in resumen.values():
        e["mismo_owner"] = len(e["owners"]) == 1
    return resumen

def calc_liquidez(copias, sales):
    hoy = datetime.date.today()
    ventas_7d = 0
    dias_con_venta = set()
    for fstr, _ in sales:
        try:
            fecha = datetime.datetime.strptime(fstr, "%b %d, %Y").date()
            if (hoy - fecha).days <= 7:
                ventas_7d += 1
                dias_con_venta.add(fecha.isoformat())
        except ValueError:
            pass
    vel = ventas_7d / 7.0
    dias = round(copias / vel, 1) if vel > 0 else None
    turn = round(ventas_7d / copias * 100, 1) if copias else None
    return ventas_7d, round(vel, 3), dias, turn, len(dias_con_venta)

def escanear_carta(nombre, url):
    html = get_html(url)
    if not html:
        return {"carta": nombre, "error": "sin_html"}
    blk = check_blocked(html)
    if blk:
        return {"carta": nombre, "error": "BLOQUEO:" + blk}
    d = parse_card(html)
    v7, vel, dias, turn, dias_distintos = calc_liquidez(d.get("copias", 0), d.get("sales", []))
    muro_items = parse_muro(html)
    resumen = resumir_muro(muro_items)

    primer = next((m for m in muro_items if m["owner"] != "pinchonauta"), None)
    bn = None
    if primer:
        cm = re.search(r"/Cards/(.+?)(?:/Graded|$)", url)
        if cm:
            time.sleep(random.uniform(15, 25))
            bn = es_buynow(primer["owner"], cm.group(1))
            if bn is None:
                time.sleep(random.uniform(20, 30))
                bn = es_buynow(primer["owner"], cm.group(1))
        primer["buynow"] = bn
        marca = {True: "[BN]", False: "[SUB]", None: "[?]"}[bn]
        if primer["precio"] in resumen:
            resumen[primer["precio"]]["bn"] = marca

    muro_txt = "; ".join(f"{p}: {e['copias']} ({'/'.join(e['owners'])}{e.get('bn','')})" for p, e in sorted(resumen.items()))
    return {"carta": nombre, "url": url,
            "min": d.get("min"), "seg": d.get("seg"), "gap": d.get("gap"),
            "copias": d.get("copias"), "n_min": d.get("n_min"), "n_cerca": d.get("n_cerca"),
            "ventas_7d": v7, "vel_dia": vel, "dias_inv": dias, "turnover": turn,
            "total_hist": d.get("total_hist"), "dias_venta_7d": dias_distintos,
            "primer_escalon": {"precio": primer["precio"], "vendedor": primer["owner"], "buynow": bn} if primer else None,
            "muro": resumen, "muro_txt": muro_txt[:700], "muro_items": muro_items}

def main():
    try:
        fs({"cmd": "sessions.destroy", "session": "ghost"}, timeout=30000)
    except Exception:
        pass
    time.sleep(3 + random.uniform(0, 10))

    resultados = {"fecha": datetime.datetime.now().strftime("%Y%m%d-%H%M%S"), "tipo": "pm-activas", "cartas": []}
    fallidas = []
    for nombre, url in CARTAS:
        r = escanear_carta(nombre, url)
        resultados["cartas"].append(r)
        if "error" in r:
            fallidas.append((nombre, url))
            print(json.dumps({"carta": nombre, "error": r["error"]}, ensure_ascii=False), flush=True)
        else:
            print(json.dumps({"carta": nombre, "min": r["min"], "seg": r["seg"], "gap": r["gap"],
                              "copias": r["copias"], "v7d": r["ventas_7d"], "vel": r["vel_dia"],
                              "1er": r.get("primer_escalon")}, ensure_ascii=False), flush=True)
        time.sleep(random.uniform(25, 45))

    if fallidas:
        print(json.dumps({"reintento": [f[0] for f in fallidas]}, ensure_ascii=False), flush=True)
        time.sleep(90 + random.uniform(0, 60))
        for i, (nombre, url) in enumerate(fallidas):
            r = escanear_carta(nombre, url)
            for j, e in enumerate(resultados["cartas"]):
                if e.get("carta") == nombre:
                    resultados["cartas"][j] = r
                    break
            if "error" in r:
                print(json.dumps({"carta": nombre, "error2": r["error"]}, ensure_ascii=False), flush=True)
            else:
                print(json.dumps({"carta": nombre, "RECUPERADA": True, "min": r["min"]}, ensure_ascii=False), flush=True)
            time.sleep(random.uniform(40, 60))

    out = f"{DATA_DIR}/pm-activas-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    json.dump(resultados, open(out, "w"), ensure_ascii=False, indent=1)
    print("GUARDADO " + out, flush=True)
    json.dump(resultados, open(f"{DATA_DIR}/pm-activas-ultimo.json", "w"), ensure_ascii=False, indent=1)
    ok = sum(1 for c in resultados["cartas"] if "error" not in c)
    print(json.dumps({"resumen": f"{ok}/{len(resultados['cartas'])} cartas OK"}, ensure_ascii=False), flush=True)
    print("OK", flush=True)

if __name__ == "__main__":
    main()
