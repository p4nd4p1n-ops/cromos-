#!/usr/bin/env python3
"""inventario_scan.py — SCAN DE LA MAÑANA (objetivo nº1 = inventario + cambios).
Orden de importancia (regla Pin 13/08/2026):
  N1: INVENTARIO  — cartas que tenemos (muro 1er/2º escalón, vendedores, copias, v7d)
  N2: OBJETIVOS   — punto de mira
  N3: OFERTADAS   — cartas con oferta enviada/pendiente
Compara con el snapshot anterior → marca CAMBIOS (⬇️/⬆️/=).
Guarda: inventario-scan-<fecha>.json (histórico) + inventario-scan.json (último, para comparar).
Uso:
  inventario_scan.py              → scan completo
  inventario_scan.py --solo A,B   → solo esos códigos (test)
  inventario_scan.py --compare    → compara los 2 últimos snapshots sin bajar nada
"""
import json, re, time, random, datetime, os, sys

sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

DATA_DIR = "/root/comc-data"
ULTIMO = os.path.join(DATA_DIR, "inventario-scan.json")

# ── N1: INVENTARIO (fuente: hoja COMC, 13/08/2026) ──────────────────────────
INVENTARIO = [
    ("TC25-251.1-B", "Flagg Chrome #251.1",        "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2511/Cooper_Flagg/31038638"),
    ("TC25-271.1-B", "Riley Chrome #271.1",        "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2711/Will_Riley/31038659"),
    ("TC25-268.1-B", "Clayton Chrome #268.1",      "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2681/Walter_Clayton_Jr/31038656"),
    ("TC25-264-B",   "Bryant Chrome #264",         "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/264/Carter_Bryant/31038652"),
    ("TC25-228.1-B", "Castle Chrome #228.1",       "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2281/Stephon_Castle/31038614"),
    ("TC25-253.1-B", "Edgecombe Chrome #253.1",    "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2531/VJ_Edgecombe/31038640"),
    ("TC25-252.1-B", "Harper Chrome #252.1",       "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"),
    ("TC25-254.1-B", "Knueppel Chrome #254.1",     "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2541/Kon_Knueppel/31038641"),
    ("DOPT24-248-B", "Daniels Optic #248 (NFL)",   "https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190"),
    ("BUC24-22-B",   "Harper Bowman Univ #22",     "https://www.comc.com/Cards/Basketball/2024-25/Bowman_University_Chrome_-_Base/22/Dylan_Harper/28629778"),
]

# ── N2: OBJETIVOS / PUNTO DE MIRA (fuente: CANDIDATAS-COMPRA.md + REGISTRO-PUNTO-MIRA.md) ──
OBJETIVOS = [
    ("PM-CURRY135",  "Curry Topps #135",             "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/135/Stephen_Curry/30579169"),
    ("PM-WEMBY195",  "Wemby Topps #195",             "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/195/Victor_Wembanyama/30579229"),
    ("PM-HARPER202", "Harper Topps #202",            "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/202/Dylan_Harper/30579236"),
    ("PM-FLAGGH161", "Flagg Holiday #H161",          "https://www.comc.com/Cards/Basketball/2025-26/Topps_Holiday_-_Base/H161/Cooper_Flagg/30774590"),
    ("PM-CURRYMP",   "Curry Monopoly PS8",           "https://www.comc.com/Cards/Basketball/2023-24/Panini_Prizm_Monopoly_-_Prizm_Skills/PS8/Stephen_Curry/25179047"),
    ("PM-BRONNY1",   "Bronny+LeBron Topps Now #1",   "https://www.comc.com/Cards/Basketball/2024-25/Topps_Now_-_Online_Exclusive_Base/1/Bronny_James_LeBron_James/26528513"),
    ("PM-DANPRIZ347","Daniels Prizm #347 (NFL)",     "https://www.comc.com/Cards/Football/2024/Panini_Prizm_-_Base/347/Rookies_-_Jayden_Daniels/27382105"),
]

# ── N3: OFERTADAS (oferta enviada/pendiente) ─────────────────────────────────
OFERTADAS = [
    ("OP-007", "Wemby Chrome #221.1 (IvIase $2.00)", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038608"),
    ("OP-008", "Flagg Topps #201 (shawnmenard $3.20)", "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/201/Cooper_Flagg/30579235"),
]

def _carga_inv():
    import os
    ruta = "/root/comc-data/inventario.txt"
    if not os.path.exists(ruta):
        return INVENTARIO
    out = []
    for ln in open(ruta, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        f = [x.strip() for x in ln.split(";")]
        if len(f) >= 3:
            out.append((f[0], f[1], f[2]))
    return out or INVENTARIO

NIVELES = [("N1", "INVENTARIO", _carga_inv()), ("N2", "OBJETIVOS", OBJETIVOS), ("N3", "OFERTADAS", OFERTADAS)]


def extrae_ventas7d(html):
    """Ventas reales de los últimos 7 días completos.
    Fix 13/08: el regex viejo contaba fechas sin hora (listados/otras fechas)
    y usaba <=7 días → inflaba con ventas del día límite (caso Williams: 12 falsas del 06/08).
    Fix 17/08 (L-027): exigir fecha+hora AM/PM lo rompió TODO (daba v7d=0 en todas,
    verificado 17/08: Flagg 0 vs fino real 8). COMC ya no muestra la hora en las ventas
    recientes → mismo patrón que muro_fino_inventario.py (fecha + precio, validado 8/8).
    Ventana estricta (hoy-fecha) < 7 días para no repetir el bug Williams."""
    sales = re.findall(
        r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)
    hoy = datetime.date.today()
    v7 = 0
    for fstr, _ in sales:
        try:
            dias = (hoy - datetime.datetime.strptime(fstr, "%b %d, %Y").date()).days
            if 0 <= dias < 7:
                v7 += 1
        except ValueError:
            pass
    return v7


def scan_carta(codigo, nombre, url):
    """1 petición FS → muro. Devuelve dict con min/seg/copias/v7d o error."""
    html = ms.get_html(url)
    if not html or len(html) < 2000:
        return {"codigo": codigo, "nombre": nombre, "error": "sin_html"}
    try:
        muro, resumen = ms.parse_muro(html)
    except Exception as e:
        return {"codigo": codigo, "nombre": nombre, "error": f"parse: {e}"}
    if not muro:
        return {"codigo": codigo, "nombre": nombre, "error": "muro_vacio"}
    precios = sorted(resumen.keys())
    p1, p2 = precios[0], (precios[1] if len(precios) > 1 else None)
    e1 = resumen[p1]
    # copias totales (fallback: nº de items visibles en el muro)
    copias = None
    m = re.search(r'class="allsellers"[^>]*>.*?qtyforsale[^>]*>\s*&nbsp;?\((\d+)\)', html, re.S)
    if m:
        copias = int(m.group(1))
    if copias is None:
        copias = len(muro)
    muro_txt = "; ".join(f"{p}: {e['copias']} ({'/'.join(e['owners'])})" for p, e in sorted(resumen.items()))
    return {
        "codigo": codigo, "nombre": nombre, "url": url,
        "min": p1, "seg": p2, "copias_1er": e1["copias"], "owners_1er": e1["owners"],
        "mismo_owner_1er": e1["mismo_owner"], "copias_totales": copias,
        "v7d": extrae_ventas7d(html), "muro_txt": muro_txt[:500],
    }


def fmt_cambio(viejo, nuevo):
    """Devuelve '⬇️ 7.25→5.50 (-24%)' / '⬆️ ...' / '=' """
    if viejo is None or nuevo is None:
        return ""
    if viejo == nuevo:
        return "="
    pct = (nuevo - viejo) / viejo * 100
    flecha = "⬇️" if nuevo < viejo else "⬆️"
    return f"{flecha} {viejo}→{nuevo} ({pct:+.0f}%)"


def linea_resultado(d, prev):
    if d.get("error"):
        return f"  ❌ {d['codigo']} {d['nombre']}: {d['error']}"
    prev_min = prev.get(d["codigo"], {}).get("min") if prev else None
    prev_cop = prev.get(d["codigo"], {}).get("copias_totales") if prev else None
    camb_min = fmt_cambio(prev_min, d["min"])
    camb_cop = ""
    if prev_cop is not None and prev_cop != d["copias_totales"]:
        delta = d["copias_totales"] - prev_cop
        camb_cop = f" | copias {prev_cop}→{d['copias_totales']} ({delta:+d})"
    prev_seg = prev.get(d["codigo"], {}).get("seg") if prev else None
    seg = f" | 2º ${d['seg']} {fmt_cambio(prev_seg, d['seg'])}" if d["seg"] is not None else ""
    owners = "/".join(d["owners_1er"])
    return (f"  {d['codigo']} {d['nombre']}: 1º ${d['min']} {camb_min}{seg}"
            f" | 1er escalón {d['copias_1er']} ({owners})"
            f"{camb_cop} | total {d['copias_totales']} | v7d {d['v7d']}")


def main():
    solo = None
    if len(sys.argv) > 1 and sys.argv[1] == "--solo":
        solo = set(sys.argv[2].split(","))
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        # comparar los 2 últimos snapshots históricos
        snaps = sorted(f for f in os.listdir(DATA_DIR) if f.startswith("inventario-scan-"))
        if len(snaps) < 2:
            print("No hay 2 snapshots para comparar")
            return
        a = json.load(open(os.path.join(DATA_DIR, snaps[-2])))
        b = json.load(open(os.path.join(DATA_DIR, snaps[-1])))
        print(f"COMPARACIÓN {a['fecha']} → {b['fecha']}")
        for nivel in ["N1", "N2", "N3"]:
            pa = {x["codigo"]: x for x in a["niveles"].get(nivel, []) if "min" in x}
            pb = {x["codigo"]: x for x in b["niveles"].get(nivel, []) if "min" in x}
            print(f"[{nivel}]")
            for cod in pb:
                if cod in pa:
                    print(linea_resultado(pb[cod], {cod: pa[cod]}))
                else:
                    print(f"  ➕ nuevo: {cod} {pb[cod]['nombre']} 1º ${pb[cod]['min']}")
        return

    # carga snapshot anterior (para comparar cambios)
    prev = {}
    if os.path.exists(ULTIMO):
        try:
            pj = json.load(open(ULTIMO))
            for nivel in pj["niveles"].values():
                for x in nivel:
                    if "min" in x:
                        prev[x["codigo"]] = x
        except Exception:
            pass

    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"=== INVENTARIO SCAN {ahora} ===")
    print(f"Baseline: {'sí (' + str(len(prev)) + ' cartas)' if prev else 'NO (primera vez)'}")
    resultado = {"fecha": ahora, "niveles": {}}
    total_ok = 0
    total_err = 0
    primera = True
    for nivel, nombre, cartas in NIVELES:
        lista = [c for c in cartas if not solo or c[0] in solo]
        if not lista:
            continue
        print(f"\n[{nivel} {nombre}]")
        resultado["niveles"][nivel] = []
        for codigo, nom, url in lista:
            if not primera:
                time.sleep(random.uniform(25, 35))  # regla FS: espaciar SIEMPRE
            primera = False
            d = scan_carta(codigo, nom, url)
            resultado["niveles"][nivel].append(d)
            if "min" in d:
                total_ok += 1
                print(linea_resultado(d, prev))
            else:
                total_err += 1
                print(linea_resultado(d, None))
    # ── RESUMEN A PRIMERA VISTA (Pin 13/08): qué cambia y qué no ──
    if prev:
        cambiadas, iguales, nuevas = [], [], []
        for nivel, nombre, cartas in NIVELES:
            for d in resultado["niveles"].get(nivel, []):
                if "min" not in d:
                    continue
                p = prev.get(d["codigo"])
                if not p or "min" not in p:
                    nuevas.append((nivel, d))
                elif (p["min"] != d["min"] or p.get("seg") != d.get("seg")
                      or p.get("copias_totales") != d.get("copias_totales")):
                    cambiadas.append((nivel, d, p))
                else:
                    iguales.append((nivel, d))
        resumen_lines = []
        resumen_lines.append("=== 🔴 CAMBIOS ===")
        for nivel, d, p in cambiadas:
            l = f"[{nivel}] {d['codigo']} {d['nombre']}: 1º {fmt_cambio(p.get('min'), d['min'])} | 2º {fmt_cambio(p.get('seg'), d.get('seg'))}"
            if p.get("copias_totales") != d.get("copias_totales"):
                l += f" | copias {p.get('copias_totales')}→{d['copias_totales']}"
            resumen_lines.append("  " + l)
        for nivel, d in nuevas:
            resumen_lines.append(f"  ➕ [{nivel}] {d['codigo']} {d['nombre']}: NUEVA (1º ${d['min']}, 2º ${d.get('seg')})")
        resumen_lines.append("=== ⚪ SIN CAMBIOS ===")
        for nivel, d in iguales:
            resumen_lines.append(f"  [{nivel}] {d['codigo']} {d['nombre']} (1º ${d['min']}, 2º ${d.get('seg')})")
        print("\n" + "\n".join(resumen_lines))
        # guardar reporte legible del día
        try:
            with open(os.path.join(DATA_DIR, f"inventario-reporte-{stamp}.txt"), "w") as fh:
                fh.write(f"INVENTARIO SCAN {ahora}\n" + "\n".join(resumen_lines) + "\n")
        except Exception:
            pass
    # guardar histórico + último
    hist = os.path.join(DATA_DIR, f"inventario-scan-{stamp}.json")
    json.dump(resultado, open(hist, "w"), ensure_ascii=False, indent=1)
    json.dump(resultado, open(ULTIMO, "w"), ensure_ascii=False, indent=1)
    print(f"\n=== FIN: {total_ok} OK, {total_err} errores → {hist} ===")


if __name__ == "__main__":
    main()
