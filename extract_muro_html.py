#!/usr/bin/env python3
"""extract_muro_html.py — extrae el muro (precios, copias, vendedores) de un HTML de COMC guardado.
Uso: extract_muro_html.py <archivo.html>"""
import re, sys, json

def parse_muro(html):
    items = re.findall(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', html)
    owners = {}
    for m in re.finditer(r'Owner: <strong><a href="/Users/([^"]+)"[^>]*>([^<]+)</a></strong>.*?Item: (\d+)', html, re.S):
        owners[m.group(3)] = m.group(2)
    muro = []
    for item_id, precio_txt in items:
        muro.append({"item_id": item_id, "precio": float(precio_txt.replace(",", "")),
                     "owner": owners.get(item_id, "?")})
    muro.sort(key=lambda x: x["precio"])
    return muro

def main():
    html = open(sys.argv[1], encoding="utf-8", errors="replace").read()
    muro = parse_muro(html)
    print(f"Items en muro: {len(muro)}")
    resumen = {}
    for m in muro:
        p = m["precio"]
        e = resumen.setdefault(p, {"copias": 0, "owners": []})
        e["copias"] += 1
        if m["owner"] not in e["owners"]:
            e["owners"].append(m["owner"])
    for p in sorted(resumen):
        e = resumen[p]
        print(f"  ${p:.2f}: {e['copias']} copias ({'/'.join(e['owners'])})")
    m = re.search(r'class="allsellers"[^>]*>.*?qtyforsale[^>]*>\s*&nbsp;?\((\d+)\)', html, re.S)
    if not m:
        m = re.search(r"All Sellers.*?qtyforsale.*?\((\d+)\)", html, re.S)
    print(f"Copias totales (qtyforsale): {m.group(1) if m else '?'}")

if __name__ == "__main__":
    main()
