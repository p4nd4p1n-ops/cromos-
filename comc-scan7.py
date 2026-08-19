#!/usr/bin/env python3
"""Escáner COMC v7 — CAMUFLAJE + LIQUIDEZ + RECENT SALES + MONITOR BLOQUEO.
- Cuenta fantasma (dragon941), sesión FS.
- Resuelve path de carta vía página de jugador (caché en /root/comc-data/cardids.json).
- Solo página 1 (min/2º/gap/copias) + Recent Sales con fechas.
- Liquidez: ventas_7d, velocidad/día, días de inventario, turnover.
- Camuflaje: orden aleatorio, delays gaussianos, lotes de 10 con pausa 5-10 min.
- Monitor: captcha/access denied/sign in to continue → PARAR y avisar.
Uso: comc-scan7.py
"""
import json, sys, urllib.request, re, html as h, time, random, datetime, os

FS = "http://127.0.0.1:8191/v1"
DATA_DIR = "/root/comc-data"
CACHE_FILE = f"{DATA_DIR}/cardids.json"
os.makedirs(DATA_DIR, exist_ok=True)

AUTH = "NHm_HFXdfqLDLC1xMt3YIjDaPZATm1x5nWxL3XS6G9kk0lV4Pcep_WHT3KlJMAHj6ZpLUz6TxbWbMXAwnf7lS3el4apRGPd8-2rlKh2JOJV9OMomQ9QTBTNg5yV04uSantEI3ZG9KGlc0hzKmE70g-jnIkGjgVvcMe9XKtKyI9d2Cby4aVSnXO8vVyxwCOS3SYogDSue_OcmKV8cMnYTLKFtud0Ba4OXrfjTpKUtjZEMukCx2CPEN3TJAGSPZmDPzISJMWOoCsKouSt4eoJMP6rOpqWTq_izyK-Cv3VmRJQc1_Y5JjIbOquF-52VI4YDqlLgXkAqe3ynmgiDzCwEC6AGa1yPbp3FWGvovN-hKdlkyqrqX-Ax6FvWc3Cc54nOT_QNAtmx-47GG4ZXvAyQfrjJ3xscQZHFpWzjZOg9ZK38ZjjhklFoxbiW2cktBen6VOqkf1ZmrB2AJQUIJt8wMKDpPEed8QmnWDo700fQ7DwcMYI8OV9DPkH_CepMYiqh5ae9PKKHAr-rOJUO4F-DJLkK7GbnbosiF2elwyCC86A3Spdn7ZRD0UrZ-nY9qQW4po0dUAwXYdNQl4QGVhCjmkpV-Qhd536tFZSrfC2WjaKCgKOw6e6fmQihp0uZijD5MHnFmhoTRgF4pVud6pSPLeBkNkHgcFBq3OgyEamGAfgE0yJ6D_SvGZJGteKpS2SN8dLcBG6rf6VEUwMhk3ZOIZMigImcdJnx23uTljGWsHbz-zje4vpK8G-c_mpV3TSIuMkyykzB_P2kgeZxyrLADjE7OQRT_JyyShIvu_Tw_GHNcFeNCuzcSfCxhJvCPuJpq5y-Y4bR2Cta3luCZmJhdBzH8nEqI6mxXg4KVIrR0pUvNZ2ffv34RN8xbJ6dh764mHs-Q66hxTr0bqHAz33vJw"

COOKIES = [
    {"name": "AuthCookie", "value": AUTH, "domain": "www.comc.com", "path": "/", "httpOnly": True, "secure": True},
    {"name": "__AntiXsrfToken", "value": "957fc2df480843859e9fa1bac46db545", "domain": "www.comc.com", "path": "/"},
    {"name": "ASP.NET_SessionId", "value": "t2ghz14y2gxy5uvgz4m0k0rp", "domain": "www.comc.com", "path": "/", "httpOnly": True},
    {"name": "SiteAffinity", "value": "legacy", "domain": ".comc.com", "path": "/"},
]

# (nombre, slug_exacto_de_la_lista_de_Pin, playerId)
PLAYERS = [
    ("Kon Knueppel", "Kon_Knueppel", "c469745"), ("Cooper Flagg", "Cooper_Flagg", "c465571"),
    ("Derik Queen", "Derik_Queen", "c469128"), ("VJ Edgecombe", "VJ_Edgecombe", "c467242"),
    ("Cedric Coward", "Cedric_Coward", "c491823"), ("Noa Essengue", "Noa_Essengue", "c495117"),
    ("Ace Bailey", "Ace_Bailey", "c469725"), ("Jeremiah Fears", "Jeremiah_Fears", "c491773"),
    ("Tyrese Proctor", "Tyrese_Proctor", "c420694"), ("Dylan Harper", "Dylan_Harper", "c421184"),
    ("Tre Johnson", "Tre_Johnson", "c433088"), ("Alijah Martin", "Alijah_Martin", "c436911"),
    ("Rocco Zikarsky", "Rocco_Zikarsky", "c446060"), ("Walter Clayton Jr.", "Walter_Clayton_Jr", "c484938"),
    ("Kasparas Jakucionis", "Kasparas_Jakucionis", "c487680"), ("Yang Hansen", "Yang_Hansen", "c491759"),
    ("Will Riley", "Will_Riley", "c491761"), ("Nique Clifford", "Nique_Clifford", "c491762"),
    ("Rasheer Fleming", "Rasheer_Fleming", "c491826"), ("Noah Penda", "Noah_Penda", "c494758"),
    ("Ben Saraf", "Ben_Saraf", "c495084"), ("Danny Wolf", "Danny_Wolf", "c495086"),
    ("Jamir Watkins", "Jamir_Watkins", "c495116"), ("Javon Small", "Javon_Small", "c499958"),
    ("Micah Peavy", "Micah_Peavy", "c396353"), ("Johni Broome", "Johni_Broome", "c436873"),
    ("Ryan Kalkbrenner", "Ryan_Kalkbrenner", "c436885"), ("Alex Toohey", "Alex_Toohey", "c446055"),
    ("Brooks Barnhizer", "Brooks_Barnhizer", "c455179"), ("Carter Bryant", "Carter_Bryant", "c467241"),
    ("Khaman Maluach", "Khaman_Maluach", "c467251"), ("Liam McNeeley", "Liam_McNeeley", "c469126"),
    ("Drake Powell", "Drake_Powell", "c469127"), ("Kam Jones", "Kam_Jones", "c469358"),
    ("Asa Newell", "Asa_Newell", "c469744"), ("Nolan Traore", "Nolan_Traore", "c478773"),
    ("Sion James", "Sion_James", "c478777"), ("Koby Brea", "Koby_Brea", "c491671"),
    ("Chaz Lanier", "Chaz_Lanier", "c491824"), ("Maxime Raynaud", "Maxime_Raynaud", "c491825"),
    ("Will Richard", "Will_Richard", "c492151"), ("Hugo Gonzalez", "Hugo_Gonzalez", "c493645"),
    ("Jase Richardson", "Jase_Richardson", "c494757"), ("Joan Beringer", "Joan_Beringer", "c494974"),
    ("Adou Thiero", "Adou_Thiero", "c495085"), ("Collin Murray-Boyles", "Collin_Murray-Boyles", "c495115"),
    ("Egor Demin", "Egor_Demin", "c495118"), ("Thomas Sorber", "Thomas_Sorber", "c495119"),
    ("Yanic Konan-Niederhauser", "Yanic_Konan-Niederhauser", "c495120"), ("Amari Williams", "Amari_Williams", "c499959"),
]

BLOCK_INDICATORS = ["access denied", "captcha", "please verify", "unusual traffic",
                    "sign in to continue"]

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

def resolve_base_path(nombre, slug, player_id):
    """Fetch página de jugador → path completo de la carta BASE."""
    url = f"https://www.comc.com/Players/Basketball/{slug}/{player_id}/Cards/Basketball/2025-26/Topps_Chrome_-_Base,sh,_RC,i100"
    html = get_html(url)
    if not html:
        return None
    pat = re.compile(r'href="(/Cards/Basketball/2025-26/Topps_Chrome_-_Base/(\d+)/[^"/]+/\d+)"')
    cands = []
    for full, num in pat.findall(html):
        if "SP" not in full and "Graded" not in full:
            cands.append((int(num), full))
    if not cands:
        return None
    # la base es la de menor número de carta
    cands.sort(key=lambda x: x[0])
    return cands[0][1]

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
    session = "ghost"
    try:
        fs({"cmd": "sessions.destroy", "session": session}, timeout=30000)
    except Exception:
        pass
    time.sleep(2)
    # caché de paths
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            cache = json.load(open(CACHE_FILE))
        except Exception:
            cache = {}
    hoy = datetime.date.today().isoformat()
    rows = []
    # cargar resultados previos del día (para re-ejecuciones parciales)
    prev_file = f"{DATA_DIR}/scan-{hoy}.json"
    prev = {}
    if os.path.exists(prev_file):
        try:
            for r in json.load(open(prev_file)):
                prev[r["nombre"]] = r
        except Exception:
            prev = {}
    rows = list(prev.values())
    bloqueado = None
    orden = list(range(len(PLAYERS)))
    random.shuffle(orden)
    # filtro: solo faltantes (los que no tienen path en caché o no están en prev)
    faltantes = [i for i in orden if not cache.get(PLAYERS[i][0]) or PLAYERS[i][0] not in prev]
    if not faltantes:
        print("nada pendiente — todas las cartas ya escaneadas", flush=True)
    lotes = [faltantes[i:i + 10] for i in range(0, len(faltantes), 10)]
    for li, lote in enumerate(lotes):
        if bloqueado:
            break
        for idx in lote:
            if bloqueado:
                break
            nombre, slug, pid = PLAYERS[idx]
            try:
                path = cache.get(nombre)
                if not path:
                    path = resolve_base_path(nombre, slug, pid)
                    if path:
                        cache[nombre] = path
                        json.dump(cache, open(CACHE_FILE, "w"))
                    time.sleep(human_delay())
                if not path:
                    print(json.dumps({"nombre": nombre, "error": "sin_path"}, ensure_ascii=False), flush=True)
                    continue
                url = "https://www.comc.com" + path
                html = get_html(url)
                if not html:
                    print(json.dumps({"nombre": nombre, "error": "sin_html"}, ensure_ascii=False), flush=True)
                    time.sleep(human_delay())
                    continue
                blk = check_blocked(html)
                if blk:
                    bloqueado = blk
                    print(json.dumps({"nombre": nombre, "error": "BLOQUEO:" + blk}, ensure_ascii=False), flush=True)
                    break
                d = parse_card(html)
                v7, vel, dias, turn = calc_liquidez(d.get("copias", 0), d.get("sales", []))
                r = {"nombre": nombre, "path": path, "fecha": hoy,
                     "min": d.get("min"), "seg": d.get("seg"), "gap": d.get("gap"),
                     "copias": d.get("copias"), "n_min": d.get("n_min"), "n_cerca": d.get("n_cerca"),
                     "ventas_7d": v7, "vel_dia": vel, "dias_inv": dias, "turnover": turn,
                     "sales": d.get("sales", [])[:20]}
                rows.append(r)
                print(json.dumps({k: r[k] for k in r if k != "sales"}, ensure_ascii=False), flush=True)
                time.sleep(human_delay())
            except Exception as e:
                print(json.dumps({"nombre": nombre, "error": str(e)[:80]}, ensure_ascii=False), flush=True)
                time.sleep(human_delay())
        if li < len(lotes) - 1 and not bloqueado:
            pausa = random.uniform(300, 600)
            print(f"--- pausa {int(pausa)}s entre lotes ---", flush=True)
            time.sleep(pausa)
    with open(f"{DATA_DIR}/scan-{hoy}.json", "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print("=== CSV ===")
    print("nombre;min;seg;gap%;copias;n_min;n_cerca;ventas_7d;vel_dia;dias_inv;turnover%")
    for r in rows:
        print(f"{r['nombre']};{r.get('min','')};{r.get('seg','')};{r.get('gap','')};"
              f"{r.get('copias','')};{r.get('n_min','')};{r.get('n_cerca','')};"
              f"{r.get('ventas_7d','')};{r.get('vel_dia','')};{r.get('dias_inv','')};{r.get('turnover','')}")
    if bloqueado:
        print(f"!!! BLOQUEO DETECTADO: {bloqueado} — PARADO", flush=True)
        sys.exit(3)
    print("OK completo", flush=True)

if __name__ == "__main__":
    main()
