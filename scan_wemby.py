#!/usr/bin/env python3
"""Scan Wembanyama Chrome #221.1 (TC25-2211-B) — URL del punto de mira (31038608). 11/08/2026."""
import json, re, datetime, sys

sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038608"

html = ms.get_html(URL)
if not html or len(html) < 2000:
    print("SIN HTML")
    sys.exit(1)

open("/tmp/wemby.html", "w").write(html)

# Ventas 7d/14d
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

# Muro activo
precios, vendedores = [], []
for r in re.findall(r'<tr>(.*?)</tr>', html, re.S):
    if 'class="seller"' in r and 'displayprice' in r and 'soldout' not in r and 'allsellers' not in r:
        pm = re.search(r'displayprice.*?class="price">\$([\d.]+)', r, re.S)
        vm = re.search(r'/Users/([A-Za-z0-9_\-]+)', r)
        if pm:
            precios.append(float(pm.group(1)))
            vendedores.append(vm.group(1) if vm else '?')
precios.sort()

copias = 0
m = re.search(r'class="allsellers"[^>]*>.*?qtyforsale[^>]*>\s*&nbsp;?\((\d+)\)', html, re.S)
if m:
    copias = int(m.group(1))

print(f"WEMBY Chrome #221.1 (TC25-2211-B, 31038608)")
print(f"  Ventas: {v7} en 7d ({len(dias)} días) · {v14} en 14d · vel {v7/7:.2f}/día")
print(f"  Copias: {copias}")
print(f"  Muro (activo): {precios[:6]}")
print(f"  Vendedores: {vendedores[:6]}")
print(f"  Últimas ventas: {[f'${p:.2f}' for _, p in sales[:10]]}")
