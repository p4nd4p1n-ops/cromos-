#!/usr/bin/env python3
"""nba_liquidez.py — liquidez de candidatas NBA (ventas 7d, vel/día, copias, muro).
Espaciado 30-45s anti-rate-limit. Uso: nba_liquidez.py "Nombre|URL" ...
Basado en el patrón de rookies_bb_liquidez.py (feed→candidatas→scan).
"""
import json, urllib.request, re, time, random, datetime, sys, html as htmllib

sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

CARTAS = [
    ("Ace Bailey Chrome #255.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2551/Ace_Bailey/31038641"),
    ("Nikola Jokic Chrome #25.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/251/Nikola_Jokic/31038619"),
    ("LeBron James Chrome #127.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/1271/LeBron_James/31038611"),
    ("Wembanyama Chrome #221.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038632"),
    ("Will Richard Chrome #287", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/287/Will_Richard/31038657"),
    ("Anthony Edwards Chrome #151.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/1511/Anthony_Edwards/31038628"),
]

def escanear(nombre, url):
    html = ms.get_html(url)
    if not html or len(html) < 2000:
        return {"carta": nombre, "error": "sin_html"}
    # Ventas 7d desde la tabla de ventas
    sales = [(f, float(p)) for f, p in re.findall(
        r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)]
    hoy = datetime.date.today()
    v7 = 0
    dias = set()
    for f, _ in sales:
        try:
            fd = datetime.datetime.strptime(f, "%b %d, %Y").date()
            if (hoy - fd).days <= 7:
                v7 += 1
                dias.add(fd)
        except ValueError:
            pass
    # Copias totales (allsellers qty)
    copias = 0
    m = re.search(r'class="allsellers"[^>]*>.*?qtyforsale[^>]*>\s*&nbsp;?\((\d+)\)', html, re.S)
    if m:
        copias = int(m.group(1))
    # Muro: primer escalón real
    min_p = None
    seg_p = None
    filas = re.findall(r'<tr>(.*?)</tr>', html, re.S)
    precios = []
    for r in filas:
        if 'class="seller"' in r and 'displayprice' in r and 'soldout' not in r and 'allsellers' not in r:
            pm = re.search(r'displayprice.*?class="price">\$([\d.]+)', r, re.S)
            if pm:
                precios.append(float(pm.group(1)))
    precios.sort()
    if precios:
        min_p = precios[0]
        seg_p = precios[1] if len(precios) > 1 else None
    return {
        "carta": nombre, "v7d": v7, "dias": len(dias),
        "vel": round(v7 / 7, 2), "copias": copias,
        "min": min_p, "seg": seg_p
    }

resultados = []
for i, (nombre, url) in enumerate(CARTAS):
    print(f"[{i+1}/{len(CARTAS)}] {nombre}...", flush=True)
    r = escanear(nombre, url)
    resultados.append(r)
    print(f"    {r}", flush=True)
    if i < len(CARTAS) - 1:
        espera = random.randint(30, 45)
        print(f"    esperando {espera}s...", flush=True)
        time.sleep(espera)

print("\n=== RESUMEN LIQUIDEZ NBA ===")
orden = sorted(resultados, key=lambda x: x.get("vel", -1), reverse=True)
for r in orden:
    if "error" in r:
        print(f"  {r['carta']}: {r['error']}")
    else:
        print(f"  {r['carta']}: vel {r['vel']}/día · {r['v7d']}v/7d en {r['dias']} días · {r['copias']} copias · muro {r['min']}/{r['seg']}")
