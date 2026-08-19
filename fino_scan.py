#!/usr/bin/env python3
"""fino_scan.py — escaneo fino de liquidez de las top candidatas.
Lee los snapshots player-*.json, coge las candidatas con más copias (dedupe por id),
y escanea cada carta en profundidad: min, seg, gap, copias, ventas_7d, vel_dia,
dias_inv, turnover, total_hist, dias_venta_7d, quarterly (tendencia trimestral).
Uso: fino_scan.py [N]   (N = nº de cartas a escanear, default 12)
Salida: JSON por línea + resumen final ordenado por ventas_7d.
"""
import json, urllib.request, re, time, random, datetime, os, sys, glob, html as htmllib

FS = "http://127.0.0.1:8191/v1"
DATA_DIR = "/root/comc-data/snapshots"

AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

# Cartas extra que no salen de los snapshots de jugadores (p.ej. la Topps Now Olímpico)
EXTRAS = []

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

def parse_muro(html):
    """Muro completo: cada copia con su precio, item_id y vendedor (owner).
    Devuelve lista ordenada por precio de {precio, item_id, owner} y un resumen
    agrupado por precio: {precio: {'copias': N, 'owners': [...], 'mismo_owner': bool}}"""
    items = re.findall(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', html)
    owners = dict(re.findall(r'Item: (\d+)<div[^>]*>.*?Owner: <strong><a href="/Users/[^"]+"[^>]*>([^<]+)</a>', html, re.S))
    # fallback si el orden de owners no casa: buscar Owner por item id en ownerdetails
    if not owners or len(owners) < len(items):
        for m in re.finditer(r'Owner: <strong><a href="/Users/([^"]+)"[^>]*>([^<]+)</a></strong>.*?Item: (\d+)', html, re.S):
            owners[m.group(3)] = m.group(2)
    muro = []
    for item_id, precio_txt in items:
        muro.append({"item_id": item_id, "precio": float(precio_txt.replace(",", "")),
                     "owner": owners.get(item_id, "?")})
    muro.sort(key=lambda x: x["precio"])
    resumen = {}
    for m in muro:
        p = m["precio"]
        e = resumen.setdefault(p, {"copias": 0, "owners": []})
        e["copias"] += 1
        if m["owner"] not in e["owners"]:
            e["owners"].append(m["owner"])
    for e in resumen.values():
        e["mismo_owner"] = len(e["owners"]) == 1
    return muro, resumen

def parse_sales_detallado(html):
    """Ventas con detalle completo: fecha, hora, precio, tipo de transacción y grado.
    Devuelve lista de {fecha, hora, precio, tipo, grado}.
    Tipos: 'Fixed Price', 'On Sale', 'Offer', 'N Item Offer' (lote), etc."""
    sales = []
    i = html.find("gvItemsSold")
    if i < 0:
        return sales
    seg = html[i:]
    # cada fila: <tr> con 5 <td>: Date | Time (PST) | Grade & Notes | Sale Price | Transaction
    for m in re.finditer(r"<tr>.*?</tr>", seg, re.S):
        fila = m.group(0)
        if "gvItemsSold" in fila or "<th" in fila:
            continue
        tds = re.findall(r"<td[^>]*>(.*?)</td>", fila, re.S)
        if len(tds) < 5:
            continue
        def limpia(x):
            x = re.sub(r"<[^>]+>", " ", x)
            return re.sub(r"\s+", " ", x).strip()
        fecha = limpia(tds[0])
        hora = limpia(tds[1])
        grado = limpia(tds[2])
        precio_m = re.search(r"\$([\d,]+\.\d{2})", tds[3])
        tipo = limpia(tds[4])
        if not fecha or not precio_m:
            continue
        sales.append({"fecha": fecha, "hora": hora, "precio": float(precio_m.group(1).replace(",", "")),
                      "tipo": tipo, "grado": grado})
    return sales

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

def calc_liquidez(copias, ventas_reales):
    hoy = datetime.date.today()
    eventos = set()
    for s in ventas_reales:
        try:
            fecha = datetime.datetime.strptime(
                s["fecha"], "%b %d, %Y").date()
            if (hoy - fecha).days <= 7:
                eventos.add((fecha.isoformat(), s.get("hora")))
        except (ValueError, KeyError):
            pass
    dias_con_venta = set(e[0] for e in eventos)
    ventas_7d = len(eventos)
    vel = ventas_7d / 7.0
    dias = round(copias / vel, 1) if vel > 0 else None
    turn = round(ventas_7d / copias * 100, 1) if copias else None
    return ventas_7d, round(vel, 3), dias, turn, len(dias_con_venta)

def es_ruido(c):
    """Descarta Non-Sports (Space Jam y similares): copias altas, cero liquidez."""
    return "/Cards/Non-Sports/" in (c.get("url") or "")

def urls_ya_medidas():
    """URLs que ya pasaron por algun fino anterior."""
    vistas = set()
    for f in glob.glob(DATA_DIR + "/fino-*.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for r in d:
            if r.get("url"):
                vistas.add(r["url"])
    return vistas

def cargar_candidatas():
    """Une todos los snapshots player-*, dedupe por id, devuelve lista de cartas."""
    por_id = {}
    for f in glob.glob(DATA_DIR + "/player-*.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for c in d.get("items", []):
            if c.get("marca") == "CANDIDATA" and c.get("url") and c.get("qty"):
                if es_ruido(c):
                    continue
                cid = c["id"]
                if cid not in por_id or (c.get("qty") or 0) > (por_id[cid].get("qty") or 0):
                    por_id[cid] = c
    return sorted(por_id.values(), key=lambda x: x.get("qty") or 0, reverse=True)

def seleccionar(cand, n):
    """60% por volumen de copias, 40% exploracion de cartas nunca medidas."""
    n_explora = max(1, int(round(n * 0.4)))
    n_volumen = n - n_explora
    medidas = urls_ya_medidas()
    elegidas = []
    urls = set()
    for c in cand:
        if len(elegidas) >= n_volumen:
            break
        if c["url"] not in urls:
            elegidas.append(c)
            urls.add(c["url"])
    nuevas = [c for c in cand if c["url"] not in medidas and c["url"] not in urls]
    for c in nuevas[:n_explora]:
        elegidas.append(c)
        urls.add(c["url"])
    if len(elegidas) < n:
        for c in cand:
            if len(elegidas) >= n:
                break
            if c["url"] not in urls:
                elegidas.append(c)
                urls.add(c["url"])
    print(json.dumps({"plazas_volumen": n_volumen,
                      "plazas_exploracion": len(elegidas) - n_volumen,
                      "urls_ya_medidas": len(medidas)}, ensure_ascii=False), flush=True)
    return elegidas
def cartas_inventario():
    """Cartas del inventario: escanearlas cada noche para acumular ventas."""
    import os
    out = []
    for ruta in ("/root/comc-data/inventario.txt",
                 "/root/comc-data/seguimiento.txt"):
        if not os.path.exists(ruta):
            continue
        for ln in open(ruta, encoding="utf-8"):
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            f = [x.strip() for x in ln.split(";")]
            if len(f) >= 3 and f[2]:
                out.append((f[1], f[2]))
    return out

def cartas_punto_mira():
    import json as _json
    import os as _os
    ruta = "/root/comc-data/punto-mira.json"
    if not _os.path.exists(ruta):
        return []
    try:
        doc = _json.load(open(ruta))
    except Exception:
        return []
    out = []
    for c in doc.get("cartas", []):
        if c.get("url"):
            out.append((c.get("nombre") or c.get("codigo"), c["url"]))
    return out


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    try:
        fs({"cmd": "sessions.destroy", "session": "ghost"}, timeout=30000)
    except Exception:
        pass
    time.sleep(2)

    cand = cargar_candidatas()
    seleccion = seleccionar(cand, n)
    print(json.dumps({"seleccion": len(seleccion), "de_candidatas_total": len(cand)}, ensure_ascii=False), flush=True)

    hoy = datetime.date.today().isoformat()
    resultados = []
    for nombre, url in EXTRAS:
        seleccion.append({"titulo": nombre, "url": url, "precio": None, "qty": None})
    ya = set(c.get("url") for c in seleccion)
    for t, u in cartas_inventario():
        if u not in ya:
            seleccion.append({"titulo": t, "url": u,
                              "precio": None, "qty": None})
            ya.add(u)
    for t, u in cartas_punto_mira():
        if u not in ya:
            seleccion.append({"titulo": t, "url": u,
                              "precio": None, "qty": None})
            ya.add(u)

    for c in seleccion:
        url = c["url"]
        print(json.dumps({"accion": "fino", "carta": c.get("titulo", "?")[:80]}, ensure_ascii=False), flush=True)
        html = get_html(url)
        if not html:
            print(json.dumps({"carta": c.get("titulo"), "error": "sin_html"}, ensure_ascii=False), flush=True)
            time.sleep(random.uniform(5, 12))
            continue
        d = parse_card(html)
        muro, muro_resumen = parse_muro(html)
        # BALLENA: vendedor con >=2 copias en el 1º o 2º escalón del muro (2 precios más bajos)
        ballena = False
        if muro:
            top2 = sorted(set(m["precio"] for m in muro))[:2]
            from collections import Counter
            cnt = Counter(m["owner"] for m in muro if m["precio"] in top2)
            ballena = any(n >= 2 for n in cnt.values())
        sales_det = parse_sales_detallado(html)
        # ventas individuales REALES: excluir lotes (Offer/N Item Offer) y gradadas
        ventas_reales = [s for s in sales_det
                         if "offer" not in s["tipo"].lower() and not s["grado"]]
        v7, vel, dias, turn, dias_distintos = calc_liquidez(d.get("copias", 0), ventas_reales)
        r = {"titulo": c.get("titulo"), "url": url, "fecha": hoy,
             "min": d.get("min"), "seg": d.get("seg"), "gap": d.get("gap"),
             "copias": d.get("copias"), "ventas_7d": v7, "vel_dia": vel,
             "dias_inv": dias, "turnover": turn, "total_hist": d.get("total_hist"),
             "dias_venta_7d": dias_distintos, "quarterly": d.get("quarterly"),
             "muro": muro, "muro_resumen": muro_resumen, "ballena": ballena,
             "sales_det": sales_det, "ventas_reales": ventas_reales}
        resultados.append(r)
        vel_txt = f"{vel}" + (" 🐋" if ballena else "")
        n_lotes = len([s for s in sales_det if "offer" in s["tipo"].lower()])
        print(json.dumps({k: r[k] for k in r if k not in ("quarterly", "muro", "muro_resumen", "sales_det", "ventas_reales")} | {"vel_txt": vel_txt, "n_ventas_det": len(sales_det), "n_lotes": n_lotes}, ensure_ascii=False), flush=True)
        res_txt = "; ".join(f"{e['copias']}: ${p}" for p, e in sorted(muro_resumen.items()))
        print(json.dumps({"MURO": {"titulo": r["titulo"][:50], "muro": res_txt[:400]}}, ensure_ascii=False), flush=True)
        time.sleep(random.uniform(6, 14))

    # guardar resultados
    out = f"{DATA_DIR}/fino-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    json.dump(resultados, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"guardado: {out}", flush=True)

    print("=== RESUMEN FINO (ordenado por ventas 7d) ===", flush=True)
    for r in sorted(resultados, key=lambda x: x.get("ventas_7d") or 0, reverse=True):
        q = r.get("quarterly") or []
        q3 = q[-3:] if q else []
        b = " 🐋" if r.get("ballena") else ""
        print(f"{r.get('titulo','?')[:70]} | min ${r.get('min')} | {r.get('copias')} cop | v7d {r.get('ventas_7d')} | días {r.get('dias_venta_7d')} | total {r.get('total_hist')} | trim {q3}{b}", flush=True)
    print("=== MUROS ===", flush=True)
    for r in sorted(resultados, key=lambda x: x.get("ventas_7d") or 0, reverse=True):
        rs = r.get("muro_resumen") or {}
        txt = "; ".join(f"{e['copias']}: ${p}" for p, e in sorted(rs.items()))
        print(f"{r.get('titulo','?')[:55]} → {txt[:350]}", flush=True)
    print("OK", flush=True)

if __name__ == "__main__":
    main()
