#!/usr/bin/env python3
"""diag_prtx4.py — contexto de las 30 menciones 'Auction' en el perfil de PRTX560."""
import re

html = open("/tmp/prtx560_profile.html").read()

print("=== CONTEXTOS 'Auction' (primeras 12) ===")
vistos = set()
for mm in re.finditer(r"[Aa]uction", html):
    s = max(0, mm.start() - 150)
    e = min(len(html), mm.start() + 150)
    ctx = re.sub(r"\s+", " ", html[s:e])
    clave = ctx[:80]
    if clave in vistos:
        continue
    vistos.add(clave)
    print("...", ctx, "...")
    print()
    if len(vistos) >= 12:
        break

# buscar enlaces a subastas en el perfil
print("\n=== LINKS /Auctions o /Auction ===")
for mm in list(re.finditer(r'href="([^"]*[Aa]uction[^"]*)"', html))[:10]:
    print(" ", mm.group(1))
