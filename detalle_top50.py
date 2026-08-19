#!/usr/bin/env python3
"""detalle_top50.py — tabla completa + análisis de oportunidades para el informe."""
import json

d = json.load(open("/root/comc-data/scan-top50-2026-08-07.json"))

def v(r, k):
    x = r.get(k)
    return x if isinstance(x, (int, float)) else 0.0

print("=== TABLA COMPLETA (min / seg / gap% / copias / ventas_7d) ===")
for r in sorted(d, key=lambda x: v(x, "ventas_7d"), reverse=True):
    print(f"{r['nombre']:24s} min={v(r,'min'):7.2f} seg={v(r,'seg'):7.2f} gap={v(r,'gap'):5.1f}% copias={v(r,'copias'):3.0f} v7d={v(r,'ventas_7d'):5.1f} vel={v(r,'vel_dia'):5.2f} inv={r.get('dias_inv')}")

print("\n=== CON VENTAS 7D > 0 (detalle ventas) ===")
for r in sorted([x for x in d if v(x, "ventas_7d") > 0], key=lambda x: v(x, "ventas_7d"), reverse=True):
    print(f"\n--- {r['nombre']} ---")
    print(f"  min={v(r,'min')} seg={v(r,'seg')} gap={v(r,'gap')}% copias={v(r,'copias')} n_min={r.get('n_min')} n_cerca={r.get('n_cerca')}")
    print(f"  vel_dia={r.get('vel_dia')} dias_inv={r.get('dias_inv')} turnover={r.get('turnover')}")
    print(f"  num={r.get('num')} sp={r.get('es_sp')}")
    print(f"  path={r.get('path')}")
    print(f"  sales={r.get('sales')}")

print("\n=== RESUMEN ===")
con = [r for r in d if v(r, "ventas_7d") > 0]
print(f"total={len(d)} con_ventas={len(con)} sin_ventas={len(d)-len(con)}")
print(f"suma ventas 7d = {sum(v(r,'ventas_7d') for r in d):.0f}")
