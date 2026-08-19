#!/usr/bin/env python3
"""top50_setup3.py — cruce con scoring por tokens del nombre completo.
Lee checklist-chrome.json, guarda top50-paths.json. Debug de no encontrados.
"""
import json, re, unicodedata, os

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

def tokens(n):
    return set(norm(n).split())

def score(nombre_jugador, slug):
    """Tokens del nombre del jugador presentes en el slug (normalizado)."""
    tj = tokens(nombre_jugador)
    ts = tokens(slug)
    return len(tj & ts), len(ts)

def main():
    cards = json.load(open(f"{DATA_DIR}/checklist-chrome.json"))
    por_slug = {}
    for cid, (num, nombre, full) in cards.items():
        m = re.search(r"/(\d+(?:\.\d+)?)/([^/]+)/(\d+)$", full)
        if not m:
            continue
        num_url, slug, cid_url = m.groups()
        es_sp = ("sp" in slug.lower() or "variation" in slug.lower()
                 or "autograph" in slug.lower() or "parallel" in slug.lower())
        key = norm(slug)
        key = re.sub(r"^(sp image variation|sp|image variation|autograph|parallel)\s*", "", key)
        prev = por_slug.get(key)
        if prev is None or (es_sp is False and prev[2] is True):
            por_slug[key] = (num_url, full, es_sp, slug)
    print("slugs únicos:", len(por_slug))

    matches, no_encontrados = {}, []
    for j in TOP50:
        mejor, mejor_score = None, (-1, -1)
        for key, (num_url, full, es_sp, slug) in por_slug.items():
            sc, lts = score(j, key)
            if sc >= 2 and sc > mejor_score[0]:
                mejor, mejor_score = (num_url, full, es_sp, slug), (sc, lts)
        if mejor is None:
            no_encontrados.append(j)
            continue
        num_url, full, es_sp, slug = mejor
        matches[j] = {"num": num_url, "path": full, "es_sp": es_sp, "slug": slug}
        tag = " (SP)" if es_sp else ""
        print(f"  {j} -> #{num_url}{tag} {slug} [score {mejor_score[0]}]")
    print("=== ENCONTRADOS:", len(matches), "| NO ENCONTRADOS:", len(no_encontrados))
    for j in no_encontrados:
        print("  FALTA:", j)
    # debug de no encontrados: buscar fragmentos en slugs
    print("=== DEBUG slugs con fragmentos:")
    for frag in ["doncic", "avdija", "towns", "williamson", "zion"]:
        hits = [slug for key, (_, _, _, slug) in por_slug.items() if frag in key]
        print(f"  '{frag}': {hits}")
    json.dump(matches, open(f"{DATA_DIR}/top50-paths.json", "w"), ensure_ascii=False, indent=1)
    print("guardado")

if __name__ == "__main__":
    main()
