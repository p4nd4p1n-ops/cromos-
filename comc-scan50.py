#!/usr/bin/env python3
"""comc-scan50.py — escaneo de las cartas del Top 50 NBA en Topps Chrome Base 2025-26.
Usa top50-paths.json (paths ya resueltos). Anti-ban + auto-reanudación + monitor bloqueo.
Uso: comc-scan50.py
"""
import json, sys, urllib.request, re, time, random, datetime, os

FS = "http://127.0.0.1:8191/v1"
DATA_DIR = "/root/comc-data"
os.makedirs(DATA_DIR, exist_ok=True)

AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
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

def human_delay():
    return max(4.0, min(30.0, random.gauss(12, 5)))

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
    return out

def calc_liquidez(copias, sales):
    hoy = datetime.date.today()
    ventas_7d = 0
    for fstr, _ in sales:
        try:
            fecha = datetime.datetime.strptime(fstr, "%b %d, %Y").date()
            if (hoy - fecha).days <= 7:
                ventas_7d += 1
        except ValueError:
            pass
    vel = ventas_7d / 7.0
    dias = round(copias / vel, 1) if vel > 0 else None
    turn = round(ventas_7d / copias * 100, 1) if copias else None
    return ventas_7d, round(vel, 3), dias, turn

def main():
    paths = json.load(open(f"{DATA_DIR}/top50-paths.json"))
    hoy = datetime.date.today().isoformat()
    out_file = f"{DATA_DIR}/scan-top50-{hoy}.json"
    rows = {}
    if os.path.exists(out_file):
        for r in json.load(open(out_file)):
            rows[r["nombre"]] = r
    session = "ghost"
    try:
        fs({"cmd": "sessions.destroy", "session": session}, timeout=30000)
    except Exception:
        pass
    time.sleep(2)
    pendientes = [(j, m) for j, m in paths.items() if j not in rows]
    random.shuffle(pendientes)
    print(f"pendientes: {len(pendientes)} de {len(paths)}", flush=True)
    bloqueado = None
    lotes = [pendientes[i:i + 10] for i in range(0, len(pendientes), 10)]
    for li, lote in enumerate(lotes):
        if bloqueado:
            break
        for jugador, m in lote:
            if bloqueado:
                break
            try:
                url = "https://www.comc.com" + m["path"]
                html = get_html(url)
                if not html:
                    print(json.dumps({"nombre": jugador, "error": "sin_html"}, ensure_ascii=False), flush=True)
                    time.sleep(human_delay())
                    continue
                blk = check_blocked(html)
                if blk:
                    bloqueado = blk
                    print(json.dumps({"nombre": jugador, "error": "BLOQUEO:" + blk}, ensure_ascii=False), flush=True)
                    break
                d = parse_card(html)
                v7, vel, dias, turn = calc_liquidez(d.get("copias", 0), d.get("sales", []))
                r = {"nombre": jugador, "path": m["path"], "num": m["num"], "es_sp": m.get("es_sp", False),
                     "fecha": hoy, "min": d.get("min"), "seg": d.get("seg"), "gap": d.get("gap"),
                     "copias": d.get("copias"), "n_min": d.get("n_min"), "n_cerca": d.get("n_cerca"),
                     "ventas_7d": v7, "vel_dia": vel, "dias_inv": dias, "turnover": turn,
                     "sales": d.get("sales", [])[:20]}
                rows[jugador] = r
                json.dump(list(rows.values()), open(out_file, "w"), ensure_ascii=False, indent=1)
                print(json.dumps({k: r[k] for k in r if k != "sales"}, ensure_ascii=False), flush=True)
                time.sleep(human_delay())
            except Exception as e:
                print(json.dumps({"nombre": jugador, "error": str(e)[:80]}, ensure_ascii=False), flush=True)
                time.sleep(human_delay())
        if li < len(lotes) - 1 and not bloqueado:
            pausa = random.uniform(300, 600)
            print(f"--- pausa {int(pausa)}s ---", flush=True)
            time.sleep(pausa)
    json.dump(list(rows.values()), open(out_file, "w"), ensure_ascii=False, indent=1)
    print("=== CSV ===")
    print("nombre;num;min;seg;gap%;copias;ventas_7d;vel_dia;dias_inv;turnover%")
    for r in sorted(rows.values(), key=lambda x: (x.get("ventas_7d") or 0), reverse=True):
        print(f"{r['nombre']};{r.get('num','')};{r.get('min','')};{r.get('seg','')};{r.get('gap','')};"
              f"{r.get('copias','')};{r.get('ventas_7d','')};{r.get('vel_dia','')};{r.get('dias_inv','')};{r.get('turnover','')}")
    if bloqueado:
        print(f"!!! BLOQUEO: {bloqueado}", flush=True)
        sys.exit(3)
    if pendientes:
        print("INCOMPLETO (re-ejecutar para continuar)", flush=True)
        sys.exit(2)
    print("OK completo", flush=True)

if __name__ == "__main__":
    main()
