#!/usr/bin/env python3
"""top50_setup2.py — cruzar Top 50 con checklist Chrome Base usando el SLUG de la URL (no el HTML).
Lee checklist-chrome.json (cardid -> [num, nombre, full]) y guarda top50-paths.json.
"""
import json, re, html as h, unicodedata, os

DATA_DIR = "/root/comc-data"

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
    n = unicodedata.normalize("NFKD", n)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().replace("_", " ").replace("-", " ")
    n = re.sub(r"[^a-z0-9 ]", "", n)
    return re.sub(r"\s+", " ", n).strip()

def main():
    cards = json.load(open(f"{DATA_DIR}/checklist-chrome.json"))
    # reconstruir: slug desde el path
    por_slug = {}  # slug normalizado -> (num, path, es_sp)
    for cid, (num, nombre, full) in cards.items():
        m = re.search(r"/(\d+(?:\.\d+)?)/([^/]+)/(\d+)$", full)
        if not m:
            continue
        num_url, slug, cid_url = m.groups()
        es_sp = "sp" in slug.lower() or "variation" in slug.lower() or "autograph" in slug.lower() or "parallel" in slug.lower()
        sn = norm(slug)
        # quitar prefijos tipo "sp image variation " del slug normalizado para emparejar
        limpio = re.sub(r"^(sp image variation|sp|image variation|autograph|parallel)\s*", "", sn)
        key = limpio
        prev = por_slug.get(key)
        if prev is None or (es_sp is False and prev[2] is True):
            por_slug[key] = (num_url, full, es_sp, slug)
    print("slugs únicos:", len(por_slug))
    matches = {}
    no_encontrados = []
    ambiguos = []
    for j in TOP50:
        jn = norm(j)
        tokens = jn.split()
        apellido = tokens[-1]
        candidatos = []
        for key, (num_url, full, es_sp, slug) in por_slug.items():
            if apellido in key or apellido in (key.split()[-1] if key else ""):
                candidatos.append((num_url, full, es_sp, slug, key))
        # filtrar: el apellido debe ser el último token del slug (más fiable)
        filtrados = [c for c in candidatos if c[4].split() and c[4].split()[-1] == apellido]
        if not filtrados:
            filtrados = candidatos
        if not filtrados:
            no_encontrados.append(j)
            continue
        # preferir base (no SP)
        base = [c for c in filtrados if not c[2]]
        eleccion = base[0] if base else filtrados[0]
        num_url, full, es_sp, slug, key = eleccion
        matches[j] = {"num": num_url, "path": full, "es_sp": es_sp, "slug": slug}
        if len(filtrados) > 1:
            matches[j]["otros"] = [c[3] for c in filtrados[1:]]
    print("=== ENCONTRADOS:", len(matches))
    for j, m in matches.items():
        tag = " (SP)" if m["es_sp"] else ""
        print(f"  {j} -> #{m['num']}{tag} {m['slug']}")
        if m.get("otros"):
            print(f"      otros: {m['otros']}")
    print("=== NO ENCONTRADOS:", len(no_encontrados))
    for j in no_encontrados:
        print(f"  {j}")
    json.dump(matches, open(f"{DATA_DIR}/top50-paths.json", "w"), ensure_ascii=False, indent=1)
    print("guardado")

if __name__ == "__main__":
    main()
