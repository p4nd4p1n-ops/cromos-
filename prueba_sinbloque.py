#!/usr/bin/env python3
"""Prueba definitiva: pagina del item de sellers 'SIN-BLOQUE' del muro de Daniels.
Si tienen BuyItNow => compra directa (mi parser falla). Si no => subasta (OK).
11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

urls = [
    ("adamrlacroix78 (SIN-BLOQUE)", "https://www.comc.com/Users/adamrlacroix78/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190"),
    ("chasingcards (SIN-BLOQUE)", "https://www.comc.com/Users/chasingcards/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190"),
    ("Craigers (SIN-BLOQUE)", "https://www.comc.com/Users/Craigers/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190"),
]
for etiqueta, url in urls:
    html = ms.get_html(url)
    if not html:
        print(f"{etiqueta}: sin_html")
        continue
    print(f"===== {etiqueta} =====")
    print("len:", len(html))
    tiene_bin = bool(re.search(r"BuyItNow|buyitnow", html))
    tiene_cart = bool(re.search(r"Add to Cart", html))
    tiene_bid = bool(re.search(r"(?i)(place\s*bid|bid\s*now|current\s*bid|start\s*bid|minimum\s*bid)", html))
    tiene_offer = bool(re.search(r"Make Offer|makeanoffer", html))
    print(f"  BuyItNow={tiene_bin} AddToCart={tiene_cart} Bid={tiene_bid} MakeOffer={tiene_offer}")
    m = re.search(r'class="actionarea">(.*?)(?=<div|</div>)', html, re.S)
    if m:
        txt = re.sub(r"<[^>]+>", " ", m.group(1))
        print("  actionarea:", re.sub(r"\s+", " ", txt).strip()[:120])
    # texto visible clave
    limpio = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    texto = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", limpio))
    i = texto.find("Sold Out")
    j = texto.find("Auction")
    print(f"  'Sold Out' en texto: {i > -1} | 'Auction' en texto: {j > -1}")
    if i > -1:
        print("  ctx:", texto[max(0,i-100):i+150])
    print()
