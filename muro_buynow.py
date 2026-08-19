#!/usr/bin/env python3
"""MURO REAL con filtro BuyItNow (L-022).
Escanea la carta, extrae el muro, y verifica los primeros N vendedores
pidiendo su página de item individual. Solo los que tienen BuyItNow
son escalones de compra directa. 11/08/2026.
Uso: muro_buynow.py <url_carta> [max_verificar]
"""
import sys, re, time, random
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

def muro_carta(url):
    html = ms.get_html(url)
    if not html or len(html) < 2000:
        return None, "sin_html"
    filas = []
    for r in re.findall(r"<tr>(.*?)</tr>", html, re.S):
        if 'class="seller"' in r and 'displayprice' in r and 'soldout' not in r and 'allsellers' not in r:
            pm = re.search(r'class="price">\$([\d.]+)', r)
            vm = re.search(r'/Users/([A-Za-z0-9_.-]+)', r)
            if pm and vm:
                filas.append({"precio": float(pm.group(1)), "vendedor": vm.group(1)})
    filas.sort(key=lambda x: x["precio"])
    return filas, None

def es_buynow(vendedor, card_path):
    """Pide la pagina del item del vendedor y comprueba BuyItNow."""
    url = f"https://www.comc.com/Users/{vendedor}/Cards/{card_path}"
    html = ms.get_html(url)
    if not html:
        return None  # sin_html: no sabemos
    tiene_bin = bool(re.search(r"BuyItNow|buyitnow", html))
    tiene_cart = bool(re.search(r"Add to Cart", html))
    return tiene_bin and tiene_cart

def main():
    if len(sys.argv) < 2:
        print("Uso: muro_buynow.py <url_carta> [max_verificar]")
        sys.exit(1)
    url = sys.argv[1]
    max_ver = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    # extraer el card_path de la url (/Users/X/Cards/<path>)
    m = re.search(r"/Cards/(.+?)(?:/Graded|$)", url)
    if not m:
        print("No puedo extraer card_path de la URL")
        sys.exit(1)
    card_path = m.group(1)
    print(f"CARD: {card_path}")

    filas, err = muro_carta(url)
    if err:
        print(f"ERROR: {err}")
        sys.exit(1)
    print(f"Muro: {len(filas)} vendedores")

    # verificar los primeros max_ver vendedores
    verificados = 0
    escalones_real = []
    for f in filas[:max_ver]:
        print(f"  verificando {f['vendedor']} (${f['precio']:.2f})...", flush=True)
        ok = es_buynow(f["vendedor"], card_path)
        if ok is None:
            print(f"    sin_html — reintento en 30s", flush=True)
            time.sleep(30)
            ok = es_buynow(f["vendedor"], card_path)
        estado = "BUYNOW ✅" if ok else ("subasta/soldout ❌" if ok is False else "desconocido ?")
        print(f"    -> {estado}", flush=True)
        if ok:
            escalones_real.append(f)
        verificados += 1
        if len(escalones_real) >= 2:
            break
        if verificados < len(filas[:max_ver]):
            time.sleep(random.randint(25, 35))

    if not escalones_real:
        print("\nSIN escalones de compra directa en los primeros", max_ver)
        return
    print("\n=== MURO REAL (solo BuyItNow) ===")
    for e in escalones_real:
        print(f"  ${e['precio']:.2f} | {e['vendedor']}")
    if len(escalones_real) >= 2:
        gap = (escalones_real[1]["precio"] - escalones_real[0]["precio"]) / escalones_real[0]["precio"] * 100
        print(f"GAP REAL: {gap:.1f}%")
    else:
        print("Solo 1 escalón verificado — faltan más verificaciones")

if __name__ == "__main__":
    main()
