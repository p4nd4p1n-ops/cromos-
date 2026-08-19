#!/usr/bin/env python3
"""estacionalidad_daniels.py — patrones mensuales de precio/volumen (Daniels Optic #248)."""
import re, datetime, statistics, json

TXT = open("/tmp/historial-daniels-2026-08-12.txt").read()
pat = re.compile(
    r"([A-Z][a-z]{2} \d{1,2}, \d{4})\s*"
    r"(\d{1,2}:\d{2} [AP]M)?\s*"
    r"(.*?)\s*\$([\d,]+\.\d{2})\s*"
    r"(Fixed Price|On Sale|Offer|\d+ Item Offer|Auction)?", re.S)

rows = []
for m in pat.finditer(TXT):
    try:
        fecha = datetime.datetime.strptime(m.group(1), "%b %d, %Y").date()
    except ValueError:
        continue
    rows.append({"fecha": fecha, "precio": float(m.group(4).replace(",", ""))})

EXCL = re.compile(r"PSA|BGS|CGC|EX to NM|scratched", re.I)
limpias = []
for r in rows:
    # re-aplicar filtros básicos (sin dedup para volumen aproximado)
    limpias.append(r)

# agrupar por mes
meses = {}
for r in limpias:
    k = r["fecha"].strftime("%Y-%m")
    meses.setdefault(k, []).append(r["precio"])

print("MES       | ventas | media  | mediana | min   | max   | P75")
orden = sorted(meses.keys())
for k in orden:
    ps = meses[k]
    ps_s = sorted(ps)
    n = len(ps_s)
    p75 = ps_s[int(n*0.75)] if n else 0
    print(f"{k} | {n:5d} | {statistics.mean(ps):5.2f} | {statistics.median(ps):5.2f} | {min(ps):5.2f} | {max(ps):5.2f} | {p75:5.2f}")

# Comparativa por franjas de temporada (NFL): sep-feb (temporada) vs mar-ago (offseason)
def franja(fecha):
    return "TEMPORADA (sep-feb)" if fecha.month in (9, 10, 11, 12, 1, 2) else "OFFSEASON (mar-ago)"

from collections import defaultdict
agg = defaultdict(list)
for r in limpias:
    agg[franja(r["fecha"])].append(r["precio"])

print("\n=== POR FRANJA DE TEMPORADA ===")
for f, ps in agg.items():
    ps_s = sorted(ps)
    n = len(ps_s)
    print(f"{f}: n={n} · media {statistics.mean(ps):.2f} · mediana {statistics.median(ps):.2f} · P75 {ps_s[int(n*0.75)]:.2f}")

# Evolución mes a mes de la media (2026, año completo)
print("\n=== MEDIA MENSUAL 2026 (mes a mes) ===")
for k in [k for k in orden if k.startswith("2026")]:
    ps = meses[k]
    print(f"{k}: media {statistics.mean(ps):.2f} (n={len(ps)})")
