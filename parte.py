#!/usr/bin/env python3
"""Parte diario COMC: 3 bloques y se acabo."""
import json, glob, os, sys, datetime

DATA = "/root/comc-data"
INV = DATA + "/inventario-scan.json"
PM = DATA + "/punto-mira.txt"
INVF = DATA + "/inventario.txt"
REG = DATA + "/reglas.txt"
UMBRAL = 7
W = 92
ACCIONES = []

def raya(c="-"):
    print(c * W)

def carga(p):
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except Exception as e:
        print("ERROR", p, e)
        return None

def medidas():
    out = {}
    for f in sorted(glob.glob(DATA + "/snapshots/fino-*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for r in d:
            u = r.get("url")
            if not u or "/Cards/Non-Sports/" in u:
                continue
            k = cid(u)
            p = out.get(k)
            vf = r.get("fecha") or ""
            if p is None or vf >= (p.get("fecha") or ""):
                out[k] = r
    return out

def dias(f):
    if not f:
        return None
    try:
        d = datetime.date.fromisoformat(f[:10])
    except Exception:
        return None
    return (datetime.date.today() - d).days

def avisos(r):
    a = []
    det = r.get("sales_det") or []
    rea = r.get("ventas_reales") or []
    if det:
        p = 100.0 * (len(det) - len(rea)) / len(det)
        if p >= 50:
            a.append("LOTES " + str(int(p)) + "%")
    if r.get("ballena"):
        a.append("BALLENA")
    dd = r.get("dias_venta_7d")
    if dd is not None and (r.get("ventas_7d") or 0) >= UMBRAL:
        if dd <= 1:
            a.append("1 SOLO DIA")
    d = dias(r.get("fecha"))
    if d is not None and d >= 3:
        a.append("hace " + str(d) + "d")
    return a

def eur(v):
    return "-" if v is None else "$" + format(float(v), ".2f")

def pct(v):
    return "-" if v is None else format(float(v), ".1f") + "%"

def lee_pm():
    cartas = []
    if not os.path.exists(PM):
        return cartas
    for ln in open(PM, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        p = [x.strip() for x in ln.split(";")]
        while len(p) < 6:
            p.append("")
        g = None
        if p[4] and p[4] != "-":
            try:
                g = float(p[4])
            except ValueError:
                g = None
        cartas.append({"cod": p[0], "nom": p[1], "url": p[2],
                       "niv": (p[3] or "VIGILAR").upper(),
                       "gat": g, "nota": p[5]})
    return cartas

def datos_inv():
    """codigo/id -> coste, precio de venta, fecha de entrada."""
    out = {}
    if not os.path.exists(INVF):
        return out
    for ln in open(INVF, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        f = [x.strip() for x in ln.split(";")]
        while len(f) < 7:
            f.append("")
        d = {"coste": None, "precio": None, "desde": f[5], "nota": f[6]}
        try:
            d["coste"] = float(f[3]) if f[3] else None
        except ValueError:
            pass
        try:
            d["precio"] = float(f[4]) if f[4] else None
        except ValueError:
            pass
        if f[2]:
            out[cid(f[2])] = d
    return out

def b1(inv):
    print()
    raya("=")
    print("1. LO QUE TENGO")
    raya("=")
    if not inv:
        print("  falta inventario-scan.json")
        return set()
    niveles = inv.get("niveles") or {}
    mias = niveles.get("N1") or []
    otras = sum(len(v) for k, v in niveles.items() if k != "N1")
    ex = datos_inv()
    urls = set()
    for k, cs in niveles.items():
        for c in cs:
            if c.get("url"):
                urls.add(cid(c["url"]))
    cap = sum((ex.get(cid(c.get("url") or ""), {}).get("coste") or 0)
              for c in mias)
    print("  escaneado: %s   %d cartas mias   (%d en N2/N3, no tuyas)"
          % (inv.get("fecha", "?")[:16], len(mias), otras))
    if cap:
        print("  capital en cartas: $%.2f" % cap)
    print()
    print("  " + "carta".ljust(27) + "v7d".rjust(4) + "  muro1o".rjust(8) +
          "    tuyo".rjust(8) + " si vendo".rjust(8) + " dias".rjust(5) +
          "   accion")
    raya()
    mias = sorted(mias, key=lambda c: -(c.get("v7d") or 0))
    R = reglas()
    fee = R.get("fee", 5.0) / 100.0
    sd = R.get("stop_dias", 21)
    sp = R.get("stop_perdida", 15.0)
    muertas, atascado, stops, cap_stop = 0, 0.0, 0, 0.0
    for c in mias:
        d = ex.get(cid(c.get("url") or ""), {})
        v = c.get("v7d")
        hold = "hold" in (d.get("nota") or "").lower()
        mn = c.get("min")
        mio = d.get("precio")
        co = d.get("coste")
        dd = dias(d.get("desde")) if d.get("desde") else None
        nt = None
        if co and mn and co > 0:
            nt = 100.0 * ((mn - 0.01) * (1.0 - fee) - co) / co
        st = []
        if not hold and nt is not None:
            if nt < -sp:
                st.append("STOP perdida %.0f%%" % nt)
            if dd is not None and dd >= sd and nt < 0:
                st.append("STOP tiempo %dd" % dd)
        if v is not None and v <= 2 and not hold:
            muertas += 1
            atascado += co or 0
        if st:
            stops += 1
            cap_stop += co or 0
        if hold:
            acc = "HOLD - " + (d.get("nota") or "")
        elif st:
            acc = " + ".join(st) + " -> LIQUIDAR"
        elif mio and mn and mio > mn:
            acc = "BAJAR a $%.2f" % (mn - 0.01)
        elif mio and mn and v == 0:
            acc = "en muro y no vende"
        elif v is None:
            acc = "sin dato"
        elif v == 0:
            acc = "SIN VENTAS - revisar precio"
        elif v <= 2:
            acc = "muerta (%d/sem)" % v
        elif v < UMBRAL:
            acc = "floja (%d/sem)" % v
        else:
            acc = "ok"
        nom = (c.get("nombre") or "?")
        if not mio and not hold:
            acc += " | falta tu precio"
            ACCIONES.append("LISTAR  " + nom + " (no tiene precio puesto)")
        elif st:
            ACCIONES.append("LIQUIDAR  " + nom + "  (" + ", ".join(st) + ")")
        elif not hold and mio and mn and mio > mn:
            ACCIONES.append("BAJAR  " + nom + "  de $%.2f a $%.2f"
                            % (mio, mn - 0.01))
        print("  " + (c.get("nombre") or "?")[:26].ljust(27) +
              str(v if v is not None else "-").rjust(4) +
              eur(mn).rjust(8) + eur(mio).rjust(8) +
              (pct(nt) if nt is not None else "-").rjust(8) +
              (str(dd) if dd is not None else "-").rjust(5) +
              "   " + acc)
    raya()
    if stops:
        print("  STOP: %d cartas   capital a liquidar $%.2f"
              % (stops, cap_stop))
    if muertas:
        print("  MUERTAS (v7d<=2): %d cartas" % muertas +
              ("   capital atascado $%.2f" % atascado if atascado else ""))
        print("  revisa los lunes, de mayor a menor capital")
    return urls

def b2(pm, med):
    print()
    raya("=")
    print("2. PUNTO DE MIRA")
    raya("=")
    if not pm:
        print("  falta punto-mira.txt")
        return set()
    urls = set(cid(c["url"]) for c in pm if c.get("url"))
    orden = {"COMPRAR": 0, "VIGILAR": 1, "OBSERVAR": 2}
    pm = sorted(pm, key=lambda c: (orden.get(c["niv"], 9), c["nom"]))
    print("  " + str(len(pm)) + " cartas (objetivo 18-20)")
    print()
    print("  " + "carta".ljust(30) + "nivel".ljust(10) + "v7d".rjust(5) +
          "  precio".rjust(9) + "   gap".rjust(7) +
          " gatillo".rjust(9) + "   senal")
    raya()
    n = 0
    for c in pm:
        r = med.get(cid(c["url"])) if c.get("url") else None
        v = r.get("ventas_7d") if r else None
        mn = r.get("min") if r else None
        gp = r.get("gap") if r else None
        g = c["gat"]
        if r is None:
            s = "sin medir aun"
        elif g and mn is not None and mn <= g and (v or 0) >= UMBRAL:
            s = ">>> COMPRAR"
            n += 1
        elif g is not None and mn is not None and mn <= g:
            s = "precio ok pero liquidez baja"
        elif (v or 0) >= UMBRAL and (gp or 0) >= 5.0:
            s = "liquida y con hueco - mirar"
        elif (v or 0) < UMBRAL:
            s = "liquidez < " + str(UMBRAL) + "/sem"
        else:
            s = "esperar"
        av = avisos(r) if r else []
        if av:
            s += "  [" + ", ".join(av) + "]"
        print("  " + c["nom"][:29].ljust(30) + c["niv"][:9].ljust(10) +
              str(v if v is not None else "-").rjust(5) +
              eur(mn).rjust(9) + pct(gp).rjust(7) +
              (eur(g) if g else "-").rjust(9) + "   " + s)
    raya()
    if len(pm) < 18:
        print("  faltan", 18 - len(pm), "para el minimo -> bloque 3")
    if n:
        print("  >>>", n, "con senal de COMPRA")
    return urls

def b3(med, cubiertas, n):
    print()
    raya("=")
    print("3. HUECOS - liquidas que ni tengo ni vigilo")
    raya("=")
    libres = [r for u, r in med.items() if u not in cubiertas]
    libres = [r for r in libres if (r.get("ventas_7d") or 0) > 0]
    libres.sort(key=lambda r: (-(r.get("ventas_7d") or 0),
                        -(r.get("dias_venta_7d") or 0)))
    libres = libres[:n]
    if not libres:
        print("  nada nuevo: todo lo liquido ya esta cubierto")
        return
    print("  " + "carta".ljust(46) + "v7d".rjust(5) + " dias".rjust(6) +
          "  precio".rjust(9) + "   gap".rjust(7) + "   avisos")
    raya()
    for r in libres:
        av = avisos(r)
        print("  " + (r.get("titulo") or "?")[:45].ljust(46) +
              str(r.get("ventas_7d") or 0).rjust(5) +
              str(r.get("dias_venta_7d") or 0).rjust(6) +
              eur(r.get("min")).rjust(9) + pct(r.get("gap")).rjust(7) +
              "   " + (", ".join(av) if av else "limpia"))
    raya()
    print("  para meterla:  nano " + PM)

def cid(u):
    return u.rstrip("/").split("/")[-1] if u else ""

def cabecera(inv, med):
    R = reglas()
    ex = datos_inv()
    mias = ((inv or {}).get("niveles") or {}).get("N1") or []
    encartas = sum((ex.get(cid(c.get("url") or ""), {}).get("coste") or 0)
                   for c in mias)
    libre = R.get("liquido", 0.0)
    print()
    raya("#")
    print("  PARTE COMC   " +
          datetime.datetime.now().strftime("%d/%m  %H:%M"))
    raya("#")
    print()
    print("  DINERO    $%.2f libre  +  $%.2f en cartas  =  $%.2f"
          % (libre, encartas, libre + encartas))
    print("  MEDIDAS   %d cartas con datos de liquidez" % len(med))
    print()
    if ACCIONES:
        print("  HOY TIENES %d COSA%s QUE HACER:"
              % (len(ACCIONES), "" if len(ACCIONES) == 1 else "S"))
        for k, a in enumerate(ACCIONES, 1):
            print("   %d. %s" % (k, a))
    else:
        print("  HOY NO HAY NADA QUE HACER.")
        print("  Ninguna carta pasa el baremo.")
        print("  Dinero quieto es mejor que dinero mal puesto.")
    print()

def main():
    import io
    import contextlib
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    inv = carga(INV)
    pm = lee_pm()
    med = medidas()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        u1 = b1(inv)
        u2 = b2(pm, med)
        b3b(med, u1 | u2, n)
    cabecera(inv, med)
    print(buf.getvalue())
    raya("#")
    print("  fin del parte.")
    raya("#")
    print()


def reglas():
    R = {"v7d_min": 7, "dias_min": 3, "lotes_max": 30,
         "precio_max": 5.05, "sin_ballena": 1}
    if os.path.exists(REG):
        for ln in open(REG, encoding="utf-8"):
            ln = ln.strip()
            if not ln or ln.startswith("#") or "=" not in ln:
                continue
            k, v = ln.split("=", 1)
            try:
                R[k.strip()] = float(v.strip())
            except ValueError:
                pass
    return R

def gap_req(R):
    fee = R.get("fee", 5.0) / 100.0
    neto = R.get("neto_min", 10.0) / 100.0
    return 100.0 * ((1.0 + neto) / (1.0 - fee) - 1.0)

def historico():
    out = {}
    for f in sorted(glob.glob(DATA + "/snapshots/fino-*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for r in d:
            u = r.get("url")
            if u:
                out.setdefault(cid(u), []).append(
                    ((r.get("fecha") or "")[:10], r.get("min")))
    for f in sorted(glob.glob(DATA + "/inventario-scan-*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        fe = (d.get("fecha") or "")[:10]
        for cs in (d.get("niveles") or {}).values():
            for c in cs:
                u = c.get("url")
                if u:
                    out.setdefault(cid(u), []).append((fe, c.get("min")))
    for k in out:
        out[k] = sorted(set(x for x in out[k] if x[1] is not None))
    return out

def muro12(r):
    m = r.get("muro") or []
    precios = sorted(set(x.get("precio") for x in m
                         if x.get("precio") is not None))
    if not precios:
        return r.get("min"), 1, r.get("seg")
    p1 = precios[0]
    n1 = len([x for x in m if x.get("precio") == p1])
    if n1 > 1:
        return p1, n1, p1
    p2 = precios[1] if len(precios) > 1 else r.get("seg")
    return p1, n1, p2

def decide(r, R):
    p1, n1, p2 = muro12(r)
    if not p1 or not p2:
        return ("SIN DATOS", None, "")
    fee = R.get("fee", 5.0) / 100.0
    neto = R.get("neto_min", 5.0) / 100.0
    techo = (p2 - 0.01) * (1.0 - fee) / (1.0 + neto)
    nota = ("ballena x%d" % n1) if n1 > 1 else ""
    if p1 <= techo:
        return ("COMPRA YA", p1, nota)
    if techo >= 0.80 * p1:
        return ("OFERTA", techo, nota)
    return ("DESCARTAR", techo, (nota + " techo bajo el 80%").strip())

def fallos(r, R):
    f = []
    if (r.get("ventas_7d") or 0) < R["v7d_min"]:
        f.append("liquidez")
    if (r.get("dias_venta_7d") or 0) < R["dias_min"]:
        f.append("concentrada")
    det = r.get("sales_det") or []
    rea = r.get("ventas_reales") or []
    if det and 100.0 * (len(det) - len(rea)) / len(det) > R["lotes_max"]:
        f.append("lotes")
    if (r.get("gap") or 0) < gap_req(R):
        f.append("gap")
    mn = r.get("min")
    if mn is None or mn > R["precio_max"]:
        f.append("precio")
    if mn is not None and mn < R.get("precio_min", 0):
        f.append("muy barata")
    if R.get("sin_ballena") and r.get("ballena"):
        f.append("ballena")
    return f

def fila3(r, txt):
    R = reglas()
    acc, pr, nota = decide(r, R)
    act = (acc + " $" + format(pr, ".2f")) if pr else acc
    if nota:
        act += " (" + nota + ")"
    print("  " + (r.get("titulo") or "?")[:42].ljust(43) +
          str(r.get("ventas_7d") or 0).rjust(4) +
          str(r.get("dias_venta_7d") or 0).rjust(5) +
          eur(r.get("min")).rjust(8) + pct(r.get("gap")).rjust(7) +
          "  " + act.ljust(22) + txt)

def b3b(med, cubiertas, n):
    R = reglas()
    print()
    raya("=")
    print("3. FICHAJES - pasan el baremo y no los tienes")
    raya("=")
    libres = [r for u, r in med.items() if u not in cubiertas]
    ok, casi = [], []
    for r in libres:
        f = fallos(r, R)
        if not f:
            ok.append(r)
        elif len(f) == 1:
            casi.append((r, f[0]))
    ok.sort(key=lambda r: -(r.get("ventas_7d") or 0))
    casi.sort(key=lambda x: -(x[0].get("ventas_7d") or 0))
    print("  " + "carta".ljust(43) + "v7d".rjust(4) + " dias".rjust(5) +
          " precio".rjust(8) + "   gap".rjust(7) +
          "  accion".ljust(24) + "estado")
    raya()
    if ok:
        for r in ok[:n]:
            fila3(r, "FICHAR")
            ac, pr, _ = decide(r, R)
            if pr:
                ACCIONES.append(ac + "  " + (r.get("titulo") or "?")[:40] +
                                "  a $%.2f" % pr)
    else:
        print("  ninguna pasa el baremo hoy")
    raya()
    print("  CASI (fallan una sola):")
    if casi:
        for r, f in casi[:n]:
            fila3(r, "falla " + f)
    else:
        print("  ninguna")
    raya()
    print("  baremo: v7d>=" + str(int(R["v7d_min"])) +
          " dias>=" + str(int(R["dias_min"])) +
          " gap>=" + format(gap_req(R), ".1f") + "%" +
          " precio $" + str(R.get("precio_min", 0)) +
          "-" + str(R["precio_max"]))
    print("  reglas en: " + REG)

if __name__ == "__main__":
    main()
