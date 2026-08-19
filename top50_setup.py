#!/usr/bin/env python3
"""top50_setup.py — obtener checklist completo de Topps Chrome Base 2025-26 y cruzar con el Top 50 NBA.
Guarda /root/comc-data/top50-paths.json con los paths de las cartas del top 50 presentes en el set.
"""
import json, urllib.request, re, html as h, time, os

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

TOP50 = [
    "Nikola Jokic", "Shai Gilgeous-Alexander", "Victor Wembanyama", "Luka Doncic", "Anthony Edwards",
    "Kawhi Leonard", "Giannis Antetokounmpo", "Jaylen Brown", "Donovan Mitchell", "Cade Cunningham",
    "Jalen Brunson", "Kevin Durant", "Tyrese Maxey", "Stephen Curry", "Jamal Murray",
    "Devin Booker", "Jalen Johnson", "Deni Avdija", "Jalen Duren", "Bam Adebayo",
    "Jayson Tatum", "James Harden", "Pascal Siakam", "Evan Mobley", "Chet Holmgren",
    "LeBron James", "Scottie Barnes", "Karl-Anthony Towns", "Alperen Sengun", "Joel Embiid",
    "Julius Randle", "Lauri Markkanen", "Paolo Banchero", "De'Aaron Fox", "Desmond Bane",
    "Cooper Flagg", "Kon Knueppel", "Amen Thompson", "Austin Reaves", "LaMelo Ball",
    "Brandon Ingram", "Rudy Gobert", "Jalen Williams", "Trey Murphy III", "Brandon Miller",
    "Stephon Castle", "Nickeil Alexander-Walker", "Zion Williamson", "Norman Powell", "Keyonte George",
]

def norm(n):
    n = h.unescape(n).lower()
    n = re.sub(r"[^a-z0-9 ]", "", n)
    return re.sub(r"\s+", " ", n).strip()

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

def fetch_checklist():
    """Páginas del set. Prueba formatos de paginación hasta conseguir todas las cartas."""
    cards = {}  # cardid -> (num, nombre, path)
    urls = [
        "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base,sh,i100",
        "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base,sh,i100,p2",
        "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base,sh,i100,p3",
        "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base,sh,i100,p4",
        "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base,sh,i100,p5",
        "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base,sh,i100,p6",
    ]
    pat = re.compile(r'href="(/Cards/Basketball/2025-26/Topps_Chrome_-_Base/(\d+(?:\.\d+)?)/[^"/]+/(\d+))"[^>]*>')
    for u in urls:
        html = get_html(u)
        if not html:
            print(f"sin html: {u}")
            continue
        found = 0
        for full, num, cid in pat.findall(html):
            if cid not in cards:
                # nombre: buscar en el título/texto del enlace
                m = re.search(r'href="' + re.escape(full) + r'"[^>]*>(.*?)</a>', html, re.S)
                nombre = ""
                if m:
                    t = re.sub(r"<[^>]+>", "", m.group(1))
                    t = re.sub(r"\s+", " ", h.unescape(t)).strip()
                    # formato típico: "2025-26 Topps Chrome - [Base] #253.1 - VJ Edgecombe"
                    mm = re.search(r"-\s*([A-Za-z][^#]*?)\s*$", t)
                    if mm:
                        nombre = mm.group(1).strip()
                cards[cid] = (num, nombre, full)
                found += 1
        print(f"{u}: {found} cartas nuevas (total {len(cards)})")
        time.sleep(3)
    return cards

def main():
    cards = fetch_checklist()
    json.dump({k: v for k, v in cards.items()}, open(f"{DATA_DIR}/checklist-chrome.json", "w"), ensure_ascii=False, indent=1)
    print("=== CARTAS DEL SET:", len(cards))
    # cruzar top50
    matches = {}
    no_encontrados = []
    for j in TOP50:
        jn = norm(j)
        tokens = jn.split()
        apellido = tokens[-1]
        candidatos = []
        for cid, (num, nombre, full) in cards.items():
            nn = norm(nombre)
            if not nn:
                continue
            nt = nn.split()
            if apellido in nt or (apellido in nn):
                candidatos.append((num, nombre, full))
        if not candidatos:
            no_encontrados.append(j)
            continue
        # elegir la base: menor número, sin SP/Graded
        candidatos.sort(key=lambda x: (x[1] and ("SP" in x[1] or "Graded" in x[1]), float(x[0]) if x[0].replace(".", "").isdigit() else 999))
        matches[j] = {"num": candidatos[0][0], "nombre_set": candidatos[0][1], "path": candidatos[0][2]}
        if len(candidatos) > 1:
            matches[j]["otros"] = [(n, nm) for n, nm, _ in candidatos[1:]]
    print("=== ENCONTRADOS:", len(matches))
    for j, m in matches.items():
        print(f"  {j} -> #{m['num']} {m['nombre_set']}")
        if m.get("otros"):
            print(f"      otros: {m['otros']}")
    print("=== NO ENCONTRADOS:", len(no_encontrados))
    for j in no_encontrados:
        print(f"  {j}")
    json.dump(matches, open(f"{DATA_DIR}/top50-paths.json", "w"), ensure_ascii=False, indent=1)
    print("guardado en top50-paths.json")

if __name__ == "__main__":
    main()
