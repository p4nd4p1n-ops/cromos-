#!/usr/bin/env python3
"""player_scan.py — catálogo completo de un jugador en COMC + filtro de mercado.
Uso: player_scan.py "Stephen Curry" ["LeBron James" ...]
Por cada jugador: 1 petición al feed de búsqueda → todas sus cartas con precio/copias.
Marca cada carta: CANDIDATA (mercado vivo) / OBSERVAR (límite) / FUERA (no operativa).
Guarda snapshot en /root/comc-data/snapshots/player-<jugador>-<fecha>.json
"""
import json, urllib.request, re, time, random, datetime, os, sys, html as htmllib, urllib.parse

FS = "http://127.0.0.1:8191/v1"
DATA_DIR = "/root/comc-data/snapshots"
os.makedirs(DATA_DIR, exist_ok=True)

AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

# Parámetros del filtro de mercado (alineados con reglas de Pin)
MAX_PRECIO = 6.0      # 10% del bankroll (~$6)
MIN_COPIAS = 10       # copias a la venta = mercado vivo
EXCLUIR_VARIANTES = ["auto", "patch", "sp - image", "image variation", "/1", "/2", "/3", "/4", "/5",
                     "graded", "psa", "bgs", "cgc", "sgc", "gem", "mint", "nm", "ex-nm", "ex&nbsp;", "ex to"]

def fs(payload, timeout=120000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def get_feed(url, retries=3):
    for i in range(retries):
        try:
            d = fs({"cmd": "request.get", "url": url, "maxTimeout": 90000, "session": "ghost", "cookies": COOKIES})
            hh = d.get("solution", {}).get("response", "")
            if hh and "<item>" in hh:
                return hh
        except Exception:
            pass
        time.sleep(12 * (i + 1))
    return ""

def feed_url(jugador):
    return ("https://www.comc.com/SearchFeed.aspx?PageSize=100"
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
            "id": cid,
            "titulo": htmllib.unescape(t.group(1)).strip() if t else "",
            "url": url,
            "precio": float(d.group(1).replace(",", "")) if d else None,
            "qty": int(d.group(2)) if d else None,
        })
    return out

def clasificar_variante(titulo):
    low = titulo.lower()
    if re.search(r"/\d{1,4}(\s|$)", titulo):       # serial /125
        return "serial"
    if "image variation" in low or "sp - image" in low or re.search(r"#\d+\.2\b", titulo):
        return "sp"
    if "auto" in low and "refractor" not in low:
        return "auto"
    if "patch" in low:
        return "patch"
    if any(x in low for x in ["psa", "bgs", "cgc", "sgc", "gem", "mint", "ex&nbsp;", "ex-nm", "ex to", "nm-mt", "near mint", "poor to"]):
        return "gradada"
    if "refractor" in low or "prizm" in low or "x-fractor" in low or "ice" in low or "wave" in low:
        return "paralela"
    return "base"

def filtrar(carta):
    """Devuelve (marca, motivo)."""
    p = carta["precio"]; q = carta["qty"]
    if p is None or q is None:
        return "FUERA", "sin precio/copias"
    variante = clasificar_variante(carta["titulo"])
    carta["variante"] = variante
    if variante in ("serial", "auto", "patch"):
        return "FUERA", f"{variante} — no operativa"
    if variante == "gradada":
        return "FUERA", "gradada — fuera de rango"
    if variante == "sp":
        return "OBSERVAR", "SP/Image Variation — rara, vigilar"
    if p > MAX_PRECIO:
        return "FUERA", f"precio ${p} > ${MAX_PRECIO}"
    if q < MIN_COPIAS:
        return "OBSERVAR", f"solo {q} copias (<{MIN_COPIAS})"
    return "CANDIDATA", f"${p} · {q} copias — mercado vivo"

def main():
    jugadores = sys.argv[1:] or ["Stephen Curry"]
    try:
        fs({"cmd": "sessions.destroy", "session": "ghost"}, timeout=30000)
    except Exception:
        pass
    time.sleep(2)

    for jugador in jugadores:
        print(f"\n===== {jugador} =====", flush=True)
        hh = get_feed(feed_url(jugador))
        items = parse_feed(hh) if hh else []
        print(f"cartas encontradas: {len(items)}", flush=True)
        if not items:
            continue

        candidatas = []
        for c in items:
            marca, motivo = filtrar(c)
            c["marca"] = marca; c["motivo"] = motivo
            if marca == "CANDIDATA":
                candidatas.append(c)
            print(f"[{marca:9}] ${c['precio'] if c['precio'] is not None else '-':>6} | qty {c['qty'] if c['qty'] is not None else '-':>3} | {c['titulo']}", flush=True)

        # guardar snapshot
        slug = re.sub(r"[^a-z0-9]+", "-", jugador.lower()).strip("-")
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path = f"{DATA_DIR}/player-{slug}-{ts}.json"
        json.dump({"fecha": ts, "jugador": jugador, "items": items}, open(path, "w"), ensure_ascii=False, indent=1)
        print(f"snapshot: {path}", flush=True)
        print(f"CANDIDATAS ({len(candidatas)}):", flush=True)
        for c in sorted(candidatas, key=lambda x: x["qty"] or 0, reverse=True):
            print(f"  → ${c['precio']} · {c['qty']} copias · {c['titulo']} | {c['url']}", flush=True)
        time.sleep(random.uniform(5, 10))

    print("OK", flush=True)

if __name__ == "__main__":
    main()
