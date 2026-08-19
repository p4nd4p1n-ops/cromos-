#!/usr/bin/env python3
"""tendencia_precio_liquidez.py — calcula tendencia de PRECIO y de LIQUIDEZ
a partir de un historial de ventas (fecha, precio).

Uso: tendencia_precio_liquidez.py <csv o md con ventas> [precio_actual]

Tendencia PRECIO:
- media de las últimas 10 ventas vs las 10 anteriores (o 5v5 si hay poco)
- pendiente simple sobre precios ordenados por fecha
Tendencia LIQUIDEZ:
- ventas por semana en las últimas 4 semanas (ventas 7d, 14d, 21d, 28d)
- pendiente de la serie semanal
Salida: resumen legible.
"""
import sys, re, datetime, json

def parse_md(path):
    """Parsea el markdown de historial: líneas tipo '| Aug 9, 2026 3:01 PM | $6.00 | Offer |'.
    Devuelve ventas (fecha, precio, tipo, bloque) ya filtradas:
    FUERA: X Item Offer (bulk), PSA/GEM MT/graduadas, EX to NM y rarezas.
    """
    ventas = []
    lines = open(path, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"\|\s*([A-Z][a-z]{2} \d{1,2}, \d{4})", lines[i])
        if m:
            bloque = lines[i] + " " + (lines[i + 1] if i + 1 < len(lines) else "")
            pm = re.search(r"\*\*\$([\d,]+\.\d{2})\*\*", bloque)
            if pm:
                try:
                    fecha = datetime.datetime.strptime(m.group(1), "%b %d, %Y").date()
                    precio = float(pm.group(1).replace(",", ""))
                    tm = re.search(r"\*\*\$[\d,]+\.\d{2}\*\*\s*\|\s*([^|\n]+?)\s*\|", bloque)
                    tipo = tm.group(1).strip() if tm else "?"
                    bloque_low = bloque.lower()
                    # FILTRO (regla de Pin 10/08/2026): bulk y cosas raras fuera de medias
                    if "item offer" in tipo.lower():
                        i += 1
                        continue
                    if any(k in bloque_low for k in
                           ["psa", "gem mt", "bgs", "sgc", "graded", "ex to nm",
                            "auto", "refractor", "parallel", "error"]):
                        i += 1
                        continue
                    ventas.append((fecha, precio, tipo, bloque[:80]))
                except ValueError:
                    pass
        i += 1
    return sorted(ventas)

def parse_csv(path):
    ventas = []
    for line in open(path, encoding="utf-8"):
        parts = line.strip().split(",")
        if len(parts) < 2:
            continue
        try:
            fecha = datetime.datetime.strptime(parts[0].strip(), "%Y-%m-%d").date()
            precio = float(parts[1].strip())
            ventas.append((fecha, precio))
        except ValueError:
            continue
    return sorted(ventas)

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
    return round(sum(1 for v in ordenada if v <= valor) / len(ordenada) * 100, 1)

def main():
    if len(sys.argv) < 2:
        print("uso: tendencia_precio_liquidez.py <archivo> [precio_actual]")
        return
    path = sys.argv[1]
    precio_actual = float(sys.argv[2]) if len(sys.argv) > 2 else None
    ventas = parse_md(path) if path.endswith(".md") else parse_csv(path)
    if not ventas:
        print("no se parsearon ventas")
        return
    precios = [p for _, p in ventas]
    hoy = datetime.date.today()

    print(f"Historial: {len(ventas)} ventas | {ventas[0][0]} → {ventas[-1][0]}\n")

    # --- LIQUIDEZ: ventas por semana (4 ventanas) ---
    print("LIQUIDEZ (ventas por ventana):")
    ventanas = {}
    for dias in (7, 14, 21, 28):
        n = sum(1 for f, _ in ventas if (hoy - f).days <= dias)
        ventanas[dias] = n
        print(f"  {dias:>2}d: {n} ventas")
    semanal = [ventanas[7], ventanas[14] - ventanas[7], ventanas[21] - ventanas[14], ventanas[28] - ventanas[21]]
    pend_liq = pendiente(semanal)
    if pend_liq > 0.5:
        tag_liq = "🔥 liquidez subiendo"
    elif pend_liq < -0.5:
        tag_liq = "❄️ liquidez cayendo"
    else:
        tag_liq = "➡️ liquidez estable"
    print(f"  pendiente semanal: {pend_liq:+.2f} → {tag_liq}")

    # --- PRECIO: media recientes vs anteriores ---
    print("\nPRECIO:")
    if len(precios) >= 10:
        recientes = precios[-10:]
        anteriores = precios[-20:-10]
        med_r = sum(recientes) / 10
        med_a = sum(anteriores) / 10 if anteriores else med_r
        pct = (med_r - med_a) / med_a * 100 if med_a else 0
        print(f"  media últimas 10 ventas: ${med_r:.2f} vs 10 anteriores: ${med_a:.2f} ({pct:+.1f}%)")
    elif len(precios) >= 6:
        recientes = precios[-5:]
        anteriores = precios[-10:-5]
        med_r = sum(recientes) / 5
        med_a = sum(anteriores) / 5 if anteriores else med_r
        pct = (med_r - med_a) / med_a * 100 if med_a else 0
        print(f"  media últimas 5 ventas: ${med_r:.2f} vs 5 anteriores: ${med_a:.2f} ({pct:+.1f}%)")
    else:
        med_r = sum(precios) / len(precios)
        pct = 0
        print(f"  media total: ${med_r:.2f} (pocos datos)")
    pend_pr = pendiente(precios[-10:]) if len(precios) >= 4 else 0
    if pend_pr > 0.15:
        tag_pr = "📈 precio subiendo"
    elif pend_pr < -0.15:
        tag_pr = "📉 precio cayendo"
    else:
        tag_pr = "➡️ precio plano"
    print(f"  pendiente precios: {pend_pr:+.2f} $/venta → {tag_pr}")

    # --- SALUD: percentil del precio actual ---
    if precio_actual:
        p = percentil(precios, precio_actual)
        print(f"\nSALUD: min muro ${precio_actual} → percentil {p} del historial de ventas")
        if p is not None:
            if p < 35:
                print("  → carta BARATA vs su historial (zona de compra)")
            elif p > 70:
                print("  → carta CARA vs su historial (zona de venta)")
            else:
                print("  → precio en zona media")

if __name__ == "__main__":
    main()
