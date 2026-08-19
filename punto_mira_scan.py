#!/usr/bin/env python3
"""punto_mira_scan.py — escanea SOLO las 6 cartas de la pestaña Punto de mira.
Output JSON a stdout, una entrada por carta.
"""
import json, urllib.request, re, time, random, datetime, os

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

CARTAS = [
    ("Dylan Harper", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"),
    ("VJ Edgecombe", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2531/VJ_Edgecombe/31038640"),
    ("Kon Knueppel", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2541/Kon_Knueppel/31038641"),
    ("Hugo Gonzalez", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2781/Hugo_Gonzalez/31038666"),
    ("Victor Wembanyama", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038608"),
]

BLOCK_INDICATORS = ["access denied", "captcha", "please verify", "unusual traffic", "sign in to continue"]

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get_html(url, session="ghost", retries=3):
    for i in range(retries):
        try:
            d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": session, "cookies": COOKIES})
            hh = d.get("solution", {}).get("response", "")
            if hh and "Just a moment" not in hh and len(hh) > 5000:
                return hh
        except Exception:
            pass
        time.sleep(10 * (i + 1))
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
    # TOTAL HISTÓRICO: span tras el sparkline (id="..._sparkline_sparkline")
    m2 = re.search(r'sparkline_sparkline"[^>]*>.*?</span>\s*<span>(\d+)</span>', html, re.S)
    if m2:
        out["total_hist"] = int(m2.group(1))
    # SERIE TRIMESTRAL: datos del sparkline (16 trimestres = 4 años)
    m3 = re.search(r'sparkline\(\[([0-9,\s]+)\]', html)
    if m3:
        out["quarterly"] = [int(x) for x in m3.group(1).split(",") if x.strip()]
        if "total_hist" not in out:
            out["total_hist"] = sum(out["quarterly"])
    return out

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

def main():
    try:
        fs({"cmd": "sessions.destroy", "session": "ghost"}, timeout=30000)
    except Exception:
        pass
    time.sleep(2)
    hoy = datetime.date.today().isoformat()
    for nombre, url in CARTAS:
        html = get_html(url)
        if not html:
            print(json.dumps({"nombre": nombre, "fecha": hoy, "error": "sin_html"}, ensure_ascii=False), flush=True)
            continue
        blk = check_blocked(html)
        if blk:
            print(json.dumps({"nombre": nombre, "fecha": hoy, "error": "BLOQUEO:" + blk}, ensure_ascii=False), flush=True)
            continue
        d = parse_card(html)
        v7, vel, dias, turn, dias_distintos = calc_liquidez(d.get("copias", 0), d.get("sales", []))
        r = {"nombre": nombre, "fecha": hoy,
             "min": d.get("min"), "seg": d.get("seg"), "gap": d.get("gap"),
             "copias": d.get("copias"), "n_min": d.get("n_min"), "n_cerca": d.get("n_cerca"),
             "ventas_7d": v7, "vel_dia": vel, "dias_inv": dias, "turnover": turn,
             "total_hist": d.get("total_hist"), "dias_venta_7d": dias_distintos,
             "quarterly": d.get("quarterly"),
             "sales": d.get("sales", [])[:20]}
        print(json.dumps(r, ensure_ascii=False), flush=True)
        time.sleep(random.uniform(6, 15))

if __name__ == "__main__":
    main()
