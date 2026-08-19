#!/usr/bin/env python3
"""top50_drive_gog.py — añade sección Top-50 a la hoja de Drive (COMC - Punto de Mira)."""
import json, subprocess

SPREADSHEET_ID = "1akdKxf9d5I6u8rM6z0EuwU7AtUujpj3ffVuadjtCH1s"
rows = json.load(open("/tmp/scan-top50.json"))

def v(r, k):
    x = r.get(k)
    return x if isinstance(x, (int, float)) else ""

rows.sort(key=lambda r: v(r, "ventas_7d"), reverse=True)

headers = ["Jugador", "Mín $", "2º $", "Gap %", "Copias", "Al mín", "Cerca mín",
           "Ventas 7d", "Vel/día", "Días inv.", "Turnover %", "Fecha"]
values = []
for r in rows:
    values.append([
        r.get("nombre", ""), v(r, "min"), v(r, "seg"), v(r, "gap"),
        v(r, "copias"), v(r, "n_min"), v(r, "n_cerca"),
        v(r, "ventas_7d"), v(r, "vel_dia"),
        r.get("dias_inv") if r.get("dias_inv") is not None else "",
        v(r, "turnover"), r.get("fecha", ""),
    ])

bloque = [["TOP-50 NBA — Topps Chrome Base 2025-26 (scan 2026-08-07)"], []] + [headers] + values
last = 52 + len(bloque)
rango = f"A53:L{last}"
data = [{"range": rango, "values": bloque}]
json_str = json.dumps(data, ensure_ascii=False)

cmd = ["/root/.config/gogcli/run-gog.sh", "sheets", "batch-update",
       f"--data-json={json_str}", SPREADSHEET_ID]
p = subprocess.run(cmd, capture_output=True, text=True)
print("RC:", p.returncode)
print((p.stdout or "")[-1500:])
print((p.stderr or "")[-1500:])
