#!/usr/bin/env python3
"""quien_vendio.py <url> — extrae las ventas recientes del HTML con su VENDEDOR si está.
Busca filas de historial de ventas y el usuario asociado. 12/08/2026."""
import sys, re, json
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

def main():
    url = sys.argv[1]
    html = ms.get_html(url)
    if not html or len(html) < 2000:
        print(json.dumps({"error": "sin_html"}))
        return
    # 1) intentar filas de ventas recientes con vendedor: buscar patrones fecha + precio + /Users/
    print("=== VENTAS CON VENDEDOR (patrón fecha+precio+user) ===")
    # patrón: fecha, luego precio, y un /Users/NAME cerca
    pat = re.compile(
        r"([A-Z][a-z]{2} \d{1,2}, \d{4}).{0,400}?\$([\d,]+\.\d{2}).{0,200}?/Users/([A-Za-z0-9_.-]+)",
        re.S)
    vistos = set()
    for m in pat.finditer(html):
        k = (m.group(1), m.group(2), m.group(3))
        if k in vistos:
            continue
        vistos.add(k)
        print(f"  {m.group(1)} | ${m.group(2)} | {m.group(3)}")
        if len(vistos) >= 15:
            break

    # 2) contexto alrededor de la venta a 0.92 (11 Aug)
    print("\n=== CONTEXTO '0.92' en HTML ===")
    for m in re.finditer(r"0\.92", html):
        s = max(0, m.start() - 300)
        ctx = re.sub(r"<[^>]+>", " ", html[s:m.start() + 100])
        ctx = re.sub(r"\s+", " ", ctx).strip()
        print(f"  ...{ctx[-200:]}")
        if m.start() > 200000:  # limitar a los primeros matches
            break

    # 3) buscar bloques de historial de ventas típicos
    print("\n=== ESTRUCTURA HISTORIAL (clases/ids) ===")
    for cls in re.findall(r'class="([^"]*(?:sale|hist|trans)[^"]*)"', html, re.I)[:10]:
        print(f"  .{cls}")

if __name__ == "__main__":
    main()
