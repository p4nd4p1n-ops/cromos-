#!/usr/bin/env python3
"""parse_mlb_poll.py — parsea el HTML guardado del poll ROY de MLB (formato forge-entity)."""
import re, glob, html

files = sorted(glob.glob("/root/comc-data/mlb-roy-poll-*.html"))
hh = open(files[-1], encoding="utf-8", errors="replace").read()

# formato: **1\. <forge-entity title="Nombre" ...>Nombre</forge-entity>, Equipo (X total vote points, Y first-place votes)**
pat = re.compile(
    r"\*\*(\d+)(?:-T)?\\?\.\s*"
    r'<forge-entity title="([^"]+)"[^>]*>.*?</forge-entity>\s*,\s*([A-Za-z \.]+?)\s*'
    r"\((\d+) total vote points(?:,\s*(\d+) first-place votes?)?\)",
    re.S)
print("=== RANKING ROY (agosto 2026) ===")
for m in pat.finditer(hh):
    num, nombre, equipo, puntos, primeros = m.groups()
    print(f"  {num:>2}. {html.unescape(nombre).strip():28} {html.unescape(equipo).strip():22} | {puntos} pts | {primeros or 0} v1º")
