#!/usr/bin/env python3
"""fix_muro_enlaces.py — alinea M=muro / N=enlace en Punto de Mira (formato de ayer)."""
import json, subprocess

SPREADSHEET_ID = "1akdKxf9d5I6u8rM6z0EuwU7AtUujpj3ffVuadjtCH1s"

durant_url = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/1551/Kevin_Durant/31038541"
wemby_url = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038608"

data = [
    {"range": "Punto de Mira!M1:N1", "values": [["Muro", "Enlace"]]},
    {"range": "Punto de Mira!M7:N7",
     "values": [["4 @ $1,75", durant_url]]},
    {"range": "Punto de Mira!M8:N8",
     "values": [["33 copias: $2.50 x 2, $2.55 x 5, $3.40 x 2, $4.70 x 2, $5.50 x 9, $5.75 x 10, $6.85 x 3", wemby_url]]},
]
json_str = json.dumps(data, ensure_ascii=False)
cmd = ["/root/.config/gogcli/run-gog.sh", "sheets", "batch-update",
       "--input=USER_ENTERED", f"--data-json={json_str}", SPREADSHEET_ID]
p = subprocess.run(cmd, capture_output=True, text=True)
print("RC:", p.returncode, (p.stdout or "")[-300:], (p.stderr or "")[-300:])
