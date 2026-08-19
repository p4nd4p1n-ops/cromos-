#!/usr/bin/env python3
"""Escaneo de candidatas para el punto de mira — filtro M-010 (vel/sem ≥13 + gap ≥5.3%).
9 candidatas base puras del feed 11/08. Espaciado 35-45s anti-rate-limit.
"""
import json, re, datetime, time, random, sys

sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

CANDIDATAS = [
    ("Will Richard #287", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/287/Will_Richard/31038675"),
    ("Nikola Jokic #25.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/251/Nikola_Jokic/31038410"),
    ("Anthony Edwards #151.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/1511/Anthony_Edwards/31038537"),
    ("Magic Johnson #244", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/244/Magic_Johnson/31038631"),
    ("Hugo Gonzalez #278.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2781/Hugo_Gonzalez/31038666"),
    ("Shaquille O'Neal #242", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/242/Shaquille_ONeal/31038629"),
    ("LeBron James #127.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/1271/LeBron_James/31038513"),
    ("Kevin Durant #155.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/1551/Kevin_Durant/31038541"),
    ("Collin Murray-Boyles #259.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2591/Collin_Murray-Boyles/31038647"),
]

def escanear(nombre, url):
    html = ms.get_html(url)
    if not html or len(html) < 2000:
        return {"carta": nombre, "error": "sin_html"}
    # Ventas 7d
    sales = [(f, float(p)) for f, p in re.findall(
        r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)]
    hoy = datetime.date.today()
    v7, dias = 0, set()
    for f, _ in sales:
        try:
            fd = datetime.datetime.strptime(f, "%b %d, %Y").date()
            if (hoy - fd).days <= 7:
                v7 += 1
                dias.add(fd)
        except ValueError:
            pass
    # Muro activo
    precios = []
    for r in re.findall(r'<tr>(.*?)</tr>', html, re.S):
        if 'class="seller"' in r and 'displayprice' in r and 'soldout' not in r and 'allsellers' not in r:
            pm = re.search(r'displayprice.*?class="price">\$([\d.]+)', r, re.S)
            if pm:
                precios.append(float(pm.group(1)))
    precios.sort()
    min_p = precios[0] if precios else None
    seg_p = precios[1] if len(precios) > 1 else None
    gap = ((seg_p - min_p) / min_p * 100) if min_p and seg_p else 0
    copias = 0
    m = re.search(r'class="allsellers"[^>]*>.*?qtyforsale[^>]*>\s*&nbsp;?\((\d+)\)', html, re.S)
    if m:
        copias = int(m.group(1))
    return {
        "carta": nombre, "vel_sem": v7, "dias": len(dias),
        "min": min_p, "seg": seg_p, "gap": round(gap, 1), "copias": copias
    }

resultados = []
for i, (nombre, url) in enumerate(CANDIDATAS):
    print(f"[{i+1}/{len(CANDIDATAS)}] {nombre}...", flush=True)
    r = escanear(nombre, url)
    resultados.append(r)
    print(f"    {r}", flush=True)
    if i < len(CANDIDATAS) - 1:
        espera = random.randint(35, 45)
        print(f"    esperando {espera}s...", flush=True)
        time.sleep(espera)

print("\n=== FILTRO M-010 (vel/sem ≥ 13 + gap ≥ 5.3%) ===")
for r in sorted(resultados, key=lambda x: x.get("vel_sem", -1), reverse=True):
    if "error" in r:
        print(f"  {r['carta']}: {r['error']}")
        continue
    ok_liq = r["vel_sem"] >= 13
    ok_gap = r["gap"] >= 5.3
    estado = "✅ PASA" if ok_liq and ok_gap else ("⏳ solo liq" if ok_liq else ("🟡 solo gap" if ok_gap else "❌"))
    print(f"  {estado} | {r['carta']:<22} vel/sem {r['vel_sem']:>3} ({r['dias']}d) | muro {r['min']}/{r['seg']} | gap {r['gap']}% | {r['copias']} copias")
