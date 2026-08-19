#!/usr/bin/env python3
"""Registro de operaciones COMC (capa 3).
  op.py                          lista abiertas y cerradas
  op.py compra COD PRECIO [URL]  abre operacion, guarda foto del baremo
  op.py venta COD PRECIO [FECHA] cierra y calcula neto
  op.py seguimiento              evolucion del muro tras vender
  op.py revision                 baremo contra resultados
"""
import sys, os, datetime
sys.path.insert(0, "/root/comc-scripts")
import parte as P

OPS = P.DATA + "/operaciones.txt"
INVF = P.DATA + "/inventario.txt"
CAB = ("# id ; codigo ; nombre ; url ; f_compra ; p_compra ; f_venta ;"
       " p_venta ; v7d ; dias ; gap ; lotes ; ballena ; nota")

def num(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None

def lee():
    ops = []
    if not os.path.exists(OPS):
        return ops
    for ln in open(OPS, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        p = [x.strip() for x in ln.split(";")]
        while len(p) < 14:
            p.append("")
        ops.append(p)
    return ops

def guarda(ops):
    with open(OPS, "w", encoding="utf-8") as f:
        f.write(CAB + "\n")
        for o in ops:
            f.write(" ; ".join(o) + "\n")

def neto(o):
    c, v = num(o[5]), num(o[7])
    if c is None or v is None or c == 0:
        return None
    fee = P.reglas().get("fee", 5.0) / 100.0
    return 100.0 * (v * (1.0 - fee) - c) / c

def foto(url):
    r = P.medidas().get(P.cid(url))
    if not r:
        return None, ["", "", "", "", ""]
    det = r.get("sales_det") or []
    rea = r.get("ventas_reales") or []
    lot = ""
    if det:
        lot = str(int(100.0 * (len(det) - len(rea)) / len(det)))
    return r, [str(r.get("ventas_7d") or 0),
               str(r.get("dias_venta_7d") or 0),
               format(float(r.get("gap") or 0), ".1f"), lot,
               "1" if r.get("ballena") else "0"]

def compra(a):
    if len(a) < 2:
        print("uso: op.py compra CODIGO PRECIO [URL]")
        return 1
    cod, precio = a[0], a[1]
    url = a[2] if len(a) > 2 else ""
    nombre = cod
    for c in P.lee_pm():
        if c["cod"].upper() == cod.upper():
            url = url or c["url"]
            nombre = c["nom"]
    for r in inv_lee():
        if r[0].upper() == cod.upper():
            url = url or r[2]
            if nombre == cod:
                nombre = r[1]
    if not url:
        print("falta URL (el codigo no esta en punto-mira.txt)")
        return 1
    r, snap = foto(url)
    ops = lee()
    oid = "OP-" + str(len(ops) + 1).zfill(3)
    hoy = datetime.date.today().isoformat()
    ops.append([oid, cod, nombre, url, hoy, precio, "", ""] + snap + [""])
    guarda(ops)
    print("registrada", oid, "-", nombre, "a $" + precio)
    if inv_add(cod, nombre, url):
        print("  entra al inventario")
    if r:
        R = P.reglas()
        f = P.fallos(r, R)
        print("  baremo al entrar: v7d " + snap[0] +
              " | dias " + snap[1] + " | gap " + snap[2] +
              "% | lotes " + snap[3] + "% | ballena " + snap[4])
        est = "SI" if not f else "NO -> " + ", ".join(f)
        print("  cumplia: " + est)
    else:
        print("  AVISO: sin medicion previa. Sin foto del baremo.")
    return 0

def venta(a):
    if len(a) < 2:
        print("uso: op.py venta CODIGO PRECIO")
        return 1
    cod, precio = a[0], a[1]
    ops = lee()
    for o in reversed(ops):
        if o[1].upper() == cod.upper() and not o[7]:
            o[6] = (a[2] if len(a) > 2
                    else datetime.date.today().isoformat())
            o[7] = precio
            guarda(ops)
            n = neto(o)
            print("cerrada " + o[0] + " - " + o[2])
            if inv_del(cod):
                print("  sale del inventario")
            print("  $" + o[5] + " -> $" + precio + "  neto " +
                  (format(n, "+.1f") + "%" if n is not None else "?"))
            return 0
    print("no hay operacion abierta con codigo", cod)
    return 1

def lista():
    ops = lee()
    ab = [o for o in ops if not o[7]]
    ce = [o for o in ops if o[7]]
    print()
    print("OPERACIONES - abiertas:", len(ab), "| cerradas:", len(ce))
    P.raya()
    for o in ab:
        print(" " + o[0] + "  " + o[2][:32].ljust(34) +
              "compra " + o[4] + "  $" + o[5])
    if ab and ce:
        P.raya()
    for o in ce:
        n = neto(o)
        print(" " + o[0] + "  " + o[2][:32].ljust(34) +
              "$" + o[5] + " -> $" + o[7] + "  " +
              (format(n, "+.1f") + "%" if n is not None else "?"))
    P.raya()
    return 0

def media(xs):
    return sum(xs) / len(xs) if xs else None

def revision():
    ops = [o for o in lee() if o[7]]
    R = P.reglas()
    print()
    P.raya("=")
    print("REVISION - el baremo contra los resultados")
    P.raya("=")
    n = len(ops)
    print("  operaciones cerradas:", n)
    if n < 25:
        print("  MUESTRA INSUFICIENTE (hacen falta ~25-30).")
        print("  Lo de abajo es descriptivo. NO mover umbrales por esto.")
    print()
    if not ops:
        print("  todavia no hay nada cerrado")
        P.raya()
        return 0
    crit = [
        ("v7d >= " + str(int(R.get("v7d_min", 7))),
         lambda o: (num(o[8]) or -1) >= R.get("v7d_min", 7)),
        ("dias >= " + str(int(R.get("dias_min", 3))),
         lambda o: (num(o[9]) or -1) >= R.get("dias_min", 3)),
        ("gap >= " + format(P.gap_req(R), ".1f"),
         lambda o: (num(o[10]) or -1) >= P.gap_req(R)),
        ("lotes < " + str(int(R.get("lotes_max", 30))),
         lambda o: (num(o[11]) if o[11] else 0)
         < R.get("lotes_max", 30)),
        ("sin ballena", lambda o: o[12] == "0"),
    ]
    print("  " + "criterio".ljust(18) + "cumplian".rjust(9) +
          "neto".rjust(9) + "     no".rjust(8) + "neto".rjust(9))
    P.raya()
    for nom, fn in crit:
        si = [neto(o) for o in ops if fn(o) and neto(o) is not None]
        no = [neto(o) for o in ops if not fn(o) and neto(o) is not None]
        ms, mn = media(si), media(no)
        print("  " + nom.ljust(18) + str(len(si)).rjust(9) +
              (format(ms, "+.1f") + "%" if ms is not None else "-").rjust(9) +
              str(len(no)).rjust(8) +
              (format(mn, "+.1f") + "%" if mn is not None else "-").rjust(9))
    P.raya()
    todos = [neto(o) for o in ops if neto(o) is not None]
    m = media(todos)
    gan = len([x for x in todos if x > 0])
    mt = format(m, "+.1f") + "%" if m is not None else "-"
    print("  global: " + str(len(todos)) + " ops | media " + mt +
          " | ganadoras " + str(gan) + "/" + str(len(todos)))
    fr = R.get("fee_retirada", 10.0)
    print("  retirada: sacar saldo de COMC cuesta " +
          format(fr, ".0f") + " pct. De cada $100 en cuenta" +
          " salen $" + format(100.0 * (1 - fr / 100.0), ".0f"))
    P.raya()
    return 0

def main():
    a = sys.argv[1:]
    if not a or a[0] == "list":
        return lista()
    if a[0] == "compra":
        return compra(a[1:])
    if a[0] == "venta":
        return venta(a[1:])
    if a[0] == "revision":
        return revision()
    if a[0] == "seguimiento":
        return seguimiento()
    print(__doc__)
    return 1


def seguimiento():
    ops = [o for o in lee() if o[7]]
    print()
    P.raya("=")
    print("SEGUIMIENTO POST-VENTA - vendi barato?")
    P.raya("=")
    if not ops:
        print("  nada cerrado todavia")
        P.raya()
        return 0
    hist = P.historico()
    for o in ops:
        serie = hist.get(P.cid(o[3]), [])
        post = [x for x in serie if x[0] >= o[6]]
        pv = num(o[7])
        print()
        print(" " + o[0] + "  " + o[2][:44])
        print("   vendida " + o[6] + " a $" + o[7])
        if not post:
            print("   sin mediciones desde la venta")
            continue
        for f, m in post[-8:]:
            d = ""
            if pv and m:
                d = "  " + format(100.0 * (m - pv) / pv, "+.0f") + "% vs venta"
            print("   " + f + "   muro 1o $" + format(m, ".2f") + d)
        if len(post) < 3:
            print("   solo " + str(len(post)) +
                  " medicion(es) tras la venta: sin veredicto")
            continue
        u3 = sorted(x[1] for x in post[-3:])
        m3 = u3[len(u3) // 2]
        if not pv or not m3:
            continue
        if m3 > pv * 1.05:
            print("   -> mediana 3 ultimas $" + format(m3, ".2f") +
                  ": el mercado subio, vendiste pronto")
        elif m3 < pv * 0.95:
            print("   -> mediana 3 ultimas $" + format(m3, ".2f") +
                  ": el mercado bajo, buena salida")
        else:
            print("   -> mediana 3 ultimas $" + format(m3, ".2f") +
                  ": sigue donde vendiste")
    P.raya()
    print("  ojo: son precios de muro, no ventas cerradas.")
    return 0


def inv_lee():
    out = []
    if not os.path.exists(INVF):
        return out
    for ln in open(INVF, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        f = [x.strip() for x in ln.split(";")]
        while len(f) < 3:
            f.append("")
        out.append(f[:3])
    return out

def inv_guarda(rows):
    with open(INVF, "w", encoding="utf-8") as f:
        f.write("# codigo ; nombre ; url\n")
        for r in rows:
            f.write(" ; ".join(r) + "\n")

def inv_add(cod, nom, url):
    rows = inv_lee()
    if any(r[0].upper() == cod.upper() for r in rows):
        return False
    rows.append([cod, nom, url])
    inv_guarda(rows)
    return True

def inv_del(cod):
    rows = inv_lee()
    n = len(rows)
    rows = [r for r in rows if r[0].upper() != cod.upper()]
    if len(rows) == n:
        return False
    inv_guarda(rows)
    return True

if __name__ == "__main__":
    sys.exit(main())
