#!/usr/bin/env python3
"""parse_historial.py — parsea historial crudo de COMC (formato pegado por Pin:
'Aug 9, 2026 10:18 AM $23.50 Fixed Price') y calcula tendencia precio+liquidez.

Filtros (regla de Pin 10/08/2026): FUERA ventas bulk (X Item Offer), graduadas
(PSA/CGC/BGS/SGC), EX to NM y rarezas. Solo cartas sueltas sin graduar.

Uso: parse_historial.py <archivo.txt> <precio_actual> <codigo>
"""
import re, sys, datetime, json

FILTROS_BLOQUE = ["item offer", "psa", "cgc", "bgs", "sgc", "graded", "gem mt",
                  "ex to nm", "ex-mt", "nm-mt", "mint", "auto", "refractor",
                  "parallel", "error", "numbered", "holo", "rookie redemption"]

def parse_crudo(path):
    """Devuelve lista de (fecha, precio, tipo) sin filtrar."""
    ventas = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # patrón: Mes Día, Año [hora] [condición] $precio tipo
        m = re.match(r"([A-Z][a-z]{2} \d{1,2}, \d{4})(?:\s+\d{1,2}:\d{2} [AP]M)?\s+(.*?)\s*\$([\d,]+\.\d{2})\s*([A-Za-z0-9][A-Za-z0-9 \-]*)", line)
        if not m:
            print("  (sin parsear):", line[:80], file=sys.stderr)
            continue
        try:
            fecha = datetime.datetime.strptime(m.group(1), "%b %d, %Y").date()
            precio = float(m.group(3).replace(",", ""))
            resto = m.group(2) + " " + m.group(4)
            ventas.append((fecha, precio, resto.strip()))
        except ValueError:
            continue
    return ventas

def filtrar(ventas):
    """Aplica filtros de Pin. Devuelve (limpias, descartadas)."""
    limpias, descartadas = [], []
    for fecha, precio, tipo in ventas:
        bloque = f"{tipo}".lower()
        if any(k in bloque for k in FILTROS_BLOQUE):
            descartadas.append((fecha, precio, tipo))
        else:
            limpias.append((fecha, precio, tipo))
    return limpias, descartadas

def deduplicar(ventas):
    """Elimina duplicados exactos (fecha+precio+tipo) — típico de pegados con
    bloques repetidos. Mantiene 1 por entrada única."""
    vistos = set()
    unicas = []
    for v in ventas:
        clave = (v[0], round(v[1], 2), v[2])
        if clave not in vistos:
            vistos.add(clave)
            unicas.append(v)
    return unicas

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
    path, precio_actual, codigo = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    ventas = parse_crudo(path)
    ventas = deduplicar(ventas)
    limpias, descartadas = filtrar(ventas)
    limpias.sort(key=lambda v: v[0])  # orden cronológico: las últimas = las más recientes
    print(f"{codigo} — {path.split('/')[-1]}")
    print(f"Ventas totales: {len(ventas)} | limpias: {len(limpias)} | descartadas: {len(descartadas)}")
    if descartadas:
        print("  descartadas ej.:", [(f"{f} ${p} {t}") for f, p, t in descartadas[:5]])

    hoy = datetime.date.today()
    precios = [p for _, p, _ in limpias]
    print(f"\nRango: {limpias[0][0]} → {limpias[-1][0]}")
    if not limpias:
        return

    # LIQUIDEZ
    print("\nLIQUIDEZ:")
    sem = []
    for dias in (7, 14, 21, 28):
        n = sum(1 for f, _, _ in limpias if (hoy - f).days <= dias)
        sem.append(n)
        print(f"  {dias:>2}d: {n} ventas")
    # ventanas semanales individuales, de ANTIGUA a RECIENTE (orden cronológico)
    semanal = [sem[3] - sem[2], sem[2] - sem[1], sem[1] - sem[0], sem[0]]
    print(f"  ventas/semana (antigua→reciente): {semanal}")
    pend_liq = pendiente(semanal)
    tag_liq = "🔥 subiendo" if pend_liq > 0.5 else ("❄️ cayendo" if pend_liq < -0.5 else "➡️ estable")
    print(f"  pendiente semanal: {pend_liq:+.2f} → {tag_liq}")

    # PRECIO
    print("\nPRECIO:")
    if len(precios) >= 10:
        r, a = precios[-10:], precios[-20:-10]
        mr, ma = sum(r)/10, sum(a)/10
        pct = (mr - ma) / ma * 100 if ma else 0
        print(f"  media últimas 10: ${mr:.2f} vs 10 anteriores: ${ma:.2f} ({pct:+.1f}%)")
    elif len(precios) >= 6:
        r, a = precios[-5:], precios[-10:-5]
        mr, ma = sum(r)/5, sum(a)/5
        pct = (mr - ma) / ma * 100 if ma else 0
        print(f"  media últimas 5: ${mr:.2f} vs 5 anteriores: ${ma:.2f} ({pct:+.1f}%)")
    else:
        mr, pct = sum(precios)/len(precios), 0
        print(f"  media total: ${mr:.2f}")
    pend_pr = pendiente(precios[-10:]) if len(precios) >= 4 else 0
    tag_pr = "📈 subiendo" if pend_pr > 0.15 else ("📉 cayendo" if pend_pr < -0.15 else "➡️ plano")
    print(f"  pendiente precios: {pend_pr:+.2f} $/venta → {tag_pr}")

    # SALUD
    p = percentil(precios, precio_actual)
    print(f"\nSALUD: min muro ${precio_actual} → percentil {p} del historial")
    if p is not None:
        if p < 35: print("  → BARATA vs historial (zona compra)")
        elif p > 70: print("  → CARA vs historial (zona venta)")
        else: print("  → zona media")

    # salida JSON para la hoja
    out = {"codigo": codigo, "ventas": len(limpias), "descartadas": len(descartadas),
           "media_semana": round(mr, 2), "percentil": p,
           "vel_dia": round(sem[0]/7, 3), "v7d": sem[0],
           "media_10": round(mr, 2) if len(precios) >= 10 else None,
           "media_ant10": round(ma, 2) if len(precios) >= 10 else None,
           "pct_cambio": round(pct, 1), "tag_precio": tag_pr, "tag_liquidez": tag_liq}
    print("\nJSON:", json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
