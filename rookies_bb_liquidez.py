#!/usr/bin/env python3
"""rookies_bb_liquidez.py — liquidez del grupo de rookies MLB 2026.
Para cada jugador: feed (patrón URL de Pin) → candidatas (≤$5.05, ≥10 copias)
→ escanear cada candidata (ventas 7d, vel/día, copias, total histórico).
Espaciado 30-45s anti-rate-limit. Uso: rookies_bb_liquidez.py "Nombre" "Nombre2" ...
"""
import json, urllib.request, re, time, random, sys, datetime, html as htmllib, os

sys.path.insert(0, "/root/comc-scripts")
import player_scan as ps
import muro_scan as ms

def escanear_carta(nombre, url):
    html = ms.get_html(url)
    if not html:
        return {"carta": nombre, "error": "sin_html"}
    sales = [(f, float(p)) for f, p in re.findall(
        r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)]
    hoy = datetime.date.today()
    v7 = 0
    for f, _ in sales:
        try:
            if (hoy - datetime.datetime.strptime(f, "%b %d, %Y").date()).days <= 7:
                v7 += 1
        except ValueError:
            pass
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

def feed_url_pin(jugador):
    import urllib.parse
    return "https://www.comc.com/SearchFeed.aspx?SportID=0&Search=" + urllib.parse.quote(jugador) + "&Sort%3dr"

def main():
    jugadores = sys.argv[1:]
    if not jugadores:
        print("uso: rookies_bb_liquidez.py \"Nombre\" ...")
        return
    try:
        ms.fs({"cmd": "sessions.destroy", "session": "ghost"}, timeout=30000)
    except Exception:
        pass
    time.sleep(3)

    for jugador in jugadores:
        print(json.dumps({"jugador": jugador}, ensure_ascii=False), flush=True)
        time.sleep(random.uniform(25, 40))
        hh = ps.get_feed(feed_url_pin(jugador))
        if not hh:
            print(json.dumps({"jugador": jugador, "error": "feed sin_html"}, ensure_ascii=False), flush=True)
            continue
        items = ps.parse_feed(hh)
        # candidatas: precio <= 5.05, qty >= 10, sin refractors/autos/paralelas caras
        cand = []
        for it in items:
            if it["precio"] is None or it["precio"] > 5.05:
                continue
            if (it["qty"] or 0) < 10:
                continue
            t = it["titulo"].lower()
            if any(k in t for k in ["refractor", "prizm", "auto", "autograph", "parallel",
                                    "mojo", "lava", "lazer", "aqua", "reptilian", "x-fractor",
                                    "sapphire", "hobby", "sparkle", "fuchsia", "wave"]):
                continue
            cand.append(it)
        print(json.dumps({"jugador": jugador, "candidatas": len(cand)}, ensure_ascii=False), flush=True)
        if not cand:
            continue
        # escanear hasta 4 candidatas por jugador (top por precio)
        cand.sort(key=lambda x: x["precio"])
        for it in cand[:4]:
            time.sleep(random.uniform(30, 45))
            r = escanear_carta(it["titulo"][:60], it["url"])
            r["precio_feed"] = it["precio"]
            r["qty_feed"] = it["qty"]
            print(json.dumps(r, ensure_ascii=False), flush=True)
    print("OK", flush=True)

if __name__ == "__main__":
    main()
