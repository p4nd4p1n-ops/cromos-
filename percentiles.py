#!/usr/bin/env python3
"""Percentiles de un historial de ventas de COMC.

  percentiles.py ARCHIVO [coste]

Separa crudas de gradadas, excluye lotes, y da distribucion y tendencia.
Si le pasas el coste, calcula tu percentil y el del break-even.
"""
import sys
import re
import statistics as st

MES = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
       "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

LINEA = re.compile(
    r"^([A-Z][a-z]{2})\s+(\d{1,2}),\s*(\d{4})\s+"
    r"(\d{1,2}:\d{2}\s*[AP]M)\s+(.*?)\$\s*([\d.,]+)\s+(.*)$")

def parse(path):
    out = []
    for ln in open(path, encoding="utf-8", errors="ignore"):
        ln = ln.replace("\t", " ").strip()
        if not ln or ln.startswith("#"):
            continue
        ln = re.sub(r"\s+", " ", ln)
        m = LINEA.match(ln)
        if not m:
            continue
        mes, dia, ano, _, grado, precio, tipo = m.groups()
        if mes not in MES:
            continue
        try:
            p = float(precio.replace(",", ""))
        except ValueError:
            continue
        fecha = "%s-%02d-%02d" % (ano, MES[mes], int(dia))
        out.append({"fecha": fecha, "precio": p,
                    "grado": grado.strip(), "tipo": tipo.strip()})
    return out

def pctil(datos, v):
    if not datos:
        return None
    return 100.0 * sum(1 for x in datos if x <= v) / len(datos)

def resumen(v, etiqueta):
    if not v:
        print("  %-16s (sin datos)" % etiqueta)
        return
    v = sorted(v)
    print("  %-16s n=%-4d mediana $%-7.2f  min $%-7.2f max $%.2f"
          % (etiqueta, len(v), st.median(v), v[0], v[-1]))

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    path = sys.argv[1]
    coste = float(sys.argv[2]) if len(sys.argv) > 2 else None
    fee = 5.0

    todo = parse(path)
    if not todo:
        print("no he podido parsear ninguna linea de", path)
        return 1

    grad = [x for x in todo if x["grado"]]
    lotes = [x for x in todo if not x["grado"]
             and "item offer" in x["tipo"].lower()]
    crudas = [x for x in todo if not x["grado"]
              and "item offer" not in x["tipo"].lower()]

    print()
    print("=" * 66)
    print("PERCENTILES -", path.split("/")[-1])
    print("=" * 66)
    print("  lineas parseadas: %d   crudas: %d   gradadas: %d   lotes: %d"
          % (len(todo), len(crudas), len(grad), len(lotes)))
    if not crudas:
        return 1

    p = sorted(x["precio"] for x in crudas)
    fechas = sorted(x["fecha"] for x in crudas)
    print("  periodo: %s a %s" % (fechas[0], fechas[-1]))
    print()
    print("  DISTRIBUCION (solo crudas, sin lotes)")
    print("  " + "-" * 62)
    for nom, q in (("P10", 0.10), ("P25", 0.25), ("P50", 0.50),
                   ("P75", 0.75), ("P90", 0.90)):
        print("  %-5s $%.2f" % (nom, p[min(int(len(p) * q), len(p) - 1)]))
    print("  %-5s $%.2f   %-5s $%.2f   media $%.2f"
          % ("min", p[0], "max", p[-1], st.mean(p)))
    print()

    print("  POR MES")
    print("  " + "-" * 62)
    meses = sorted(set(x["fecha"][:7] for x in crudas))
    for mm in meses:
        resumen([x["precio"] for x in crudas if x["fecha"][:7] == mm], mm)
    print()
    print("  TRAMOS RECIENTES (desde la ultima venta del archivo)")
    print("  " + "-" * 62)
    ult = fechas[-1]
    import datetime
    d1 = datetime.date.fromisoformat(ult)
    for dias, et in ((7, "ultimos 7d"), (30, "ultimos 30d"),
                     (90, "ultimos 90d")):
        lim = (d1 - datetime.timedelta(days=dias)).isoformat()
        resumen([x["precio"] for x in crudas if x["fecha"] >= lim], et)

    if grad:
        print()
        print("  GRADADAS (otra carta, solo referencia)")
        print("  " + "-" * 62)
        tipos = {}
        for x in grad:
            k = " ".join(x["grado"].split()[:2])
            tipos.setdefault(k, []).append(x["precio"])
        for k in sorted(tipos):
            resumen(tipos[k], k)

    if coste:
        be = coste / (1.0 - fee / 100.0)
        print()
        print("  TU POSICION")
        print("  " + "-" * 62)
        print("  coste        $%.2f  -> percentil %.0f"
              % (coste, pctil(p, coste)))
        print("  break-even   $%.2f  -> percentil %.0f  (fee %.0f%%)"
              % (be, pctil(p, be), fee))
        n = sum(1 for x in p if x >= be)
        print("  ventas historicas a break-even o mas: %d de %d (%.0f%%)"
              % (n, len(p), 100.0 * n / len(p)))
        lim = (d1 - datetime.timedelta(days=30)).isoformat()
        rec = [x["precio"] for x in crudas if x["fecha"] >= lim]
        if rec:
            n2 = sum(1 for x in rec if x >= be)
            print("  en los ultimos 30 dias: %d de %d" % (n2, len(rec)))
    print("=" * 66)
    return 0

if __name__ == "__main__":
    sys.exit(main())
