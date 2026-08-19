#!/usr/bin/env python3
"""Acumula el historial de ventas por carta desde los fino-*.json.

La pagina publica de COMC solo ensena las ultimas ~20 ventas. Guardandolas
cada noche y fusionandolas se reconstruye el historial completo sin login.

Las ventas identicas (misma fecha, hora, precio, tipo) son copias reales
vendidas a la vez, asi que se conserva el maximo visto en un mismo escaneo.

  acumula_ventas.py            procesa todos los fino-*.json
  acumula_ventas.py --lista    solo lista lo acumulado
"""
import json
import glob
import os
import re
import sys
import collections

DATA = "/root/comc-data"
DEST = DATA + "/ventas"

MES = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
       "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}

LIN = re.compile(
    r"^([A-Z][a-z]{2} \d{1,2}, \d{4})\s+(\d{1,2}:\d{2}\s*[AP]M)\s+"
    r"(.*?)\$\s*([\d.,]+)\s+(.*)$")

def cid(u):
    return u.rstrip("/").split("/")[-1] if u else ""

def orden(k):
    m = re.match(r"([A-Z][a-z]{2}) (\d{1,2}), (\d{4})", k[0])
    if not m:
        return ("0000-00-00", k[1])
    return ("%s-%02d-%02d" % (m.group(3), MES.get(m.group(1), 0),
                              int(m.group(2))), k[1])

def linea(k):
    f, h, p, t, g = k
    g = (g + " ") if g else ""
    return "%s %s %s$%.2f %s" % (f, h, g, p, t)

def lee(path):
    c = collections.Counter()
    if not os.path.exists(path):
        return c
    for ln in open(path, encoding="utf-8", errors="ignore"):
        ln = re.sub(r"\s+", " ", ln.replace("\t", " ").strip())
        if not ln or ln.startswith("#"):
            continue
        m = LIN.match(ln)
        if not m:
            continue
        f, h, g, p, t = m.groups()
        try:
            v = float(p.replace(",", ""))
        except ValueError:
            continue
        c[(f, h, v, t.strip(), g.strip())] += 1
    return c

def escribe(path, cont, titulo, url):
    ks = sorted(cont, key=orden, reverse=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# " + (titulo or "") + "\n")
        f.write("# " + (url or "") + "\n")
        f.write("# acumulado automatico. NO editar a mano.\n")
        for k in ks:
            for _ in range(cont[k]):
                f.write(linea(k) + "\n")

def main():
    os.makedirs(DEST, exist_ok=True)
    if "--lista" in sys.argv:
        for p in sorted(glob.glob(DEST + "/*.txt")):
            n = sum(1 for l in open(p, encoding="utf-8")
                    if l.strip() and not l.startswith("#"))
            cab = open(p, encoding="utf-8").readline().strip("# \n")
            print("%-14s %5d ventas   %s" % (
                os.path.basename(p)[:-4], n, cab[:50]))
        return 0

    PROC = DATA + "/acumula-procesados.txt"
    procesados = set()
    if os.path.exists(PROC) and "--todo" not in sys.argv:
        procesados = set(
            l.strip() for l in open(PROC, encoding="utf-8")
            if l.strip())

    todos = sorted(glob.glob(DATA + "/snapshots/fino-*.json"))
    objetivo = [f for f in todos
                if os.path.basename(f) not in procesados]
    if "--todo" in sys.argv:
        print("modo --todo: reprocesando", len(todos), "snapshots")
    else:
        print("snapshots nuevos:", len(objetivo), "de", len(todos))

    nuevos = collections.defaultdict(collections.Counter)
    meta = {}
    for f in objetivo:
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for r in d:
            u = r.get("url")
            det = r.get("sales_det") or []
            if not u or not det:
                continue
            k = cid(u)
            meta[k] = (r.get("titulo") or "", u)
            c = collections.Counter()
            for s in det:
                try:
                    v = float(s.get("precio") or 0)
                except (TypeError, ValueError):
                    continue
                c[(s.get("fecha", ""), s.get("hora", ""), v,
                   (s.get("tipo") or "").strip(),
                   (s.get("grado") or "").strip())] += 1
            for kk, n in c.items():
                if n > nuevos[k][kk]:
                    nuevos[k][kk] = n

    tot_n = tot_c = 0
    for k, cont in sorted(nuevos.items()):
        path = DEST + "/" + k + ".txt"
        viejo = lee(path)
        antes = sum(viejo.values())
        for kk, n in cont.items():
            if n > viejo[kk]:
                viejo[kk] = n
        ahora = sum(viejo.values())
        t, u = meta.get(k, ("", ""))
        escribe(path, viejo, t, u)
        if ahora > antes:
            tot_n += 1
            tot_c += ahora - antes
        print("%-12s %5d ventas (%+d)  %s"
              % (k, ahora, ahora - antes, t[:44]))
    print()
    print("cartas actualizadas: %d   ventas nuevas: %d" % (tot_n, tot_c))
    with open(PROC, "a", encoding="utf-8") as pf:
        for f in objetivo:
            pf.write(os.path.basename(f) + "\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
