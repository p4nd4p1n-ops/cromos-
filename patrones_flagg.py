#!/usr/bin/env python3
"""patrones_flagg.py — tendencias y patrones del historial de Flagg Topps #201."""
import re, datetime, statistics
from collections import defaultdict

TXT = open('/tmp/historial-flagg-chrome.txt').read()
pat = re.compile(
    r"([A-Z][a-z]{2} \d{1,2}, \d{4})\s*(\d{1,2}:\d{2} [AP]M)?\s*(.*?)\s*\$([\d,]+\.\d{2})\s*"
    r"(Fixed Price|On Sale|Offer|\d+ Item Offer|Auction)?", re.S)
rows = []
for m in pat.finditer(TXT):
    try:
        fecha = datetime.datetime.strptime(m.group(1), "%b %d, %Y").date()
    except ValueError:
        continue
    rows.append({"fecha": fecha, "cond": (m.group(3) or "").strip(),
                 "precio": float(m.group(4).replace(",", "")), "tipo": (m.group(5) or "").strip(),
                 "hora": m.group(2) or ""})
EXCL = re.compile(r"PSA|BGS|CGC|EX to NM|Good to VG|Poor to Fair|scratched", re.I)
limpias = [r for r in rows if not EXCL.search(r["cond"]) and r["tipo"] != "Auction"
           and not (re.match(r"(\d+) Item Offer", r["tipo"]) and int(re.match(r"(\d+) Item Offer", r["tipo"]).group(1)) >= 10)]
vistos = set(); dedup = []
for r in sorted(limpias, key=lambda x: (x["fecha"], x["hora"])):
    k = (r["fecha"], r["hora"], r["precio"])
    if k in vistos: continue
    vistos.add(k); dedup.append(r)

# 1. Tendencia mensual (mediana y volumen)
meses = defaultdict(list)
for r in dedup:
    meses[r["fecha"].strftime("%Y-%m")].append(r["precio"])
print("=== TENDENCIA MENSUAL ===")
for k in sorted(meses):
    ps = meses[k]
    print(f"{k}: n={len(ps):3d} · mediana ${statistics.median(ps):.2f} · media ${statistics.mean(ps):.2f}")

# 2. Días de la semana con más ventas
dias = defaultdict(int)
for r in dedup:
    dias[r["fecha"].strftime("%A")] += 1
print("\n=== VENTAS POR DÍA DE SEMANA ===")
orden = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
for d in orden:
    print(f"{d}: {dias.get(d,0)}")

# 3. Evolución semanal reciente (últimas 12 semanas)
print("\n=== EVOLUCIÓN SEMANAL (12 últimas) ===")
hoy = datetime.date(2026, 8, 12)
semanas = defaultdict(list)
for r in dedup:
    delta = (hoy - r["fecha"]).days
    if 0 <= delta < 84:
        semanas[delta // 7].append(r["precio"])
for w in sorted(semanas):
    ps = semanas[w]
    print(f"hace {w*7}-{w*7+6}d: n={len(ps):3d} · mediana ${statistics.median(ps):.2f} · media ${statistics.mean(ps):.2f}")

# 4. Rango de horas con más ventas
horas = defaultdict(int)
for r in dedup:
    hm = re.match(r"(\d{1,2}):", r["hora"])
    if hm:
        h = int(hm.group(1)) % 12
        if "PM" in r["hora"]: h += 12
        horas[h] += 1
print("\n=== VENTAS POR HORA (UTC-4 aprox, hora COMC) ===")
for h in sorted(horas):
    if horas[h] >= 30:
        print(f"{h:02d}:00-{h:02d}:59: {horas[h]}")
