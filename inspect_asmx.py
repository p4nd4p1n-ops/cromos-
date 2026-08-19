#!/usr/bin/env python3
"""Inspecciona los metodos del servicio CardPopupService.asmx de COMC.
La pagina carga /CardPopupService.asmx/js — ahi estan los metodos AJAX.
11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

# 1) el js del servicio
html = ms.get_html("https://www.comc.com/CardPopupService.asmx/js")
if html:
    print("=== CardPopupService.asmx/js ===")
    print("len:", len(html))
    # metodos expuestos
    for m in re.finditer(r'(?:Sys\.Net\.WebServiceProxy|\.prototype\.)\s*\.\s*([A-Za-z0-9_]+)\s*=', html):
        print("metodo:", m.group(1))
    # tambien buscar nombres de metodos en el js
    nombres = set(re.findall(r'([A-Za-z]+Service\.[A-Za-z0-9_]+)', html))
    print("nombres service:", list(nombres)[:20])
else:
    print("sin_html en asmx/js")

# 2) el html de la carta para ver como se llama al popup
html2 = ms.get_html("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852")
if html2:
    print("\n=== llamadas al popup en la pagina ===")
    for m in re.finditer(r'(?:CardPopupService|\.asmx)[^"\']{0,80}', html2):
        print(m.group(0)[:120])
    # buscar funciones JS relacionadas con sellers/items
    for m in re.finditer(r'function\s+([A-Za-z0-9_]+)\([^)]*\)\s*\{', html2):
        f = m.group(1)
        if any(k in f.lower() for k in ["item", "sale", "popup", "card", "detail", "auction"]):
            print("funcion:", f)
