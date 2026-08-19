#!/usr/bin/env python3
"""Busca seccion de subastas activas en la pagina de la BASE de Daniels.
11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

html = ms.get_html("https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190")
if not html:
    print("sin_html")
    sys.exit()

print("=== h1-h6 ===")
for m in re.finditer(r"<h([1-6])[^>]*>(.*?)</h\1>", html, re.S):
    t = re.sub(r"<[^>]+>", "", m.group(2)).strip()
    print(f"h{m.group(1)}: {t[:70]}")

print("\n=== 'Auction' en toda la pagina (posiciones) ===")
for m in re.finditer(r"Auction", html):
    i = m.start()
    ctx = re.sub(r"\s+", " ", html[max(0,i-120):i+120])
    print(f"@{i}: {ctx[:240]}")

print("\n=== 'Bid' en toda la pagina ===")
for m in re.finditer(r"[Bb]id", html):
    i = m.start()
    if i < 150000 or i > 340000:
        continue
    ctx = re.sub(r"\s+", " ", html[max(0,i-120):i+120])
    print(f"@{i}: {ctx[:240]}")
