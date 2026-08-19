#!/usr/bin/env python3
"""VERIFICACION FINAL del metodo BuyItNow en la pagina del item del vendedor.
ClassicSportscards (subasta segun Pin) en la base de Daniels.
11/08/2026.
"""
import sys, re
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

urls = [
    ("ClassicSportscards (SUBATA segun Pin)", "https://www.comc.com/Users/ClassicSportscards/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190"),
    ("dobiscollecting (BUYNOW)", "https://www.comc.com/Users/dobiscollecting/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190"),
]
for etiqueta, url in urls:
    html = ms.get_html(url)
    if not html:
        print(f"{etiqueta}: sin_html")
        continue
    print(f"===== {etiqueta} =====")
    tiene_bin = bool(re.search(r"BuyItNow|buyitnow", html))
    tiene_cart = bool(re.search(r"Add to Cart", html))
    tiene_bid = bool(re.search(r"(?i)(place\s*bid|bid\s*now|current\s*bid|start\s*bid|min\s*bid|Bid on this|bidbutton|btnBid)", html))
    tiene_offer = bool(re.search(r"Make Offer|makeanoffer", html))
    # el guid/item de esta pagina
    im = re.search(r"Item:\s*(\d+)", html)
    print(f"  item={im.group(1) if im else '?'} BuyItNow={tiene_bin} AddToCart={tiene_cart} Bid={tiene_bid} MakeOffer={tiene_offer}")
    # texto visible del actionarea
    m = re.search(r'class="actionarea">(.*?)(?=<div|</div>)', html, re.S)
    if m:
        txt = re.sub(r"<[^>]+>", " ", m.group(1))
        print("  actionarea:", re.sub(r"\s+", " ", txt).strip()[:150])
    # buscar en el texto visible la palabra Auction o Sold Out
    limpio = re.sub(r"<script.*?</script>", "", html, flags=re.S)
    texto = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", limpio))
    for kw in ["Auction", "Sold Out", "This item is being auctioned", "auction"]:
        i = texto.find(kw)
        if i > -1:
            print(f"  '{kw}' en texto: {texto[max(0,i-60):i+120]}")
    print()
