#!/usr/bin/env python3
"""Precio objetivo de venta (Listing) para Edgecombe — reglas del sistema 11/08/2026.
Ventana: vel_dia ≤1 → últimas 20 ventas. Outliers fuera. Oferta = VentaEsperada×0.95/1.10.
"""
import re, sys
from datetime import datetime

path = sys.argv[1] if len(sys.argv) > 1 else 'historial-edgecombe-chrome-2026-08-10.txt'
vel = float(sys.argv[2]) if len(sys.argv) > 2 else 0.857

ventas = []
for line in open(path):
    m = re.match(r'^([A-Z][a-z]{2} \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M)\s+\$([\d.]+)\s+(.*)$', line.strip())
    if not m:
        continue
    fecha_s, precio, tipo = m.groups()
    tipo = tipo.strip().lower()
    # descartar bulk/graduadas/EX-NM/rarezas (mismo criterio que parse_historial.py)
    if any(x in tipo for x in ['item offer', 'bulk', 'psa', 'cga', 'cgc', 'bgs', 'sgc', 'ex to nm', 'rare']):
        continue
    try:
        fecha = datetime.strptime(fecha_s, '%b %d, %Y %I:%M %p')
    except ValueError:
        continue
    ventas.append((fecha, float(precio)))

# dedup (fecha+precio+tipo)
ventas = list(dict.fromkeys(ventas))
ventas.sort(key=lambda x: x[0])

n = 20 if vel <= 1 else 10
ultimas = ventas[-n:]
precios = sorted(p[1] for p in ultimas)
def pct(p):
    i = min(len(precios)-1, int(p/100*len(precios)))
    return precios[i]

print(f"Ventas limpias: {len(ventas)} | ventana {n} ({ultimas[0][0].date()} → {ultimas[-1][0].date()})")
print(f"Media: ${sum(p[1] for p in ultimas)/n:.2f}")
print(f"P50 ${pct(50):.2f} | P60 ${pct(60):.2f} | P65 ${pct(65):.2f} | P70 ${pct(70):.2f} | P75 ${pct(75):.2f}")
print(f"Min ${min(p[1] for p in ultimas):.2f} | Max ${max(p[1] for p in ultimas):.2f}")
print(f"Últimas {n}:", [f"${p[1]:.2f}" for p in ultimas])
