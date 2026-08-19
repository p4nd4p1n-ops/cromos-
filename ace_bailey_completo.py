#!/usr/bin/env python3
"""Ace Bailey completo — base + refractor + paralelas visibles (11/08/2026).
URLs verificadas del feed de esta mañana. Espaciado anti-rate-limit.
"""
import json, urllib.request, re, time, random, datetime, sys

sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

CARTAS = [
    ("Base #255.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2551/Ace_Bailey/31038642"),
    ("Refractor #255.1", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base_-_Refractor/2551/Ace_Bailey/31053400"),
]

def escanear(nombre, url):
    html = ms.get_html(url)
    if not html or len(html) < 2000:
        return {"carta": nombre, "error": "sin_html"}
    # Ventas 7d
    sales = [(f, float(p)) for f, p in re.findall(
        r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)]
    hoy = datetime.date.today()
    v7, v14, dias = 0, 0, set()
    for f, _ in sales:
        try:
            fd = datetime.datetime.strptime(f, "%b %d, %Y").date()
            if (hoy - fd).days <= 7:
                v7 += 1
                dias.add(fd)
            if (hoy - fd).days <= 14:
                v14 += 1
        except ValueError:
            pass
    # Muro activo (filtrar soldout y allsellers)
    precios = []
    vendedores = []
    for r in re.findall(r'<tr>(.*?)</tr>', html, re.S):
        if 'class="seller"' in r and 'displayprice' in r and 'soldout' not in r and 'allsellers' not in r:
            pm = re.search(r'displayprice.*?class="price">\$([\d.]+)', r, re.S)
            vm = re.search(r'/Users/([A-Za-z0-9_\-]+)', r)
            if pm:
                precios.append(float(pm.group(1)))
                vendedores.append(vm.group(1) if vm else '?')
    precios.sort()
    # Copias totales
    copias = 0
    m = re.search(r'class="allsellers"[^>]*>.*?qtyforsale[^>]*>\s*&nbsp;?\((\d+)\)', html, re.S)
    if m:
        copias = int(m.group(1))
    # Paralelas en sidebar
    paralelas = re.findall(r'\[Base\][^<]*|Prism[^<]*|Pulsar[^<]*|RayWave[^<]*|Red White[^<]*|Refractor[^<]*|Negative[^<]*|Aqua[^<]*|Green[^<]*|Blue[^<]*', html)
    unicas = []
    for p in paralelas:
        p = p.strip()
        if p and p not in unicas:
            unicas.append(p)
    return {
        "carta": nombre, "v7d": v7, "v14d": v14, "dias": len(dias),
        "vel": round(v7 / 7, 2), "copias": copias,
        "min": precios[0] if precios else None,
        "seg": precios[1] if len(precios) > 1 else None,
        "vendedores": vendedores[:6], "paralelas": unicas[:12]
    }

for i, (nombre, url) in enumerate(CARTAS):
    print(f"[{i+1}/{len(CARTAS)}] {nombre}...", flush=True)
    r = escanear(nombre, url)
    print(json.dumps(r, ensure_ascii=False, indent=2), flush=True)
    if i < len(CARTAS) - 1:
        espera = random.randint(35, 45)
        print(f"  esperando {espera}s...", flush=True)
        time.sleep(espera)
