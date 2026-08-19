#!/usr/bin/env python3
"""reglas_drive.py — crea pestaña 'Reglas' en la hoja COMC - Punto de Mira (Drive) con el playbook operativo."""
import json, subprocess, urllib.request

SPREADSHEET_ID = "1akdKxf9d5I6u8rM6z0EuwU7AtUujpj3ffVuadjtCH1s"

# --- 1. crear pestaña 'Reglas' si no existe (via gog sheets batch-update no puede; usar update a rango crea? no.
# Usamos la misma técnica que antes: comprobar con get y si no existe, usar la API via gog? gog no crea tabs.
# Alternativa: escribir en rango 'Reglas!A1' fallará si no existe. Probamos crear con Sheets API raw via token gog no disponible.
# Solución ya usada antes: la pestaña 'Top-50' se creó con la API REST usando refresh token... pero no teníamos el token.
# En top50_a_drive.py falló por credenciales. PERO la pestaña Top-50 SÍ se creó? No — la sección Top-50 se escribió en la pestaña Cromos (A53).
# Para 'Reglas', probar primero si existe; si no, intentar addSheet via la API REST con el access token que gog usa internamente no es accesible.
# Plan B: usar gog sheets update sobre 'Reglas!A1' — si la hoja no existe dará error; entonces crearla requiere API.
# Plan C: escribir las reglas como texto en la pestaña Cromos, en columnas libres (Q+) al final, o en Punto de Mira.
# Mejor plan: probar si 'Reglas' existe; si no, crear con Sheets API usando endpoint de spreadsheets.batchUpdate
# con access token obtenido del keyring... demasiado. Usemos gog con rango 'Reglas' y si falla, lo ponemos en Cromos!Q1.
# ---

# Intentar leer 'Reglas!A1'
p = subprocess.run(["/root/.config/gogcli/run-gog.sh", "sheets", "get", SPREADSHEET_ID, "Reglas!A1:A1"],
                   capture_output=True, text=True)
existe = "Unable to parse range" not in (p.stdout + p.stderr) and p.returncode == 0
print("pestaña Reglas existe:", existe)

contenido = [
    ["REGLAS OPERATIVAS COMC — v1 (08/08/2026)"],
    [""],
    ["Fórmulas", "", "", ""],
    ["Precio máx compra (objetivo)", "= VentaEsperada × 0,95 ÷ 1,10", "", ""],
    ["VentaEsperada", "percentil 60-70 del historial de ventas, SIN outliers (IQR)", "", ""],
    ["Ventana según liquidez", "vel_dia > 1 → últimas 10 ventas · vel_dia ≤ 1 → últimas 20 ventas", "", ""],
    ["Outliers", "SIEMPRE fuera: fuera de [Q1-1,5×IQR, Q3+1,5×IQR]", "", ""],
    ["Venta mínima", "= Compra × 1,10 ÷ 0,95 (margen 10% + fee 5%)", "", ""],
    ["Break-even", "= Compra ÷ 0,95", "", ""],
    ["", "", "", ""],
    ["Fees COMC", "", "", ""],
    ["Venta fixed-price", "5% (NO 20%)", "", ""],
    ["Cash-out", "10% — regla: NUNCA retirar efectivo, todo en crédito COMC", "", ""],
    ["", "", "", ""],
    ["Reglas de compra", "", "", ""],
    ["Gap mínimo", "≥ 5% entre mínimo y 2º precio (verde en hoja)", "", ""],
    ["Tamaño", "precio ≤ 10% del bankroll (~6$)", "", ""],
    ["Meta", "$61 → $1000 en crédito COMC (+7,4%/op ≈ 39 ops)", "", ""],
    ["", "", "", ""],
    ["Estado actual (08/08/2026)", "", "", ""],
    ["Knueppel", "comprado a 3.00 · actual 3.49 · máx pagar 3.11 · venta mínima 3.47", "", ""],
    ["Durant", "actual 1.75 · máx pagar 1.11 (sin chollo hoy)", "", ""],
    ["Wemby", "actual 2.50 · máx pagar 1.47 (sin chollo hoy)", "", ""],
    ["", "", "", ""],
    ["Nota", "celdas amarillas = calculadas · celdas blancas = datos reales del scan", "", ""],
]

if existe:
    rango = "Reglas!A1:D" + str(len(contenido))
else:
    # intentar crear pestaña vía Sheets API con access token de gog no disponible; probamos update directo
    rango = "Reglas!A1:D" + str(len(contenido))

data = [{"range": rango, "values": contenido}]
json_str = json.dumps(data, ensure_ascii=False)
cmd = ["/root/.config/gogcli/run-gog.sh", "sheets", "batch-update",
       "--input=USER_ENTERED", f"--data-json={json_str}", SPREADSHEET_ID]
p2 = subprocess.run(cmd, capture_output=True, text=True)
print("update RC:", p2.returncode)
print((p2.stdout or "")[-300:])
print((p2.stderr or "")[-300:])
