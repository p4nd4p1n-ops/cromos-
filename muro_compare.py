#!/usr/bin/env python3
"""muro_compare.py — compara los 2 últimos snapshots de muro fino (muro-fino-*.json)
y detecta por carta: copias NUEVAS (item_id que no estaba), copias que desaparecieron,
y cambios de precio de un mismo item.

Uso: muro_compare.py  (usa muro-fino-ultimo.json + el anterior disponible)
Salida: JSON con movimientos por carta.
"""
import json, glob, os, sys

DATA_DIR = "/root/comc-data"

def cargar_snapshots():
    """Devuelve (anterior, ultimo) ordenados por fecha, o (None, None) si no hay 2."""
    files = sorted(glob.glob(f"{DATA_DIR}/muro-fino-*.json"))
    files = [f for f in files if "ultimo" not in f]
    if len(files) < 2:
        # si solo hay 1, comparar contra vacío (todo son nuevas)
        if len(files) == 1:
            return None, json.load(open(files[0]))
        return None, None
    a = json.load(open(files[-2]))
    b = json.load(open(files[-1]))
    return a, b

def por_carta(snap):
    if snap is None:
        return {}
    return {c["carta"]: c for c in snap.get("cartas", []) if "error" not in c}

def main():
    a, b = cargar_snapshots()
    if b is None:
        print(json.dumps({"error": "no hay snapshots de muro"}, ensure_ascii=False))
        return
    da = por_carta(a)
    db = por_carta(b)
    mov = {"fecha_anterior": a.get("fecha") if a else None,
           "fecha_actual": b.get("fecha"),
           "cartas": []}
    for carta, cb in db.items():
        ca = da.get(carta)
        if ca is None:
            continue  # carta nueva en el muro (no en el anterior): no comparable aún
        items_a = {m["item_id"]: m for m in ca.get("muro_items", [])}
        items_b = {m["item_id"]: m for m in cb.get("muro_items", [])}
        nuevas = [items_b[i] for i in items_b if i not in items_a]
        desaparecidas = [items_a[i] for i in items_a if i not in items_b]
        cambio_precio = []
        for i, m in items_b.items():
            if i in items_a and items_a[i]["precio"] != m["precio"]:
                cambio_precio.append({"item_id": i, "owner": m["owner"],
                                      "precio": f"{items_a[i]['precio']}→{m['precio']}"})
        if nuevas or desaparecidas or cambio_precio:
            mov["cartas"].append({
                "carta": carta,
                "nuevas": [{"precio": m["precio"], "owner": m["owner"], "item_id": m["item_id"]} for m in nuevas],
                "desaparecidas": [{"precio": m["precio"], "owner": m["owner"], "item_id": m["item_id"]} for m in desaparecidas],
                "cambio_precio": cambio_precio,
                "muro_actual": cb.get("muro_txt"),
                "min": cb.get("min"), "seg": cb.get("seg"), "gap": cb.get("gap"),
                "copias": cb.get("copias"), "vel_dia": cb.get("vel_dia"),
            })
    print(json.dumps(mov, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
