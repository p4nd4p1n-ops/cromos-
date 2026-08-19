#!/usr/bin/env python3
"""muro_enlaces_hoja.py — añade muro + enlaces COMC: sección Top-50 (Cromos) y Durant/Wemby (Punto de Mira)."""
import json, subprocess

SPREADSHEET_ID = "1akdKxf9d5I6u8rM6z0EuwU7AtUujpj3ffVuadjtCH1s"

# --- 1. Enlaces para las 45 cartas de la sección Top-50 (Cromos, filas 56..100) ---
rows = json.load(open("/tmp/scan-top50.json"))
rows.sort(key=lambda r: (r.get("min") is None, r.get("min") or 0))

enlaces = []
for i, r in enumerate(rows):
    url = "https://www.comc.com" + r["path"]
    enlaces.append([f'=HYPERLINK("{url}","COMC")'])

# --- 2. Muro + enlaces Durant/Wemby (Punto de Mira, filas 7-8) ---
muro = json.load(open("/tmp/muro-2026-08-08.json"))  # traído del LXC

def txt_muro(nombre):
    m = muro.get(nombre, {})
    pp = m.get("por_precio", {})
    partes = [f"${p} x {c}" for p, c in pp.items()]
    return f"{m.get('total_copias','?')} copias: " + ", ".join(partes)

durant_url = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/1551/Kevin_Durant/31038541"
wemby_url = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038608"

data = [
    # Cromos: header Enlace en M1 + enlaces M56:M100
    {"range": "Cromos!M1", "values": [["Enlace"]]},
    {"range": f"Cromos!M56:M{55 + len(rows)}", "values": enlaces},
    # Punto de Mira: headers M1/N1, enlace+muro filas 7-8, leyenda movida a Q1
    {"range": "Punto de Mira!M1:N1", "values": [["Enlace", "Muro"]]},
    {"range": "Punto de Mira!M7:N7",
     "values": [[f'=HYPERLINK("{durant_url}","COMC")', txt_muro("Kevin Durant")]]},
    {"range": "Punto de Mira!M8:N8",
     "values": [[f'=HYPERLINK("{wemby_url}","COMC")', txt_muro("Victor Wembanyama")]]},
    {"range": "Punto de Mira!Q1:R1", "values": [["Leyenda: fondo amarillo = calculado", ""]]},
]
json_str = json.dumps(data, ensure_ascii=False)
cmd = ["/root/.config/gogcli/run-gog.sh", "sheets", "batch-update",
       "--input=USER_ENTERED", f"--data-json={json_str}", SPREADSHEET_ID]
p = subprocess.run(cmd, capture_output=True, text=True)
print("RC:", p.returncode, (p.stdout or "")[-300:], (p.stderr or "")[-300:])
print("Muro Durant:", txt_muro("Kevin Durant"))
print("Muro Wemby:", txt_muro("Victor Wembanyama"))
