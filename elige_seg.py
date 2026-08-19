#!/usr/bin/env python3
"""Propone cartas para seguimiento diario desde los player-*.json.

  elige_seg.py DEPORTE [precio_max] [min_copias]

DEPORTE: Football | Baseball | Basketball
"""
import json, glob, sys

D = "/root/comc-data/snapshots"
dep = sys.argv[1] if len(sys.argv) > 1 else "Football"
pmax = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
qmin = int(sys.argv[3]) if len(sys.argv) > 3 else 20

por_id = {}
for f in glob.glob(D + "/player-*.json"):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    for c in d.get("items", []):
        u = c.get("url") or ""
        if "/Cards/" + dep + "/" not in u:
            continue
        if c.get("marca") != "CANDIDATA":
            continue
        p, q = c.get("precio"), c.get("qty") or 0
        if p is None or p > pmax or q < qmin:
            continue
        k = u.rstrip("/").split("/")[-1]
        if k not in por_id or q > (por_id[k].get("qty") or 0):
            por_id[k] = c

top = sorted(por_id.values(), key=lambda x: -(x.get("qty") or 0))
print("# candidatas", dep, "precio <=", pmax, "copias >=", qmin,
      "->", len(top))
print("# codigo ; nombre ; url ; nota")
for i, c in enumerate(top[:20], 1):
    t = (c.get("titulo") or "")[:60]
    print("SEG-%02d ; %s ; %s ; seguimiento" % (i, t, c.get("url")))
