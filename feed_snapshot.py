#!/usr/bin/env python3
"""feed_snapshot.py — guarda instantáneas de feeds COMC y compara con la anterior.
Modos:
  feed_snapshot.py            → baja feeds (set + cartas punto de mira), guarda JSON, compara si hay previa
  feed_snapshot.py --compare  → compara las 2 últimas instantáneas sin bajar nada
Uso de salida: JSON por línea con el resumen de diferencias.
"""
import json, urllib.request, re, time, random, datetime, os, sys, html as htmllib

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

SET_URL = ("https://www.comc.com/SearchFeed.aspx?SportID=8&Year=2025-26"
           "&ParentSetPath=Basketball%2f2025-26%2fTopps_Chrome"
           "&SetPath=Basketball%2f2025-26%2fTopps_Chrome_-_Base&PageSize=100&Sort%3dr")

CARTAS = [
    "2025-26 Topps Chrome - [Base] #252.1 - Dylan Harper",
    "2025-26 Topps Chrome - [Base] #253.1 - VJ Edgecombe",
    "2025-26 Topps Chrome - [Base] #254.1 - Kon Knueppel",
    "2025-26 Topps Chrome - [Base] #278.1 - Hugo Gonzalez",
    "2025-26 Topps Chrome - [Base] #221.1 - Victor Wembanyama",
]

# Parámetros del embudo (auto-selección) — visibles y ajustables
BANKROLL = 61.0          # bankroll actual $
MAX_PRECIO = 6.0         # 10% del bankroll (~$6)
MAX_COPIAS = 200         # no perseguir cartas con saturación absurda
MIN_PRECIO = 0.25        # por debajo, el fee se come el margen
MOTIVO_PUNTO_MIRA = "fija punto de mira"
AUTO_SELECCION = False  # Pin 13/08: FUERA — generaba 100 candidatas sin filtro de liquidez (ruido)

def auto_seleccion(items_set):
    """Aplica filtros del embudo al feed del set. Devuelve lista de candidatas + motivo."""
    seleccion = []
    for x in items_set:
        p = x.get("precio"); q = x.get("qty")
        if p is None or q is None:
            continue
        motivos = []
        if p <= MAX_PRECIO and p >= MIN_PRECIO:
            motivos.append(f"precio ${p} ≤ ${MAX_PRECIO}")
        if q > 0 and q <= MAX_COPIAS:
            motivos.append(f"{q} copias")
        if motivos:
            x["motivo"] = " + ".join(motivos)
            seleccion.append(x)
    return seleccion

def feed_url(search):
    import urllib.parse
    return ("https://www.comc.com/SearchFeed.aspx?SportID=0&PageSize=100"
            "&Search=" + urllib.parse.quote(search) + "&Sort%3dr")

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
        precio = float(d.group(1).replace(",", "")) if d else None
        qty = int(d.group(2)) if d else None
        out.append({
            "id": cid,
            "titulo": htmllib.unescape(t.group(1)).strip() if t else "",
            "url": url,
            "precio": precio,
            "qty": qty,
        })
    return out

def guardar(nombre, items):
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = f"{DATA_DIR}/{nombre}-{ts}.json"
    json.dump({"fecha": ts, "items": items}, open(path, "w"), ensure_ascii=False, indent=1)
    return path

def ultimas(nombre, n=2):
    files = sorted(f for f in os.listdir(DATA_DIR) if f.startswith(nombre + "-") and f.endswith(".json"))
    return [f"{DATA_DIR}/{f}" for f in files[-n:]]

def comparar(a, b):
    """a = anterior, b = nueva. Devuelve dict de diferencias."""
    da = {x["id"]: x for x in a["items"]}
    db = {x["id"]: x for x in b["items"]}
    dif = {"nuevas": [], "qty_sube": [], "precio_baja": [], "precio_sube": [], "qty_baja": [], "desaparecidas": []}
    for cid, x in db.items():
        if cid not in da:
            dif["nuevas"].append(x)
        else:
            y = da[cid]
            if x["qty"] is not None and y["qty"] is not None:
                if x["qty"] > y["qty"]:
                    dif["qty_sube"].append({"id": cid, "titulo": x["titulo"], "qty": f"{y['qty']}→{x['qty']}", "precio": x["precio"]})
                elif x["qty"] < y["qty"]:
                    dif["qty_baja"].append({"id": cid, "titulo": x["titulo"], "qty": f"{y['qty']}→{x['qty']}", "precio": x["precio"]})
            if x["precio"] is not None and y["precio"] is not None:
                if x["precio"] < y["precio"]:
                    dif["precio_baja"].append({"id": cid, "titulo": x["titulo"], "precio": f"{y['precio']}→{x['precio']}", "qty": x["qty"]})
                elif x["precio"] > y["precio"]:
                    dif["precio_sube"].append({"id": cid, "titulo": x["titulo"], "precio": f"{y['precio']}→{x['precio']}", "qty": x["qty"]})
    for cid, x in da.items():
        if cid not in db:
            dif["desaparecidas"].append(x)
    return dif

def ultimas_por_carta(nombre, n=2):
    """Devuelve dict: clave de carta -> lista de paths de sus snapshots (orden cronológico)."""
    por_carta = {}
    for f in sorted(f for f in os.listdir(DATA_DIR) if f.startswith(nombre + "-") and f.endswith(".json")):
        # feed-carta-YYYYMMDD-HHMMSS.json → el nombre no distingue carta; usar primer item del JSON
        d = json.load(open(f"{DATA_DIR}/{f}"))
        items = d.get("items", [])
        clave = "?"
        if items:
            t = items[0].get("titulo", "")
            m = re.search(r"#([\d.]+)\s*-\s*([A-Za-z\. ]+)$", t)
            clave = m.group(2).strip() if m else t[:30]
        por_carta.setdefault(clave, []).append(f"{DATA_DIR}/{f}")
    return {k: v[-n:] for k, v in por_carta.items()}

def main():
    if "--compare" in sys.argv:
        for nombre in ["feed-set", "feed-carta"]:
            if nombre == "feed-set":
                fs_ = ultimas(nombre)
                if len(fs_) >= 2:
                    a = json.load(open(fs_[0])); b = json.load(open(fs_[1]))
                    d = comparar(a, b)
                    print(json.dumps({"tipo": nombre, "desde": a["fecha"], "hasta": b["fecha"], "dif": d}, ensure_ascii=False))
                else:
                    print(json.dumps({"tipo": nombre, "error": "necesita 2 instantáneas"}, ensure_ascii=False))
            else:
                for carta, fs_ in ultimas_por_carta(nombre).items():
                    if len(fs_) >= 2:
                        a = json.load(open(fs_[0])); b = json.load(open(fs_[1]))
                        d = comparar(a, b)
                        print(json.dumps({"tipo": nombre, "carta": carta, "desde": a["fecha"], "hasta": b["fecha"], "dif": d}, ensure_ascii=False))
                    else:
                        print(json.dumps({"tipo": nombre, "carta": carta, "error": "necesita 2 instantáneas"}, ensure_ascii=False))
        return

    # modo snapshot
    try:
        fs({"cmd": "sessions.destroy", "session": "ghost"}, timeout=30000)
    except Exception:
        pass
    time.sleep(2)

    print(json.dumps({"accion": "feed set"}, ensure_ascii=False), flush=True)
    hh = get_feed(SET_URL)
    items = parse_feed(hh) if hh else []
    print(json.dumps({"feed-set": len(items)}, ensure_ascii=False), flush=True)
    if items:
        p = guardar("feed-set", items)
        print(json.dumps({"guardado": p}, ensure_ascii=False), flush=True)

        # AUTO-SELECCIÓN: embudo visible, se guarda y se imprime
        seleccion = auto_seleccion(items) if AUTO_SELECCION else []
        sel_path = f"{DATA_DIR}/auto-seleccion-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        json.dump({"fecha": datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
                   "params": {"bankroll": BANKROLL, "max_precio": MAX_PRECIO,
                              "min_precio": MIN_PRECIO, "max_copias": MAX_COPIAS},
                   "seleccion": seleccion}, open(sel_path, "w"), ensure_ascii=False, indent=1)
        print(json.dumps({"AUTO-SELECCION": {"guardado": sel_path, "total": len(seleccion)}},
                         ensure_ascii=False), flush=True)
        for s in seleccion:
            print(json.dumps({"SEL": {"titulo": s["titulo"], "precio": s["precio"],
                                       "qty": s["qty"], "motivo": s["motivo"]}},
                             ensure_ascii=False), flush=True)

        # feeds individuales: punto de mira fijo + top de la auto-selección (hasta 10)
        por_titulo = {}
        for s in seleccion:
            t = s["titulo"]
            # normalizar título para buscar variantes (sin el sufijo de variante)
            por_titulo[t] = t
        a_escanear = list(CARTAS) + [t for t in por_titulo.values() if t not in CARTAS][:10]
        print(json.dumps({"individuales_plan": len(a_escanear)}, ensure_ascii=False), flush=True)

        for titulo in a_escanear:
            time.sleep(random.uniform(5, 10))
            print(json.dumps({"accion": "feed carta", "carta": titulo}, ensure_ascii=False), flush=True)
            hh = get_feed(feed_url(titulo))
            items_c = parse_feed(hh) if hh else []
            print(json.dumps({"feed-carta": len(items_c), "carta": titulo}, ensure_ascii=False), flush=True)
            if items_c:
                p = guardar("feed-carta", items_c)
                print(json.dumps({"guardado": p}, ensure_ascii=False), flush=True)
    else:
        print(json.dumps({"error": "feed set vacío, no hay auto-selección"}, ensure_ascii=False), flush=True)

    # comparar si hay previas (por carta, para no mezclar cartas distintas)
    fs_ = ultimas("feed-set")
    if len(fs_) >= 2:
        a = json.load(open(fs_[0])); b = json.load(open(fs_[1]))
        d = comparar(a, b)
        print(json.dumps({"COMPARACION": "feed-set", "desde": a["fecha"], "hasta": b["fecha"],
                          "nuevas": len(d["nuevas"]), "qty_sube": len(d["qty_sube"]),
                          "precio_baja": len(d["precio_baja"]), "precio_sube": len(d["precio_sube"]),
                          "qty_baja": len(d["qty_baja"]),
                          "desaparecidas": len(d["desaparecidas"])}, ensure_ascii=False), flush=True)
    for carta, fs_c in ultimas_por_carta("feed-carta").items():
        if len(fs_c) >= 2:
            a = json.load(open(fs_c[0])); b = json.load(open(fs_c[1]))
            d = comparar(a, b)
            print(json.dumps({"COMPARACION": "feed-carta", "carta": carta, "desde": a["fecha"], "hasta": b["fecha"],
                              "nuevas": len(d["nuevas"]), "qty_sube": len(d["qty_sube"]),
                              "precio_baja": len(d["precio_baja"]), "precio_sube": len(d["precio_sube"]),
                              "qty_baja": len(d["qty_baja"]),
                              "desaparecidas": len(d["desaparecidas"])}, ensure_ascii=False), flush=True)
    print("OK", flush=True)

if __name__ == "__main__":
    main()
