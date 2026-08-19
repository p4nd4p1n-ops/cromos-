#!/usr/bin/env python3
"""Genera JSON para batch-update del Sheets nativo desde el xlsx descargado."""
import json, sys
import openpyxl

SRC = "/root/.config/gogcli/drive-downloads/1h7saKtwDCAF_QMKyGEoxVZcNujSKZsz7_cromos.xlsx"
wb = openpyxl.load_workbook(SRC)

def sheet_rows(name):
    ws = wb[name]
    rows = []
    for row in ws.iter_rows(values_only=True):
        if any(c is not None for c in row):
            rows.append(["" if c is None else c for c in row])
    return rows

# 1) Punto de mira (estructura de Pin + fila Flagg)
pm = sheet_rows("Punto de mira ")
# normalizar fecha a string ISO
for r in pm[1:]:
    if isinstance(r[0], (int, float)):
        pass

# 2) Cromos
cr = sheet_rows("Cromos")
# quitar fila duplicada de cabecera al final si existe
while len(cr) > 1 and cr[-1] == cr[0]:
    cr.pop()

# 3) Recent Sales
rs = sheet_rows("Recent Sales")

data = {
    "Punto de mira": pm,
    "Cromos": cr,
    "Recent Sales": rs,
}
print(json.dumps(data, ensure_ascii=False, default=str))
