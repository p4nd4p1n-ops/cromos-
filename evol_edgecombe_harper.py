#!/usr/bin/env python3
"""Evolución del mercado de Edgecombe Topps Chrome #253.1 y Harper Bowman Univ #22
desde los snapshots player-* del CT kobe (09/08 - 16/08) + feed-carta del 17/08."""
import json, glob, sys

def evol(files, target_id, label):
    print("=== %s (cardId %s) ===" % (label, target_id))
    for f in sorted(files):
        try:
            d = json.load(open(f))
        except Exception as e:
            print(f.split("/")[-1], "ERR", e)
            continue
        fecha = d.get("fecha", f.split("/")[-1])
        for it in d.get("items", []):
            if str(it.get("id")) == target_id or target_id in it.get("url", ""):
                print("%s | precio %s | qty %s | marca %s | %s" % (
                    fecha, it.get("precio"), it.get("qty"), it.get("marca"), it.get("titulo", "")[:70]))
                break

evol(glob.glob("/root/comc-data/snapshots/player-vj-edgecombe-*.json"), "31038640", "VJ Edgecombe Topps Chrome #253.1")
print()
evol(glob.glob("/root/comc-data/snapshots/player-dylan-harper-*.json"), "28629778", "Dylan Harper Bowman Univ #22")
print()
print("=== feed-carta 17/08 (primeras 4) ===")
for f in sorted(glob.glob("/root/comc-data/snapshots/feed-carta-*.json")):
    try:
        d = json.load(open(f))
        if isinstance(d, dict):
            print(f.split("/")[-1], "|", json.dumps(d)[:300])
        else:
            print(f.split("/")[-1], "| list len", len(d), json.dumps(d[0])[:200] if d else "")
    except Exception as e:
        print(f.split("/")[-1], "ERR", e)
