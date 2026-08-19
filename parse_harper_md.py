#!/usr/bin/env python3
"""Procesa historial de Harper en formato .md (tabla) — 11/08/2026."""
import re
from datetime import datetime

ventas = []
for line in open('historial-harper-chrome-2026-08-10.md'):
    m = re.match(r'\|\s*([A-Z][a-z]{2} \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M)\s*\|\s*\$([\d.]+)\s*\|\s*(.*?)\s*\|', line)
    if not m:
        continue
    fecha_s, precio, tipo = m.groups()
    tipo = tipo.strip().lower()
    if any(x in tipo for x in ['item offer', 'bulk', 'psa', 'cga', 'cgc', 'bgs', 'sgc', 'ex to nm', 'rare']):
        continue
    try:
        fecha = datetime.strptime(fecha_s, '%b %d, %Y %I:%M %p')
    except ValueError:
        continue
    ventas.append((fecha, float(precio)))

ventas = list(dict.fromkeys(ventas))
ventas.sort(key=lambda x: x[0])
print(f"Ventas limpias: {len(ventas)}")
print(f"Rango: {ventas[0][0].date()} → {ventas[-1][0].date()}")

# liquidez
hoy = datetime(2026, 8, 11)
v7 = sum(1 for f, p in ventas if (hoy - f).days <= 7)
v14 = sum(1 for f, p in ventas if (hoy - f).days <= 14)
v21 = sum(1 for f, p in ventas if (hoy - f).days <= 21)
v28 = sum(1 for f, p in ventas if (hoy - f).days <= 28)
print(f"7d: {v7} · 14d: {v14} · 21d: {v21} · 28d: {v28}")
print(f"vel_dia (7d): {v7/7:.2f}")

# precio
ult10 = ventas[-10:]
ant10 = ventas[-20:-10]
media10 = sum(p for _, p in ult10) / len(ult10)
media_ant10 = sum(p for _, p in ant10) / len(ant10)
print(f"Media últimas 10: ${media10:.2f} vs 10 anteriores: ${media_ant10:.2f} ({(media10-media_ant10)/media_ant10*100:+.1f}%)")

# percentil del min muro (7.00)
precios = sorted(p for _, p in ventas)
for muro in [7.00, 7.49]:
    pct = sum(1 for p in precios if p <= muro) / len(precios) * 100
    print(f"Percentil muro ${muro:.2f}: {pct:.1f}")

# ultimas 20
print("Últimas 20:", [f"${p:.2f}" for _, p in ventas[-20:]])
