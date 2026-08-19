#!/usr/bin/env python3
"""rookies_bb_scan.py — busca los 4 rookies top de MLB 2026 en COMC (feed por jugador).
Espaciado 30-45s anti-rate-limit. Filtro candidata: precio ≤ $5.05, copias ≥ 10.
Guarda snapshots en /root/comc-data/bb-rookies-<ts>/
"""
import json, urllib.request, re, time, random, datetime, os, html as htmllib

FS = "http://127.0.0.1:8191/v1"
AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

JUGADORES = [
    "Kevin McGonigle",
    "JJ Wetherholt",
    "Sal Stewart",
    "Munetaka Murakami",
]

MAX_PRECIO = 5.05
MIN_COPIAS = 10

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get_feed(url, retries=3):
    for i in range(retries):
        try:
            d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "cookies": COOKIES})
            hh = d.get("solution", {}).get("response", "")
            if hh and "Just a moment" not in hh and len(hh) > 2000:
                return hh
        except Exception:
            pass
        time.sleep(15 * (i + 1))
    return ""

def feed_url(jugador):
    import urllib.parse
    return ("https://www.comc.com/SearchFeed.aspx?SportID=0&PageSize=100"
            "&Search=" + urllib.parse.quote(jugador) + "&Sort%3dr")

def parse_feed(hh):
    out = []
    for it in re.findall(r"<item>.*?</item>", hh, re.S):
        t = re.search(r"<title>(.*?)</title>", it, re.S)
        g = re.search(r"<guid>(.*?)</guid>", it, re.S)
        d = re.search(r"Sale Price: \$([\d,.]+).*?Qty: (\d+)", it, re.S)
        if not g:
            continue
        url = htmllib.unescape(g.group(1)).strip()
        cid = url.rstrip("/").split("/")[-1]
        out.append({
            "titulo": htmllib.unescape(t.group(1)).strip() if t else "?",
            "url": url, "id": cid,
            "precio": float(d.group(1).replace(",", "")) if d else None,
            "qty": int(d.group(2)) if d else None,
        })
    return out

def main():
    try:
        fs({"cmd": "sessions.destroy", "session": "ghost"}, timeout=30000)
    except Exception:
        pass
    time.sleep(3)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = f"/root/comc-data/bb-rookies-{ts}"
    os.makedirs(outdir, exist_ok=True)
    print(f"DIR {outdir}", flush=True)

    for jugador in JUGADORES:
        time.sleep(random.uniform(25, 40))
        hh = get_feed(feed_url(jugador))
        if not hh:
            print(json.dumps({"jugador": jugador, "error": "sin_html"}, ensure_ascii=False), flush=True)
            continue
        items = parse_feed(hh)
        json.dump({"jugador": jugador, "items": items},
                  open(f"{outdir}/{jugador.replace(' ', '-')}.json", "w"), ensure_ascii=False, indent=1)
        print(json.dumps({"jugador": jugador, "items": len(items)}, ensure_ascii=False), flush=True)
        # mostrar todos (candidatas marcadas)
        for it in items:
            if it["precio"] is None:
                continue
            cand = it["precio"] <= MAX_PRECIO and (it["qty"] or 0) >= MIN_COPIAS
            marca = "CANDIDATA ✅" if cand else ""
            print(f"  {it['titulo'][:70]:72} | ${it['precio']:6.2f} | qty {it['qty']} {marca}", flush=True)
    print("OK", flush=True)

if __name__ == "__main__":
    main()
