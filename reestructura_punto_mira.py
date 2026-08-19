#!/usr/bin/env python3
"""reestructura_punto_mira.py — Punto de Mira con campos exactos de Pin:
Fecha temporada Coleccion Numero Nombre Tipo Vel/día Precio Actual Precio maximo que pagamos venta minima para ganar Muro enlace"""
import json, subprocess

SPREADSHEET_ID = "1akdKxf9d5I6u8rM6z0EuwU7AtUujpj3ffVuadjtCH1s"

# --- 1. limpiar la pestaña ---
p = subprocess.run(["/root/.config/gogcli/run-gog.sh", "sheets", "clear",
                    SPREADSHEET_ID, "Punto de mira!A1:P15"],
                   capture_output=True, text=True)
print("clear RC:", p.returncode, (p.stderr or "")[-200:])

# --- 2. headers + filas (12 columnas: A..L) ---
headers = ["Fecha", "temporada", "Coleccion", "Numero", "Nombre", "Tipo",
           "Vel/día", "Precio Actual", "Precio maximo que pagamos",
           "venta minima para ganar", "Muro", "enlace"]

rows = [
    ["2026-08-07", "2025-26", "Topps Chrome - [Base]", "252.1", "Dylan Harper", "Base",
     1.286, 7.5, 6, "=IF(I2=\"\",\"\",ROUND(I2*1.1/0.95,2))",
     "2 @ $7,50",
     "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"],
    ["2026-08-07", "2025-26", "Topps Chrome - [Base]", "253.1", "VJ Edgecombe", "Base",
     0.714, 1.78, 1.88, "=IF(I3=\"\",\"\",ROUND(I3*1.1/0.95,2))",
     "",
     "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2531/VJ_Edgecombe/31038640"],
    ["2026-08-07", "2025-26", "Topps Chrome - [Base]", "254.1", "Kon Knueppel", "Base",
     1.857, 3.49, 3.11, "=IF(I4=\"\",\"\",ROUND(I4*1.1/0.95,2))",
     "3.49, 3.70 x2, 3.75 x5 (1.49 = subasta PRTX560, no firme)",
     "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2541/Kon_Knueppel/31038641"],
    ["2026-08-07", "2025-26", "Topps Chrome - [Base]", "278.1", "Hugo Gonzalez", "Base",
     0.571, 1.3, 1.08, "=IF(I5=\"\",\"\",ROUND(I5*1.1/0.95,2))",
     "7 @ $1,30 (benny3277)",
     "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2781/Hugo_Gonzalez/31038666"],
    ["", "", "", "", "", "", "", "", "", "", "", ""],  # fila 6 en blanco
    ["2026-08-08", "2025-26", "Topps Chrome - [Base]", "1551", "Kevin Durant", "Base",
     1.0, 1.75, 1.11, "=IF(I7=\"\",\"\",ROUND(I7*1.1/0.95,2))",
     "4 @ $1,75",
     "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/1551/Kevin_Durant/31038541"],
    ["2026-08-08", "2025-26", "Topps Chrome - [Base]", "2211", "Victor Wembanyama", "Base",
     2.571, 2.5, 1.47, "=IF(I8=\"\",\"\",ROUND(I8*1.1/0.95,2))",
     "33 copias: $2.50 x 2, $2.55 x 5, $3.40 x 2, $4.70 x 2, $5.50 x 9, $5.75 x 10, $6.85 x 3",
     "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038608"],
]

values = [headers] + rows
data = [{"range": "Punto de mira!A1:L9", "values": values}]
json_str = json.dumps(data, ensure_ascii=False)
cmd = ["/root/.config/gogcli/run-gog.sh", "sheets", "batch-update",
       "--input=USER_ENTERED", f"--data-json={json_str}", SPREADSHEET_ID]
p2 = subprocess.run(cmd, capture_output=True, text=True)
print("update RC:", p2.returncode, (p2.stdout or "")[-200:], (p2.stderr or "")[-300:])
