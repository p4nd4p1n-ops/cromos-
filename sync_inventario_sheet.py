#!/usr/bin/env python3
"""sync_inventario_sheet.py — pasa el último snapshot del inventario_scan a la hoja COMC.
- Lee /root/comc-data/inventario-scan.json del CT kobe (vía ssh)
- Actualiza Inventario: F (precio actual), H (1 muro), I (2 muro) por código
- Escribe en M1 la fecha/hora de los datos (celda de timestamp)
Uso: sync_inventario_sheet.py            → update automático
     sync_inventario_sheet.py --dry      → solo muestra lo que haría
"""
import subprocess, json, sys, os

SSH = ["ssh", "-J", "root@100.89.234.7", "root@192.168.0.102"]
GOG = "/root/.config/gogcli/run-gog.sh"
SHEET_ID = "1akdKxf9d5I6u8rM6z0EuwU7AtUujpj3ffVuadjtCH1s"
CELDA_FECHA = "Inventario!M1"   # celda con la fecha de los datos (Pin 13/08/2026)

def get_snapshot():
    r = subprocess.run(SSH + ["cat", "/root/comc-data/inventario-scan.json"],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise SystemExit(f"ssh error: {r.stderr}")
    return json.loads(r.stdout)

def gog(*args):
    r = subprocess.run([GOG] + list(args), capture_output=True, text=True, timeout=90)
    return r

def main():
    dry = "--dry" in sys.argv
    snap = get_snapshot()
    fecha = snap.get("fecha", "?")
    n1 = snap.get("niveles", {}).get("N1", [])
    if not n1:
        print("N1 INVENTARIO vacío en el snapshot — nada que escribir")
        return
    # fila por código
    filas = {}
    for d in n1:
        if "min" not in d:
            continue
        cod = d["codigo"]
        min_s = f"{d['min']:.2f}"
        owners = "/".join(d["owners_1er"])
        h = f"1: ${d['min']:.2f} ({owners})" if owners and owners != "?" else f"1: ${d['min']:.2f}"
        i = ""
        if d.get("seg") is not None:
            i = f"2: ${d['seg']:.2f}"
        filas[cod] = {"F": min_s, "H": h, "I": i}
    # leer la hoja para localizar filas por código (col A)
    r = gog("-p", "sheets", "get", SHEET_ID, "Inventario!A1:L16")
    if r.returncode != 0:
        print("ERROR leyendo hoja:", r.stdout[-500:], r.stderr[-500:])
        return
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    # localizar nº de fila por código
    cod2row = {}
    for idx, line in enumerate(lines[1:], start=2):  # fila 1 = cabecera
        cod = line.split("\t")[0].strip() if "\t" in line else line.split("|")[0].strip()
        cod2row[cod] = idx
    # construir updates
    updates = []
    for cod, vals in filas.items():
        row = cod2row.get(cod)
        if not row:
            print(f"  ⚠️ {cod} no encontrado en la hoja")
            continue
        for col, val in vals.items():
            if val:
                updates.append({"range": f"Inventario!{col}{row}", "values": [[val]]})
    if not updates:
        print("Nada que actualizar")
        return
    # timestamp
    fecha_corta = fecha  # "2026-08-13 09:40:00"
    try:
        from datetime import datetime, timezone
        from zoneinfo import ZoneInfo
        dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        dt_local = dt.astimezone(ZoneInfo("Europe/Madrid"))  # hora de Pin (Logroño)
        fecha_corta = dt_local.strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass
    updates.append({"range": CELDA_FECHA, "values": [[f"Datos del: {fecha_corta}"]]})
    if dry:
        print(f"[DRY] fecha={fecha_corta}, {len(updates)-1} celdas:")
        for u in updates:
            print("  ", u["range"], "=", u["values"][0][0])
        return
    data_json = json.dumps(updates)
    r = gog("sheets", "batch-update", f"--data-json={data_json}", SHEET_ID)
    if r.returncode != 0:
        print("ERROR batch-update:", r.stdout[-800:], r.stderr[-800:])
        return
    print(f"✅ Hoja actualizada: {len(updates)-1} celdas + timestamp {CELDA_FECHA}")

if __name__ == "__main__":
    main()
