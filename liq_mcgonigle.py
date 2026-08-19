#!/usr/bin/env python3
"""liq_mcgonigle.py — mide la LIQUIDEZ de las 4 candidatas de McGonigle:
trae el feed del jugador (URL de Pin), localiza las candidatas por título,
y escanea cada página de carta (espaciado 30-45s) para ventas 7d + vel/día.
"""
import json, urllib.request, re, time, random, sys, html as htmllib
sys.path.insert(0, "/root/comc-scripts")
import player_scan as ps
import muro_scan as ms  # reutiliza cookies/fs de muro_scan

FS = "http://127.0.0.1:8191/v1"
URL_FEED = "https://www.comc.com/SearchFeed.aspx?SportID=0&Search=Kevin+McGonigle&Sort%3dr"

def escanear_carta(nombre, url):
    """Vuelve con ventas 7d + vel/día + copias + total histórico (parse del HTML de carta)."""
    html = ms.get_html(url)
    if not html:
        return {"carta": nombre, "error": "sin_html"}
    # ventas recientes (fechas + precios)
    sales = [(f, float(p)) for f, p in re.findall(
        r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)]
    hoy = __import__("datetime").date.today()
    v7 = sum(1 for f, _ in sales if (hoy - __import__("datetime").datetime.strptime(f, "%b %d, %Y").date()).days <= 7) if sales else 0
    copias = 0
    m = re.search(r'class="allsellers"[^>]*>.*?qtyforsale[^>]*>\s*&nbsp;?\((\d+)\)', html, re.S)
    if m:
        copias = int(m.group(1))
    total_hist = 0
    m2 = re.search(r'sparkline_sparkline"[^>]*>.*?</span>\s*<span>(\d+)</span>', html, re.S)
    if m2:
        total_hist = int(m2.group(1))
    return {"carta": nombre, "ventas_7d": v7, "vel_dia": round(v7 / 7.0, 3),
            "copias": copias, "total_hist": total_hist, "n_ventas_vistas": len(sales)}

def main():
    # 1) feed del jugador
    hh = ps.get_feed(URL_FEED.replace("%3dr", "r"))
    if not hh:
        print(json.dumps({"error": "feed sin_html"}, ensure_ascii=False))
        return
    items = ps.parse_feed(hh)

    # 2) candidatas: precio <= 5.05 y qty >= 10, sin refractors/autos caros
    TARGETS = ["Bowman Draft - [Base] #BD-59", "Bowman In Action #BIA-10",
               "USA Baseball Stars & Stripes - [Base] #55", "Chrome Prospects - Mega Box Mojo #BCP-145"]
    cand = []
    for it in items:
        if it["precio"] is None:
            continue
        for t in TARGETS:
            if t in it["titulo"]:
                cand.append(it)
                break
    print(json.dumps({"candidatas_encontradas": len(cand)}, ensure_ascii=False), flush=True)

    # 3) escanear cada una con espaciado
    for it in cand:
        time.sleep(random.uniform(30, 45))
        r = escanear_carta(it["titulo"][:60], it["url"])
        r["precio_feed"] = it["precio"]
        r["qty_feed"] = it["qty"]
        print(json.dumps(r, ensure_ascii=False), flush=True)
    print("OK", flush=True)

if __name__ == "__main__":
    main()
