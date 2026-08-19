#!/usr/bin/env python3
"""analyze_top50.py — resumen + informe del escaneo top-50 de Topps Chrome Base 2025-26."""
import json, datetime, sys

DATA_DIR = "/root/comc-data"
f = f"{DATA_DIR}/scan-top50-2026-08-07.json"
d = json.load(open(f))
print("TOTAL:", len(d))
if d:
    print("CAMPOS:", sorted(d[0].keys()))

# tabla ordenada por ventas 7d
def v(r, k):
    x = r.get(k)
    return x if isinstance(x, (int, float)) else 0.0

print("\n=== ORDENADO POR VENTAS 7D ===")
for r in sorted(d, key=lambda x: v(x, "ventas_7d"), reverse=True):
    print(f"{r['nombre']:24s} v7d={v(r,'ventas_7d'):6.1f} pct={r.get('pct')} gap={r.get('gap')} obj={r.get('objetivo')} srp={r.get('srp')} sp={r.get('es_sp')}")

# oportunidades: liquidez alta + gap positivo
print("\n=== TOP OPORTUNIDADES (ventas_7d>=10, gap>0) ===")
for r in sorted([x for x in d if v(x, "ventas_7d") >= 10 and v(x, "gap") and v(x, "gap") > 0],
                key=lambda x: v(x, "ventas_7d") * (v(x, "gap") or 0), reverse=True):
    print(f"{r['nombre']:24s} v7d={v(r,'ventas_7d'):6.1f} gap={r.get('gap')} obj={r.get('objetivo')}")

# sin datos
print("\n=== SIN VENTAS (v7d=0) ===")
zero = [r["nombre"] for r in d if v(r, "ventas_7d") == 0]
print(len(zero), zero)
