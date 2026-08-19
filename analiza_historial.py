#!/usr/bin/env python3
"""analiza_historial.py <archivo> [nombre] — parsea historial pegado por Pin (formato COMC).
Mismo pipeline que Daniels: filtrar graduadas/EX/subastas/bulk → dedup → ventas 7d →
media últ.10/20 → outliers → P60-70 → oferta máx (P65 × 0.95 ÷ 1.10). 12/08/2026."""
import re, datetime, statistics, sys

TXT = open(sys.argv[1]).read()
NOMBRE = sys.argv[2] if len(sys.argv) > 2 else "?"

pat = re.compile(
    r"([A-Z][a-z]{2} \d{1,2}, \d{4})\s*"
    r"(\d{1,2}:\d{2} [AP]M)?\s*"
    r"(.*?)\s*\$([\d,]+\.\d{2})\s*"
    r"(Fixed Price|On Sale|Offer|\d+ Item Offer|Auction)?", re.S)

rows = []
for m in pat.finditer(TXT):
    fecha_s = m.group(1)
    hora = m.group(2) or ""
    cond = (m.group(3) or "").strip()
    precio = float(m.group(4).replace(",", ""))
    tipo = (m.group(5) or "").strip()
    try:
        fecha = datetime.datetime.strptime(fecha_s, "%b %d, %Y").date()
    except ValueError:
        continue
    rows.append({"fecha": fecha, "fecha_s": fecha_s, "hora": hora, "cond": cond,
                 "precio": precio, "tipo": tipo})

print(f"=== {NOMBRE} ===")
print(f"Total filas crudas: {len(rows)}")

EXCL = re.compile(r"PSA|BGS|CGC|EX to NM|Good to VG|scratched|condition", re.I)
limpias = []
for r in rows:
    if EXCL.search(r["cond"]):
        continue
    if r["tipo"] == "Auction":
        continue
    mm = re.match(r"(\d+) Item Offer", r["tipo"])
    if mm and int(mm.group(1)) >= 10:
        continue
    limpias.append(r)
print(f"Tras filtrar graduadas/subastas/bulk: {len(limpias)}")

vistos = set()
dedup = []
for r in sorted(limpias, key=lambda x: (x["fecha"], x["hora"])):
    k = (r["fecha"], r["hora"], r["precio"])
    if k in vistos:
        continue
    vistos.add(k)
    dedup.append(r)
print(f"Tras dedup: {len(dedup)}")

hoy = datetime.date(2026, 8, 12)
v7 = [r for r in dedup if 0 <= (hoy - r["fecha"]).days <= 7]
dias_distintos = sorted({r["fecha"] for r in v7})
print(f"\nVENTAS 7d: {len(v7)} en {len(dias_distintos)} días distintos ({[str(d) for d in dias_distintos]})")
for r in v7:
    print(f"  {r['fecha_s']} {r['hora']} ${r['precio']:.2f} {r['tipo']}")
vel = len(v7) / 7.0
print(f"vel_dia: {vel:.2f}")

N = 10 if vel > 1 else 20
ultimas = sorted(dedup, key=lambda x: (x["fecha"], x["hora"]))[-N:]
media_ult = statistics.mean(r["precio"] for r in ultimas)
print(f"\nÚLTIMAS {N} VENTAS: media {media_ult:.2f} (min {min(r['precio'] for r in ultimas):.2f} · max {max(r['precio'] for r in ultimas):.2f})")

precios = sorted(r["precio"] for r in dedup)
mediana = statistics.median(precios)
q1 = precios[len(precios)//4]
q3 = precios[3*len(precios)//4]
iqr = q3 - q1
out_sup = q3 + 1.5 * iqr
limpio_out = [r for r in dedup if r["precio"] <= out_sup]
outs = [r for r in dedup if r["precio"] > out_sup]
print(f"\nHistorial: mediana {mediana:.2f} · Q1 {q1:.2f} · Q3 {q3:.2f} · IQR {iqr:.2f} · outlier > {out_sup:.2f}")
print(f"Outliers descartados ({len(outs)}): " + ", ".join(f"${r['precio']:.2f} ({r['fecha_s']})" for r in outs))

precios_limpios = sorted(r["precio"] for r in limpio_out)
n = len(precios_limpios)
def pct(p):
    if not precios_limpios:
        return None
    return precios_limpios[min(n - 1, int(p / 100.0 * n))]
p60, p65, p70 = pct(60), pct(65), pct(70)
print(f"\nPercentiles historial limpio (n={n}): P60 {p60:.2f} · P65 {p65:.2f} · P70 {p70:.2f}")
oferta = p65 * 0.95 / 1.10
print(f"VentaEsperada (P65): {p65:.2f} → OFERTA máx = {p65:.2f} × 0.95 ÷ 1.10 = {oferta:.2f}")
print(f"RESUMEN: vel {vel:.2f} · media últ.{N} {media_ult:.2f} · P65 {p65:.2f} · oferta {oferta:.2f}")
