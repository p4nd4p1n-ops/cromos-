#!/usr/bin/env python3
"""Pagina del ITEM de subasta (mbevilacqua) — extrae TODO el texto visible para
encontrar la marca de subasta (boton, texto, tiempo). 11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

html = ms.get_html("https://www.comc.com/Users/mbevilacqua/Cards/Football/2024/Panini_Donruss_Optic_-_Base_-_Purple_Shock_Prizm/248/Rated_Rookie_-_Jayden_Daniels/28877852")
if not html:
    print("sin_html")
    sys.exit()

# texto visible completo
limpio = re.sub(r"<script.*?</script>", "", html, flags=re.S)
limpio = re.sub(r"<style.*?</style>", "", limpio, flags=re.S)
texto = re.sub(r"<[^>]+>", " ", limpio)
texto = re.sub(r"\s+", " ", texto)
# zona del item (buscar despues de la imagen)
idx = texto.find("Preview of Card")
print("TEXTO DESDE LA IMAGEN:")
print(texto[idx:idx+2500] if idx > -1 else texto[:2500])

print("\n=== botones/links de accion ===")
for m in re.finditer(r'(?:class="(?:addtocart|buyitnow|makeanoffer|bid[^"]*)"|href="javascript:([A-Za-z]+)\([^)]*\)")', html):
    print(m.group(0)[:120])
