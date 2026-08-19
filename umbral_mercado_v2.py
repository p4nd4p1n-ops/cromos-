#!/usr/bin/env python3
"""Umbral de liquidez CORREGIDO — métrica vel/día (como la hoja) y semanas vacías contadas.
11/08/2026 — corrección de la inconsistencia señalada por Pin.
"""
import re, os
from datetime import datetime, timedelta
from collections import Counter

ARCHIVOS = {
    "Harper": "historial-harper-chrome-2026-08-10.md",
    "Flagg": "historial-flagg-chrome-2026-08-10.txt",
    "Knueppel": "historial-knueppel-chrome-2026-08-10.txt",
    "Edgecombe": "historial-edgecombe-chrome-2026-08-10.txt",
    "Bryant": "historial-bryant-chrome-2026-08-11.txt",
    "Castle": "historial-castle-chrome-2026-08-11.txt",
    "AceBailey": "historial-acebailey-chrome-2026-08-11.txt",
}

HOY = datetime(2026, 8, 11)

def parse_archivo(path):
    ventas = []
    for line in open(path):
        m = re.match(r'^\|?\s*([A-Z][a-z]{2} \d{1,2}, \d{4} \d{1,2}:\d{2} [AP]M)\s*\|?\s*\$([\d.]+)\s*\|?\s*(.*?)\s*\|?$', line.strip())
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
        ventas.append(fecha)
    ventas = sorted(set(ventas))
    return ventas

def inicio_semana(f):
    return (f - timedelta(days=f.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

print("=" * 70)
print("VEL/DÍA ACTUAL POR CARTA (métrica de la hoja: ventas 7d ÷ 7)")
print("=" * 70)

vels_actuales = []
for nombre, arch in ARCHIVOS.items():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), arch)
    if not os.path.exists(path):
        continue
    fechas = parse_archivo(path)
    if not fechas:
        continue
    v7 = sum(1 for f in fechas if (HOY - f).days <= 7)
    v14 = sum(1 for f in fechas if (HOY - f).days <= 14)
    vel_dia = v7 / 7
    vels_actuales.append((nombre, vel_dia, v7, v14))
    print(f"  {nombre:<10} vel/día {vel_dia:.2f} (v7d {v7} · v14d {v14})")

print("\n" + "=" * 70)
print("DISTRIBUCIÓN SEMANAL CON SEMANAS VACÍAS (corregido)")
print("=" * 70)

todas_semanas = []  # valores de ventas POR SEMANA, incluyendo 0s
for nombre, arch in ARCHIVOS.items():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), arch)
    if not os.path.exists(path):
        continue
    fechas = parse_archivo(path)
    if not fechas:
        continue
    # rango de semanas desde la primera venta hasta HOY
    primera = min(fechas)
    semana_ini = inicio_semana(primera)
    semana_hoy = inicio_semana(HOY)
    n_semanas = ((semana_hoy - semana_ini).days // 7) + 1
    # ventas por semana (con 0s)
    ventas_por_semana = Counter(inicio_semana(f) for f in fechas)
    serie = [ventas_por_semana.get(semana_ini + timedelta(weeks=i), 0) for i in range(n_semanas)]
    todas_semanas.extend(serie)
    # últimas 8 semanas
    print(f"  {nombre:<10} últimas 8 sem: {serie[-8:]}")

vals = sorted(todas_semanas)
n = len(vals)
def pct(p):
    return vals[min(n-1, int(p/100*n))]
print(f"\nSemanas totales (con vacías): {n}")
print(f"  min {vals[0]} · P25 {pct(25)} · mediana {pct(50)} · P75 {pct(75)} · P90 {pct(90)} · P95 {pct(95)} · max {vals[-1]}")
print(f"  Media: {sum(vals)/n:.2f}")

# Convertir a vel/día: ventas/semana ÷ 7
print("\n=== UMBRAL EN MÉTRICA DE LA HOJA (vel/día) ===")
for label, p in [("P75", 75), ("P90", 90), ("P95", 95)]:
    v = pct(p)
    print(f"  {label} mercado: {v} ventas/semana = vel/día {v/7:.2f}")
print(f"\n  → Umbral propuesto: el vel/día del P90 del mercado (top 10%)")
