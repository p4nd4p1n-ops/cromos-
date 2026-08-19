#!/usr/bin/env python3
"""Compara dos snapshots de feed-set y muestra cambios: nuevas, desaparecidas, precio baja, qty sube."""
import json
import sys

def load(path):
    with open(path) as f:
        return json.load(f)["items"]

def main():
    if len(sys.argv) < 3:
        print("uso: compare_feed_snapshots.py <snapshot_A.json> <snapshot_B.json>")
        return
    a = load(sys.argv[1])
    b = load(sys.argv[2])
    da = {x["id"]: x for x in a}
    db = {x["id"]: x for x in b}

    print("== NUEVAS (no estaban en A) ==")
    for i in db:
        if i not in da:
            x = db[i]
            print(f"  {x['titulo'][:60]} | ${x['precio']} | {x['qty']} copias")
    print("== DESAPARECIDAS (estaban en A, ya no) ==")
    for i in da:
        if i not in db:
            x = da[i]
            print(f"  {x['titulo'][:60]} | era ${x['precio']} | {x['qty']} copias")
    print("== PRECIO BAJA ==")
    for i in db:
        if i in da and db[i]["precio"] < da[i]["precio"]:
            x, y = da[i], db[i]
            print(f"  {x['titulo'][:55]} | ${x['precio']} -> ${y['precio']} | qty {x['qty']}->{y['qty']}")
    print("== QTY SUBE (stock fresco) ==")
    for i in db:
        if i in da and db[i]["qty"] > da[i]["qty"]:
            x, y = da[i], db[i]
            print(f"  {x['titulo'][:55]} | qty {x['qty']}->{y['qty']} | ${y['precio']}")

if __name__ == "__main__":
    main()
