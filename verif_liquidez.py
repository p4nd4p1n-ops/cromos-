#!/usr/bin/env python3
"""verif_liquidez.py — busca candidatas con LIQUIDEZ en otros sets (memorabilia, autos...).
Pin 13/08 12:05: "busca las que tengan liquidez igual que las memorabilia etc".
Baja feeds de sets extra → filtra candidatas baratas → verifica liquidez real (v7d corregido L-026)
de las top con la página de cada carta. Guarda /root/comc-data/verificacion-<fecha>.json
"""
import sys, json, re, time, random, datetime
sys.path.insert(0, "/root/comc-scripts")
import feed_snapshot as fsmod
import muro_scan as ms

SETS = [
    ("CHROME-MEMO", "https://www.comc.com/SearchFeed.aspx?SportID=8&Year=2025-26&ParentSetPath=Basketball%2f2025-26%2fTopps_Chrome&SetPath=Basketball%2f2025-26%2fTopps_Chrome_-_Memorabilia&PageSize=100&Sort%3dr"),
    ("CHROME-AUTOS", "https://www.comc.com/SearchFeed.aspx?SportID=8&Year=2025-26&ParentSetPath=Basketball%2f2025-26%2fTopps_Chrome&SetPath=Basketball%2f2025-26%2fTopps_Chrome_-_Autographs&PageSize=100&Sort%3dr"),
    ("TOPPS-25", "https://www.comc.com/SearchFeed.aspx?SportID=8&Year=2025-26&ParentSetPath=Basketball%2f2025-26%2fTopps&SetPath=Basketball%2f2025-26%2fTopps_-_Base&PageSize=100&Sort%3dr"),
    ("NFL-OPTIC24", "https://www.comc.com/SearchFeed.aspx?SportID=2&Year=2024&ParentSetPath=Football%2f2024%2fPanini_Donruss_Optic&SetPath=Football%2f2024%2fPanini_Donruss_Optic_-_Base&PageSize=100&Sort%3dr"),
    ("NFL-PRIZM24", "https://www.comc.com/SearchFeed.aspx?SportID=2&Year=2024&ParentSetPath=Football%2f2024%2fPanini_Prizm&SetPath=Football%2f2024%2fPanini_Prizm_-_Base&PageSize=100&Sort%3dr"),
]


def extrae_ventas7d(html):  # fix L-026 (fecha+hora, ventana < 7 días)
    sales = re.findall(
        r"([A-Z][a-z]{2} \d{1,2}, \d{4})\s+\d{1,2}:\d{2} [AP]M[^$]*?\$([\d,]+\.\d{2})", html)
    hoy = datetime.date.today()
    v7 = 0
    for fstr, _ in sales:
        try:
            dias = (hoy - datetime.datetime.strptime(fstr, "%b %d, %Y").date()).days
            if 0 <= dias < 7:
                v7 += 1
        except ValueError:
            pass
    return v7


def main():
    solo_feeds = "--feeds" in sys.argv
    verificadas = []
    candidatas_guardadas = {}
    primero_set = True
    for nombre, url_set in SETS:
        if not primero_set and not solo_feeds:
            time.sleep(300)  # pausa entre sets (regla FS)
        primero_set = False
        hh = fsmod.get_feed(url_set)
        items = fsmod.parse_feed(hh) if hh else []
        print(f"[{nombre}] {len(items)} items en feed", flush=True)
        cands = [it for it in items if it.get("precio") and it["precio"] <= 8.0]
        cands.sort(key=lambda x: x["precio"])
        for it in cands[:10]:
            print(f"  CAND: ${it['precio']:.2f} | {it['qty']} copias | {it['titulo'][:60]}", flush=True)
        candidatas_guardadas[nombre] = cands[:15]
        if solo_feeds:
            continue
        # verificar liquidez de las top (máx 2 por set — regla FS)
        for it in cands[:2]:
            time.sleep(random.uniform(25, 35))
            html = ms.get_html(it["url"])
            if not html:
                print(f"  ❌ sin_html: {it['titulo'][:45]}", flush=True)
                continue
            try:
                muro, resumen = ms.parse_muro(html)
            except Exception as e:
                print(f"  ❌ parse: {e}", flush=True)
                continue
            if not muro:
                print(f"  ⚠️ muro vacío: {it['titulo'][:45]}", flush=True)
                continue
            precios = sorted(resumen.keys())
            p1 = precios[0]
            seg = precios[1] if len(precios) > 1 else None
            v7 = extrae_ventas7d(html)
            owners = "/".join(resumen[p1]["owners"])
            print(f"  ✔ {it['titulo'][:45]} | 1º ${p1:.2f} ({owners}) | 2º ${seg if seg else 0:.2f} | copias {len(muro)} | v7d {v7}", flush=True)
            verificadas.append({"set": nombre, "titulo": it["titulo"], "url": it["url"],
                                "min": p1, "seg": seg, "v7d": v7, "owners": owners})
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    with open(f"/root/comc-data/feed-candidatas-{stamp}.json", "w") as fh:
        json.dump(candidatas_guardadas, fh, ensure_ascii=False, indent=1)
    with open(f"/root/comc-data/verificacion-{stamp}.json", "w") as fh:
        json.dump(verificadas, fh, ensure_ascii=False, indent=1)
    print(f"=== FIN: {len(verificadas)} verificadas → feed-candidatas-{stamp}.json ===", flush=True)


if __name__ == "__main__":
    main()
