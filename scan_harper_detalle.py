#!/usr/bin/env python3
"""scan_harper_detalle.py — escanea Harper Chrome con el parser detallado:
ventas con tipo de transacción, exclusión de lotes, media corregida."""
import json, time, datetime, statistics, sys, os
sys.path.insert(0, "/root/comc-scripts")
from fino_scan import fs, get_html, parse_card, parse_muro, parse_sales_detallado

URL = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"

def main():
    try:
        fs({"cmd": "sessions.destroy", "session": "ghost"}, timeout=30000)
    except Exception:
        pass
    time.sleep(2)
    html = get_html(URL)
    if not html:
        print(json.dumps({"error": "sin_html"}, ensure_ascii=False)); return

    d = parse_card(html)
    muro, muro_resumen = parse_muro(html)
    sales_det = parse_sales_detallado(html)

    # ventas individuales reales: sin lotes (offer) y sin gradadas
    ventas_reales = [s for s in sales_det
                     if "offer" not in s["tipo"].lower() and not s["grado"]]
    lotes = [s for s in sales_det if "offer" in s["tipo"].lower()]
    gradadas = [s for s in sales_det if s["grado"]]

    print("=== VENTAS DETALLE (todas) ===", flush=True)
    for s in sales_det:
        g = f" [GRADO: {s['grado'][:30]}]" if s["grado"] else ""
        print(f"{s['fecha']} {s['hora']} | ${s['precio']} | {s['tipo']}{g}", flush=True)

    print("=== RESUMEN ===", flush=True)
    print(f"ventas totales capturadas: {len(sales_det)}", flush=True)
    print(f"lotes excluidos: {len(lotes)}", flush=True)
    print(f"gradadas excluidas: {len(gradadas)}", flush=True)
    print(f"ventas individuales reales: {len(ventas_reales)}", flush=True)

    hoy = datetime.date.today()
    def en7d(s):
        try:
            f = datetime.datetime.strptime(s["fecha"], "%b %d, %Y").date()
            return (hoy - f).days <= 7
        except ValueError:
            return False

    r7 = [s["precio"] for s in ventas_reales if en7d(s)]
    crudo7 = [s["precio"] for s in sales_det if en7d(s)]
    if r7:
        print(f"MEDIA 7d REAL (sin lotes): ${round(statistics.mean(r7),2)}  (n={len(r7)})", flush=True)
        print(f"MEDIA 7d CRUDA (con lotes): ${round(statistics.mean(crudo7),2)}  (n={len(crudo7)})", flush=True)
        print(f"ventas reales 7d ordenadas: {sorted(r7)}", flush=True)
    else:
        print("sin ventas individuales en 7d", flush=True)
    print("OK", flush=True)

if __name__ == "__main__":
    main()
