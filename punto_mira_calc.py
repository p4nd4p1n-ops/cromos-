#!/usr/bin/env python3
"""punto_mira_calc.py — rellena celdas calculadas (objetivo/dif/ganancia) con fórmulas y las marca en amarillo."""
import json, subprocess

SPREADSHEET_ID = "1akdKxf9d5I6u8rM6z0EuwU7AtUujpj3ffVuadjtCH1s"

# Fórmulas: I=Precio Objetivo (regla: gap 15% vs 2º precio), J=Dif % vs Objetivo, K=Ganancia $
# Durant: seg=1.85 -> objetivo 1.61 ; Wemby: seg=2.50 -> objetivo 2.17
bloque = [
    ["=ROUND(1.85/1.15,2)", "=ROUND((I7-H7)/H7*100,1)", "=ROUND(H7-I7,2)"],
    ["=ROUND(2.5/1.15,2)",  "=ROUND((I8-H8)/H8*100,1)", "=ROUND(H8-I8,2)"],
]

# leyenda en M1
leyenda = [
    ["Leyenda: fondo amarillo = calculado", "", "", ""],
]

data = [
    {"range": "Punto de Mira!I7:K8", "values": bloque},
    {"range": "Punto de Mira!M1:P1", "values": leyenda},
]
json_str = json.dumps(data, ensure_ascii=False)

cmd = ["/root/.config/gogcli/run-gog.sh", "sheets", "batch-update",
       "--input=USER_ENTERED", f"--data-json={json_str}", SPREADSHEET_ID]
p = subprocess.run(cmd, capture_output=True, text=True)
print("update RC:", p.returncode, (p.stdout or "")[-400:], (p.stderr or "")[-400:])

# formato amarillo en las celdas calculadas I7:K8
fmt = {"backgroundColor": {"red": 1.0, "green": 0.92, "blue": 0.4}}
cmd2 = ["/root/.config/gogcli/run-gog.sh", "sheets", "format", SPREADSHEET_ID,
        "Punto de Mira!I7:K8", f"--format-json={json.dumps(fmt)}",
        "--format-fields=userEnteredFormat.backgroundColor"]
p2 = subprocess.run(cmd2, capture_output=True, text=True)
print("format RC:", p2.returncode, (p2.stdout or "")[-400:], (p2.stderr or "")[-400:])
