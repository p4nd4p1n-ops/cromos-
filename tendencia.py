#!/usr/bin/env python3
"""tendencia.py — calcula la tendencia de cada cromo a partir de su serie trimestral
(quarterly del sparkline, 16 trimestres = 4 años) y del historial de ventas scrapeado.

Salida por carta:
- tendencia DEMANDA: pendiente últimos 4 trimestres + % cambio → 🔥 subiendo / ❄️ enfriando / ➡️ estable
- salud PRECIO: percentil del precio actual (min muro) dentro de los precios de venta recientes
"""
import json, sys, datetime

def pendiente(ys):
    n = len(ys)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    den = sum((xs[i] - mx) ** 2 for i in range(n))
    return num / den if den else 0.0

def percentil(lista, valor):
    if not lista:
        return None
    ordenada = sorted(lista)
    menor = sum(1 for v in ordenada if v <= valor)
    return round(menor / len(ordenada) * 100, 1)

def clasificar(pend, pct):
    if pend > 1.2 or pct > 30:
        return "🔥 subiendo"
    if pend < -1.2 or pct < -25:
        return "❄️ enfriando"
    return "➡️ estable"

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/root/comc-data/muro-fino-ultimo.json"
    d = json.load(open(path))
    print(f"TENDENCIA por carta — scan {d.get('fecha', '?')}\n")
    for c in d.get("cartas", []):
        if "error" in c:
            print(f"{c['carta'][:30]:32} | ERROR {c['error']}")
            continue
        q = c.get("quarterly") or []
        sales = c.get("sales") or []
        precios_venta = [p for _, p in sales]
        min_actual = c.get("min")
        linea = f"{c['carta'][:30]:32}"
        if len(q) >= 4:
            ult4 = q[-4:]
            ant4 = q[-8:-4] if len(q) >= 8 else q[:4]
            pend = pendiente(ult4)
            pct = (ult4[-1] - ult4[0]) / ult4[0] * 100 if ult4[0] else 0
            pct_ant = (sum(ant4) / len(ant4)) if ant4 else 0
            cambio_vs_ant = (ult4[-1] - pct_ant) / pct_ant * 100 if pct_ant else 0
            tag = clasificar(pend, pct)
            linea += f"| vol 4T: {ult4} | pend {pend:+.2f} | {pct:+.0f}% | vs ant {cambio_vs_ant:+.0f}% | {tag}"
        else:
            linea += "| sin serie trimestral"
        if min_actual and precios_venta:
            p = percentil(precios_venta, min_actual)
            med = sum(precios_venta) / len(precios_venta)
            linea += f" | min ${min_actual} | P{'' if p is None else p} (media ventas ${med:.2f}, n={len(precios_venta)})"
        print(linea)

if __name__ == "__main__":
    main()
