#!/usr/bin/env python3
"""Candidatas a punto de mira: liquidez real que aun no vigilas.

Lee el ultimo fino-*.json, descarta lo que ya esta en inventario.txt
o en punto-mira.json, y filtra v7d>=5 y gap>=7 (barra floja, no de
compra). Solo sugiere -- pm.py add es cosa tuya.

  candidatos.py            lista candidatas
"""
import json
import glob
import os
import sys

DATA = "/root/comc-data"
INV = DATA + "/inventario.txt"
PM = DATA + "/punto-mira.json"

V7D_MIN = 5
GAP_MIN = 7.0


def leer_dias_min():
    ruta = DATA + "/reglas.txt"
    if os.path.exists(ruta):
        for ln in open(ruta, encoding="utf-8"):
            ln = ln.strip()
            if ln.startswith("dias_min"):
                try:
                    return float(ln.split("=", 1)[1].strip())
                except ValueError:
                    pass
    return 3.0


DIAS_MIN = leer_dias_min()


def cid(u):
    return u.rstrip("/").split("/")[-1] if u else ""


def cids_inventario():
    out = set()
    if not os.path.exists(INV):
        return out
    for ln in open(INV, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#") or ";" not in ln:
            continue
        p = [x.strip() for x in ln.split(";")]
        if len(p) > 2:
            out.add(cid(p[2]))
    return out


def cids_punto_mira():
    out = set()
    if not os.path.exists(PM):
        return out
    doc = json.load(open(PM))
    for c in doc.get("cartas", []):
        out.add(cid(c.get("url")))
    return out


def ultimo_fino():
    fs = sorted(glob.glob(DATA + "/snapshots/fino-*.json"))
    return fs[-1] if fs else None


def main():
    f = ultimo_fino()
    if not f:
        print("no hay fino-*.json")
        return 1
    datos = json.load(open(f))
    fuera = cids_inventario() | cids_punto_mira()

    cand = []
    for r in datos:
        u = r.get("url")
        if not u or cid(u) in fuera:
            continue
        v7 = r.get("ventas_7d") or 0
        gap = r.get("gap") or 0
        dias = r.get("dias_venta_7d") or 0
        if v7 >= V7D_MIN and gap >= GAP_MIN and dias >= DIAS_MIN:
            cand.append(r)

    cand.sort(key=lambda r: -(r.get("ventas_7d") or 0))

    print()
    print("CANDIDATAS A VIGILAR -", len(cand),
          "  (v7d>=%d gap>=%.0f%% dias>=%.0f)" % (
              V7D_MIN, GAP_MIN, DIAS_MIN))
    print("-" * 78)
    if not cand:
        print("  ninguna hoy")
    for r in cand[:15]:
        print(" %-42s v7d=%-3d dias=%-2d gap=%.1f%%  min $%.2f" % (
            (r.get("titulo") or "?")[:42], r.get("ventas_7d") or 0,
            r.get("dias_venta_7d") or 0, r.get("gap") or 0,
            r.get("min") or 0))
        print("   pm.py add %s \"%s\" %s OBSERVAR" % (
            cid(r.get("url")), (r.get("titulo") or "?")[:40],
            r.get("url")))
    print("-" * 78)
    print("fuente:", os.path.basename(f))
    return 0


if __name__ == "__main__":
    sys.exit(main())
