#!/usr/bin/env python3
"""muro_knueppel6.py — busca '3.49' en el HTML fresco y extrae la tabla allsellers correcta."""
import re, html as h

html = open("/tmp/knueppel5.html").read()

print("=== CONTEXTOS '3.49' ===")
for mm in list(re.finditer(r"3\.49", html))[:6]:
    s = max(0, mm.start() - 250)
    e = min(len(html), mm.start() + 250)
    print(re.sub(r"\s+", " ", html[s:e]))
    print()

# extraer SOLO la tabla allsellers: buscar el ancla "All Sellers" y subir al <table>
i = html.find("All Sellers")
print("pos All Sellers:", i)
# buscar <table> antes de esa posición
j = html.rfind("<table", 0, i)
print("pos table:", j)
if j != -1:
    # fin de tabla
    fin = html.find("</table>", j)
    bloque = html[j:fin + 8]
    print("tabla len:", len(bloque))
    filas = re.findall(r'<tr[^>]*>(.*?)</tr>', bloque, re.S)
    print("filas en tabla:", len(filas))
    out = []
    for f in filas:
        sm = re.search(r'class="seller">\s*<a[^>]*>([^<]+)</a>', f)
        pm = re.search(r'class="displayprice">.*?\$([\d,]+\.\d{2})', f, re.S)
        qm = re.search(r'class="qtyforsale">(.*?)</td>', f, re.S)
        if not pm:
            continue
        precio = float(pm.group(1).replace(",", ""))
        seller = h.unescape(sm.group(1)).strip() if sm else "(all sellers)"
        qraw = qm.group(1) if qm else ""
        qn = re.search(r'\((\d+)\)', qraw)
        qty = int(qn.group(1)) if qn else None
        out.append((precio, seller, qty))
    print("\n=== TABLA ALLSELLERS REAL (primeros 15) ===")
    for p, s, q in out[:15]:
        print(f"  ${p:.2f} | {s:24s} | qty={q if q is not None else 'SUB/—'}")
    print("\nTOTAL filas:", len(out))
