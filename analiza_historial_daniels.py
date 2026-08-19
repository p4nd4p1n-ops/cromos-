#!/usr/bin/env python3
"""analiza_historial_daniels.py — parsea el historial pegado por Pin (Daniels Optic #248)."""
import re, datetime, statistics, json

TXT = open("/tmp/historial-daniels-2026-08-12.txt").read()

# Patrón: fecha, hora, [condición], $precio, tipo
pat = re.compile(
    r"([A-Z][a-z]{2} \d{1,2}, \d{4})\s*"
    r"(\d{1,2}:\d{2} [AP]M)?\s*"
    r"(.*?)\s*\$([\d,]+\.\d{2})\s*"
    r"(Fixed Price|On Sale|Offer|\d+ Item Offer|Auction)?",
    re.S)

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

print(f"Total filas crudas: {len(rows)}")

# Filtros
EXCL = re.compile(r"PSA|BGS|CGC|EX to NM|scratched|condition", re.I)
limpias = []
for r in rows:
    if EXCL.search(r["cond"]):
        continue
    if r["tipo"] == "Auction":
        continue
    # bulk item offers (N>=10)
    mm = re.match(r"(\d+) Item Offer", r["tipo"])
    if mm and int(mm.group(1)) >= 10:
        continue
    limpias.append(r)

print(f"Tras filtrar graduadas/subastas/bulk: {len(limpias)}")

# Dedup por (fecha, hora, precio)
vistos = set()
dedup = []
for r in sorted(limpias, key=lambda x: (x["fecha"], x["hora"])):
    k = (r["fecha"], r["hora"], r["precio"])
    if k in vistos:
        continue
    vistos.add(k)
    dedup.append(r)

print(f"Tras dedup: {len(dedup)}")

# Ventas 7d (hoy = 12/08/2026, ventana 05-11)
hoy = datetime.date(2026, 8, 12)
v7 = [r for r in dedup if (hoy - r["fecha"]).days <= 7 and r["fecha"] <= hoy]
dias_distintos = sorted({r["fecha"] for r in v7})
print(f"\nVENTAS 7d: {len(v7)} en {len(dias_distintos)} días distintos ({dias_distintos})")
for r in v7:
    print(f"  {r['fecha_s']} {r['hora']} ${r['precio']:.2f} {r['tipo']}")

vel = len(v7) / 7.0
print(f"vel_dia: {vel:.2f}")

# Últimas N (regla: vel>1 → 10; si no → 20)
N = 10 if vel > 1 else 20
ultimas = sorted(dedup, key=lambda x: (x["fecha"], x["hora"]))[-N:]
print(f"\nÚLTIMAS {N} VENTAS (regla ventana):")
for r in ultimas:
    print(f"  {r['fecha_s']} ${r['precio']:.2f} {r['tipo']}")
media_ult = statistics.mean(r["precio"] for r in ultimas)
print(f"media últ.{N}: {media_ult:.2f}")

# Outliers en TODO el historial limpio (para percentiles)
precios = sorted(r["precio"] for r in dedup)
mediana = statistics.median(precios)
q1 = precios[len(precios)//4]
q3 = precios[3*len(precios)//4]
iqr = q3 - q1
out_sup = q3 + 1.5 * iqr
limpio_out = [r for r in dedup if r["precio"] <= out_sup]
print(f"\nHistorial: mediana {mediana:.2f} · Q1 {q1:.2f} · Q3 {q3:.2f} · IQR {iqr:.2f}")
print(f"Outlier > {out_sup:.2f}: {sum(1 for r in dedup if r['precio'] > out_sup)} ventas descartadas")
for r in dedup:
    if r["precio"] > out_sup:
        print(f"  OUT: {r['fecha_s']} ${r['precio']:.2f} {r['tipo']} {r['cond']}")

precios_limpios = sorted(r["precio"] for r in limpio_out)
n = len(precios_limpios)
def pct(p):
    if not precios_limpios:
        return None
    idx = min(n - 1, int(p / 100.0 * n))
    return precios_limpios[idx]
p60, p65, p70 = pct(60), pct(65), pct(70)
print(f"\nPercentiles historial limpio (n={n}): P60 {p60:.2f} · P65 {p65:.2f} · P70 {p70:.2f}")
print(f"Media últ.10: {statistics.mean(r['precio'] for r in sorted(dedup, key=lambda x:(x['fecha'],x['hora']))[-10:]):.2f}")

# Oferta = VentaEsperada (P60-70) × 0.95 / 1.10
venta_esp = p65
oferta = venta_esp * 0.95 / 1.10
print(f"\nVentaEsperada (P65): {venta_esp:.2f}")
print(f"OFERTA = {venta_esp:.2f} × 0.95 ÷ 1.10 = {oferta:.2f}")
print(f"Margen si compro a {oferta:.2f} y vendo a muro 1º ${sorted([r['precio'] for r in v7]) and ''} (gap 7.9%): venta mínima para +10% = {oferta*1.10/0.95:.2f}")
