#!/usr/bin/env python3
"""punto_mira_add.py — añade Durant y Wemby a la pestaña Punto de Mira (hoja Drive)."""
import json, subprocess

SPREADSHEET_ID = "1akdKxf9d5I6u8rM6z0EuwU7AtUujpj3ffVuadjtCH1s"

# fila 6 en blanco, filas 7-8: Durant y Wemby (datos del scan top-50 2026-08-07)
bloque = [
    ["", "", "", "", "", "", "", "", "", "", "", ""],
    ["2026-08-08", "2025-26", "Topps Chrome - [Base]", 1551, "Kevin Durant", "Base",
     1.0, 1.75, "", "", "", 5.4],
    ["2026-08-08", "2025-26", "Topps Chrome - [Base]", 2211, "Victor Wembanyama", "Base",
     2.571, 2.5, "", "", "", 0.0],
]

rango = "Punto de Mira!A6:L8"
data = [{"range": rango, "values": bloque}]
json_str = json.dumps(data, ensure_ascii=False)

cmd = ["/root/.config/gogcli/run-gog.sh", "sheets", "batch-update",
       f"--data-json={json_str}", SPREADSHEET_ID]
p = subprocess.run(cmd, capture_output=True, text=True)
print("RC:", p.returncode)
print((p.stdout or "")[-1000:])
print((p.stderr or "")[-1000:])
