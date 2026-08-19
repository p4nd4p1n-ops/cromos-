#!/usr/bin/env python3
"""muro_knueppel8.py — tabla de paralelos/vista principal del HTML fresco: precio por variante + filas grade."""
import re, html as h

html = open("/tmp/knueppel7.html").read()

# tabla de paralelos: buscar <table> con parallel rows
# estructura: <tr class="parallel"> ... <a title="[Base]" ...> ... <td class="displayprice">$X</td> <td class="qtyforsale">(N)</td>
par_rows = re.findall(r'<tr class="(?:parallel|grade)"[^>]*>(.*?)</tr>', html, re.S)
print("filas parallel/grade:", len(par_rows))

vistos = set()
for f in par_rows:
    tm = re.search(r'class="parallelname">([^<]+)</', f) or re.search(r'class="grade">([^<]+)</', f)
    pm = re.search(r'class="displayprice">.*?\$([\d,]+\.\d{2})', f, re.S)
    qm = re.search(r'class="qtyforsale">(.*?)</td>', f, re.S)
    nm = re.search(r'href="([^"]*)"', f)
    if not pm:
        continue
    nombre = tm.group(1).strip() if tm else (nm.group(1).split("/")[-1] if nm else "?")
    qraw = qm.group(1) if qm else ""
    qn = re.search(r'\((\d+)\)', qraw)
    qty = qn.group(1) if qn else "SUB/—"
    precio = pm.group(1)
    clave = (nombre, precio, qty)
    if clave in vistos:
        continue
    vistos.add(clave)
    print(f"  {nombre:30s} ${precio:>8s}  qty={qty}")

print("\n=== ¿aparece '3.49' en la página? ===")
for mm in list(re.finditer(r"3\.49", html))[:8]:
    s = max(0, mm.start() - 120)
    e = min(len(html), mm.start() + 120)
    print("  ...", re.sub(r"\s+", " ", html[s:e])[:260])

# ¿el precio del cuadro principal (grande)?
m = re.search(r'class="[^"]*price[^"]*"[^>]*>\s*\$([\d,]+\.\d{2})', html)
if m:
    print("\nprimer precio en página:", m.group(1))
