#!/usr/bin/env python3
"""Registro de ofertas y ficha de vendedores.

  ofertas.py                        ofertas vivas y exposicion
  ofertas.py add CARTA VEND PRECIO  registra una oferta viva
  ofertas.py estado N ESTADO        cierra la oferta N
  ofertas.py vendedores             como negocia cada vendedor
  ofertas.py todas                  historial completo

ESTADO: aceptada | rechazada | contraoferta | cancelada | caducada
"""
import sys
import os
import datetime

DATA = "/root/comc-data"
OF = DATA + "/ofertas.txt"
CAB = "# fecha ; carta ; vendedor ; precio ; estado ; nota"
VIVA = "viva"
BUENOS = ("aceptada",)
MALOS = ("rechazada", "contraoferta", "cancelada", "caducada")


def num(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def lee():
    out = []
    if not os.path.exists(OF):
        return out
    for ln in open(OF, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        p = [x.strip() for x in ln.split(";")]
        while len(p) < 6:
            p.append("")
        out.append(p[:6])
    return out


def guarda(rows):
    with open(OF, "w", encoding="utf-8") as f:
        f.write(CAB + "\n")
        for r in rows:
            f.write(" ; ".join(r) + "\n")


def dias(f):
    try:
        d = datetime.date.fromisoformat(f)
    except Exception:
        return None
    return (datetime.date.today() - d).days


def vivas(rows):
    return [r for r in rows if r[4].lower() == VIVA]


def cmd_lista(rows):
    v = vivas(rows)
    print()
    print("OFERTAS VIVAS:", len(v))
    print("-" * 74)
    total = 0.0
    for i, r in enumerate(rows):
        if r[4].lower() != VIVA:
            continue
        p = num(r[3]) or 0
        total += p
        d = dias(r[0])
        av = ""
        if d is not None and d >= 3:
            av = "  CADUCA YA (3 dias)"
        elif d is not None and d >= 1:
            av = "  %dd sin respuesta" % d
        print(" %-3d %s  %-22s %-18s $%-7.2f%s"
              % (i, r[0], r[1][:22], r[2][:18], p, av))
    print("-" * 74)
    print(" expuesto en ofertas vivas: $%.2f" % total)
    return 0


def cmd_add(rows, a):
    if len(a) < 3:
        print("uso: ofertas.py add CARTA VENDEDOR PRECIO [nota]")
        return 1
    NEGATIVAS = ("rechazada", "contraoferta")
    for r in rows:
        if (r[1].lower() != a[0].lower()
                or r[2].lower() != a[1].lower()):
            continue
        if r[4].lower() == VIVA:
            print("YA TIENES UNA OFERTA VIVA a %s por %s ($%s, %s)"
                  % (a[1], a[0], r[3], r[0]))
            return 1
        if r[4].lower() not in NEGATIVAS:
            continue
        d = dias(r[0])
        if d is not None and d < 30:
            print("TE DIJO QUE NO hace %d dias: $%s -> %s (%s)"
                  % (d, r[3], r[4], r[0]))
            print("REGLA: una oferta por carta y vendedor.")
            print("Cuarentena 30 dias. Quedan %d." % (30 - d))
            return 1
    nota = a[3] if len(a) > 3 else ""
    rows.append([datetime.date.today().isoformat(), a[0], a[1],
                 "%.2f" % float(a[2]), VIVA, nota])
    guarda(rows)
    print("registrada: %s a %s por $%s" % (a[0], a[1], a[2]))
    return cmd_lista(rows)


def cmd_estado(rows, a):
    if len(a) < 2:
        print("uso: ofertas.py estado N ESTADO")
        return 1
    i = int(a[0])
    if i < 0 or i >= len(rows):
        print("indice fuera de rango")
        return 1
    est = a[1].lower()
    if est not in BUENOS + MALOS + (VIVA,):
        print("estado invalido:", est)
        return 1
    rows[i][4] = est
    guarda(rows)
    print("oferta %d -> %s  (%s, %s)" % (i, est, rows[i][1], rows[i][2]))
    return 0


def cmd_vendedores(rows):
    v = {}
    for r in rows:
        est = r[4].lower()
        if est == VIVA:
            continue
        d = v.setdefault(r[2], {"n": 0, "ok": 0, "ult": "", "acc": []})
        d["n"] += 1
        if est in BUENOS:
            d["ok"] += 1
            p = num(r[3])
            if p:
                d["acc"].append(p)
        if r[0] > d["ult"]:
            d["ult"] = r[0]
    print()
    print("FICHA DE VENDEDORES")
    print("-" * 74)
    print(" %-22s %5s %5s %6s  %-10s %s"
          % ("vendedor", "ofer", "acep", "%", "ultima", "criterio"))
    print("-" * 74)
    for k in sorted(v, key=lambda x: (-v[x]["n"], x)):
        d = v[k]
        pct = 100.0 * d["ok"] / d["n"] if d["n"] else 0
        if d["n"] >= 3 and d["ok"] == 0:
            crit = "NO OFERTAR (0 de %d)" % d["n"]
        elif d["ok"] and pct >= 50:
            crit = "acepta bien"
        elif d["ok"]:
            crit = "a veces"
        else:
            crit = "sin exito aun"
        print(" %-22s %5d %5d %5.0f%%  %-10s %s"
              % (k[:22], d["n"], d["ok"], pct, d["ult"], crit))
    print("-" * 74)
    tot = sum(d["n"] for d in v.values())
    ok = sum(d["ok"] for d in v.values())
    print(" total: %d ofertas cerradas, %d aceptadas (%.0f%%)"
          % (tot, ok, 100.0 * ok / tot if tot else 0))
    return 0


def cmd_todas(rows):
    print()
    print(" %-3s %-11s %-22s %-18s %8s  %s"
          % ("n", "fecha", "carta", "vendedor", "precio", "estado"))
    print("-" * 78)
    for i, r in enumerate(rows):
        print(" %-3d %-11s %-22s %-18s %8s  %s"
              % (i, r[0], r[1][:22], r[2][:18], "$" + r[3], r[4]))
    print("-" * 78)
    return 0


def main():
    rows = lee()
    a = sys.argv[1:]
    if not a:
        return cmd_lista(rows)
    if a[0] == "add":
        return cmd_add(rows, a[1:])
    if a[0] == "estado":
        return cmd_estado(rows, a[1:])
    if a[0] == "vendedores":
        return cmd_vendedores(rows)
    if a[0] == "todas":
        return cmd_todas(rows)
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
