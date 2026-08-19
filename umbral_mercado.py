#!/usr/bin/env python3
"""Umbral de liquidez RELATIVO AL MERCADO — analiza todos los historiales del inventario
y saca la distribución de ventas semanales del conjunto para definir el umbral de "despertar".
11/08/2026 — petición de Pin: definir cómo calcular el umbral respecto al mercado."""
import re, glob, os
from datetime import datetime, timedelta
from collections import Counter

# Todos los historiales del inventario
ARCHIVOS = {
    "Harper": "historial-harper-chrome-2026-08-10.md",   # formato tabla markdown
    "Flagg": "historial-flagg-chrome-2026-08-10.txt",
    "Knueppel": "historial-knueppel-chrome-2026-08-10.txt",
    "Edgecombe": "historial-edgecombe-chrome-2026-08-10.txt",
    "Bryant": "historial-bryant-chrome-2026-08-11.txt",
    "Castle": "historial-castle-chrome-2026-08-11.txt",
    "AceBailey": "historial-acebailey-chrome-2026-08-11.txt",
}

def parse_archivo(path):
    """Acepta formato de una línea y formato tabla markdown."""
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
        ventas.append((fecha, float(precio)))
    # dedup
    ventas = list(dict.fromkeys(ventas))
    ventas.sort(key=lambda x: x[0])
    return ventas

def inicio_semana(f):
    return f - timedelta(days=f.weekday())

print("=" * 70)
print("DISTRIBUCIÓN SEMANAL POR CARTA (para definir umbral relativo al mercado)")
print("=" * 70)

todas_semanas = []  # (carta, semana, n_ventas, n_dias)
for nombre, arch in ARCHIVOS.items():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), arch)
    if not os.path.exists(path):
        print(f"\n{nombre}: archivo no encontrado ({arch})")
        continue
    ventas = parse_archivo(path)
    if not ventas:
        print(f"\n{nombre}: sin ventas parseadas")
        continue
    semanas = Counter()
    dias_por_semana = {}
    for f, p in ventas:
        s = inicio_semana(f)
        semanas[s] += 1
        dias_por_semana.setdefault(s, set()).add(f.date())
    vals = sorted(semanas.values())
    mediana = vals[len(vals)//2]
    maximo = vals[-1]
    # últimas 4 semanas
    ult4 = sorted(semanas.keys())[-4:]
    ult4_str = ", ".join(f"{semanas[s]}v/{len(dias_por_semana[s])}d" for s in ult4)
    print(f"\n{nombre} ({len(ventas)} ventas, {len(semanas)} semanas):")
    print(f"  mediana {mediana}/semana · max {maximo}/semana · últimas 4: {ult4_str}")
    for s, n in semanas.items():
        todas_semanas.append((nombre, s, n, len(dias_por_semana[s])))

print("\n" + "=" * 70)
print("MERCADO COMPLETO (todas las semanas de todas las cartas)")
print("=" * 70)
vals_m = sorted(n for _, _, n, _ in todas_semanas)
n = len(vals_m)
def pct(p):
    return vals_m[min(n-1, int(p/100*n))]
print(f"Semanas totales: {n}")
print(f"  min {vals_m[0]} · P25 {pct(25)} · mediana {pct(50)} · P75 {pct(75)} · P90 {pct(90)} · max {vals_m[-1]}")
print(f"  Media: {sum(vals_m)/n:.2f}")

# Definir umbral: qué es "despertar" vs la distribución del mercado
print("\n=== DEFINICIÓN DEL UMBRAL (relativo al mercado) ===")
print(f"  Mediana del mercado: {pct(50)} ventas/semana")
print(f"  P75 del mercado: {pct(75)} ventas/semana")
print(f"  P90 del mercado: {pct(90)} ventas/semana")
print(f"  → Una carta 'despierta' cuando supera su propia mediana ×2 Y está en el P75+ del mercado")
