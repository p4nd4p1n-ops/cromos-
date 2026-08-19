#!/usr/bin/env python3
"""dashboard_comc.py — CARTERA COMC estilo MetaMask (Pin 13/08/2026).
Cada carta = activo con valor, P&L ($ y %), cambio del día. Total arriba.
Clic en una carta → ficha: muro completo, vendedores, copias, v7d, enlace COMC.
P&L neto estimado = precio_ref × 0.95 (fee) − coste; precio_ref = nuestra lista
si está por debajo del muro, si no el muro (lo que competiría hoy).
Uso: dashboard_comc.py [--out salida.html]
"""
import subprocess, json, sys, os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

SSH = ["ssh", "-J", "root@100.89.234.7", "root@192.168.0.102"]
DATA_DIR = "/root/comc-data"
OUT = "/root/.openclaw/workspace/comc/dashboard-comc.html"
GOG = "/root/.config/gogcli/run-gog.sh"
SHEET_ID = "1akdKxf9d5I6u8rM6z0EuwU7AtUujpj3ffVuadjtCH1s"

BASE_INICIAL = {
    "TC25-251.1-B": (24.49, 24.89), "TC25-271.1-B": (0.87, 0.87),
    "TC25-268.1-B": (0.60, 0.64), "TC25-264-B": (1.02, 1.10),
    "TC25-228.1-B": (0.89, 0.95), "TC25-253.1-B": (1.80, 2.00),
    "TC25-252.1-B": (7.25, 7.50), "TC25-254.1-B": (3.50, 3.69),
    "DOPT24-248-B": (4.30, 4.50), "BUC24-22-B": (0.98, 0.99),
}

URLS = {
    "TC25-251.1-B": "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2511/Cooper_Flagg/31038638",
    "TC25-271.1-B": "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2711/Will_Riley/31038659",
    "TC25-268.1-B": "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2681/Walter_Clayton_Jr/31038656",
    "TC25-264-B":   "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/264/Carter_Bryant/31038652",
    "TC25-228.1-B": "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2281/Stephon_Castle/31038614",
    "TC25-253.1-B": "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2531/VJ_Edgecombe/31038640",
    "TC25-252.1-B": "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639",
    "TC25-254.1-B": "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2541/Kon_Knueppel/31038641",
    "DOPT24-248-B": "https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190",
    "BUC24-22-B":   "https://www.comc.com/Cards/Basketball/2024-25/Bowman_University_Chrome_-_Base/22/Dylan_Harper/28629778",
    "PM-HUGO":      "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2781/Hugo_Gonzalez/31038666",
    "PM-CURRY135":  "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/135/Stephen_Curry/30579169",
    "PM-WEMBY195":  "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/195/Victor_Wembanyama/30579229",
    "PM-HARPER202": "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/202/Dylan_Harper/30579236",
    "PM-FLAGGH161": "https://www.comc.com/Cards/Basketball/2025-26/Topps_Holiday_-_Base/H161/Cooper_Flagg/30774590",
    "PM-CURRYMP":   "https://www.comc.com/Cards/Basketball/2023-24/Panini_Prizm_Monopoly_-_Prizm_Skills/PS8/Stephen_Curry/25179047",
    "PM-BRONNY1":   "https://www.comc.com/Cards/Basketball/2024-25/Topps_Now_-_Online_Exclusive_Base/1/Bronny_James_LeBron_James/26528513",
    "PM-WILL50":    "https://www.comc.com/Cards/Football/2022/Bowman_University_Chrome_-_Base/501/Caleb_Williams/22165612",
    "PM-DANPRIZ347":"https://www.comc.com/Cards/Football/2024/Panini_Prizm_-_Base/347/Rookies_-_Jayden_Daniels/27382105",
    "OP-007":       "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038608",
    "OP-008":       "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/201/Cooper_Flagg/30579235",
}


def get_snapshot():
    r = subprocess.run(SSH + ["cat", f"{DATA_DIR}/inventario-scan.json"],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise SystemExit(f"ssh error: {r.stderr}")
    return json.loads(r.stdout)


def get_hoja():
    """{codigo: {coste, be, lista, estado}} desde la hoja Inventario (TSV)."""
    r = subprocess.run([GOG, "-p", "sheets", "get", SHEET_ID, "Inventario!A1:L16"],
                       capture_output=True, text=True, timeout=90)
    out = {}
    if r.returncode != 0:
        return out
    lines = [l for l in r.stdout.splitlines() if l.strip()][1:]
    for line in lines:
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        cod = parts[0].strip()
        def num(s):
            try:
                return float(s.replace("$", "").replace(",", ""))
            except Exception:
                return None
        lista_raw = parts[6].strip()
        lista_val = num(lista_raw.split(" ")[0]) if lista_raw else None
        estado = ""
        if "HOLD" in lista_raw.upper():
            estado = "HOLD"
        elif "list" in lista_raw.lower():
            estado = "LIST"
        else:
            estado = "NO_VENTA"
        out[cod] = {"coste": num(parts[3]), "be": num(parts[4]),
                    "lista": lista_val, "estado": estado, "lista_raw": lista_raw}
    return out


def fmt_fecha(fecha):
    try:
        dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return dt.astimezone(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return fecha


def pnl(coste, precio_ref):
    """P&L neto: (precio_ref × 0.95 − coste) / coste → ($, %)."""
    if coste is None or precio_ref is None:
        return None, None
    neto = precio_ref * 0.95
    d = neto - coste
    pct = d / coste * 100 if coste else 0
    return d, pct


def tarjeta_activo(d, base, hoja):
    """Tarjeta estilo token: nombre, precio, % P&L coloreado, valor. <details> = ficha."""
    cod, nom = d["codigo"], d["nombre"]
    if "min" not in d:
        return f"<details class='card err'><summary><b>{cod}</b> {nom} — ❌ {d.get('error','')}</summary></details>"
    h = hoja.get(cod, {})
    coste = h.get("coste")
    estado = h.get("estado", "")
    # precio_ref: nuestra lista si es < muro; si no, muro (lo que competiría hoy)
    ref = d["min"]
    if h.get("lista") is not None and (estado == "LIST"):
        ref = min(h["lista"], d["min"])
    d_, pct = pnl(coste, ref)
    # cambio del día vs baseline
    min_ant = base.get(cod, (None,))[0]
    flecha, tipo = ("=", "igual")
    if min_ant is not None and abs(min_ant - d["min"]) >= 0.005:
        flecha, tipo = ("⬇", "baja") if d["min"] < min_ant else ("⬆", "suba")
    color_pnl = "#2ecc71" if (pct or 0) >= 0 else "#e74c3c"
    color_dia = {"baja": "#e74c3c", "suba": "#2ecc71", "igual": "#7f8c8d"}[tipo]
    badge = {"LIST": "<span class='b b-list'>LIST</span>", "HOLD": "<span class='b b-hold'>HOLD</span>",
             "NO_VENTA": ""}.get(estado, "")
    pnl_txt = "—"
    if pct is not None:
        pnl_txt = f"{'+' if d_ >= 0 else ''}{d_:.2f}$ ({'+' if pct >= 0 else ''}{pct:.1f}%)"
    val_txt = f"${ref:.2f}" if ref is not None else "—"
    cos_txt = f"${coste:.2f}" if coste is not None else "—"
    url = d.get("url") or URLS.get(cod, "#")
    # ficha expandida
    muro_html = d.get("muro_txt", "").replace("; ", "<br>")
    partes = []
    if muro_html:
        partes.append(f"<div class='muro'><b>Muro completo:</b><br>{muro_html}</div>")
    be_txt = f"${h['be']:.2f}" if h.get("be") is not None else "—"
    meta = (f"<div class='meta'>1º ${d['min']:.2f} · 2º ${d['seg']:.2f} · copias {d['copias_totales']}"
            f" · ventas 7d {d['v7d']} · coste {cos_txt} · break-even {be_txt}"
            f" · 1er: {'/'.join(d.get('owners_1er') or ['?'])}</div>")
    cuerpo = (f"<div class='cuerpo'>{meta}{partes[0] if partes else ''}"
              f"<div><a href='{url}' target='_blank'>Ver en COMC ↗</a></div></div>")
    summary = (f"<summary><span class='ic'>🃏</span>"
               f"<span class='nm'>{nom} <small>{cod}</small>{badge}</span>"
               f"<span class='vl'>${ref:.2f}</span>"
               f"<span class='pnl' style='color:{color_pnl}'>{pnl_txt}</span>"
               f"<span class='dia' style='color:{color_dia}'>{flecha} {d['min']:.2f}</span></summary>")
    return f"<details class='card'>{summary}{cuerpo}</details>"


def main():
    snap = get_snapshot()
    fecha = fmt_fecha(snap.get("fecha", "?"))
    hoja = get_hoja()
    niveles = snap.get("niveles", {})
    n1 = niveles.get("N1", []); n2 = niveles.get("N2", []); n3 = niveles.get("N3", [])
    # totales de la cartera
    tot_coste = tot_valor = 0.0
    activos = []
    for d in n1:
        if "min" not in d:
            continue
        h = hoja.get(d["codigo"], {})
        coste = h.get("coste")
        ref = d["min"]
        if h.get("lista") is not None and h.get("estado") == "LIST":
            ref = min(h["lista"], d["min"])
        if coste:
            tot_coste += coste
            tot_valor += ref * 0.95
            activos.append((d["codigo"], d["nombre"], ref, coste))
    pnl_tot = tot_valor - tot_coste
    pnl_tot_pct = pnl_tot / tot_coste * 100 if tot_coste else 0
    css = """
    *{box-sizing:border-box}body{font-family:system-ui,sans-serif;margin:0;padding:18px;background:#101018;color:#e8e8f0}
    h1{font-size:20px;margin:0;color:#fff}h1 small{color:#8a8aa0;font-weight:normal;font-size:13px}
    .tot{background:#1a1a2e;border:1px solid #2a2a44;border-radius:14px;padding:16px;margin:12px 0 18px;text-align:center}
    .tot .lbl{color:#8a8aa0;font-size:12px;text-transform:uppercase;letter-spacing:1px}
    .tot .big{font-size:30px;font-weight:800;color:#fff;margin:2px 0}
    .tot .sub{font-size:13px;color:#8a8aa0}.pos{color:#2ecc71}.neg{color:#e74c3c}
    h2{font-size:14px;color:#8a8aa0;text-transform:uppercase;letter-spacing:1px;margin:20px 0 8px;border-bottom:1px solid #2a2a44;padding-bottom:6px}
    .card{background:#1a1a2e;border:1px solid #2a2a44;border-radius:12px;margin:6px 0;overflow:hidden}
    .card summary{cursor:pointer;padding:11px 14px;font-size:14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
    .card summary:hover{background:#22223a}
    .ic{font-size:18px}.nm{flex:1;min-width:150px}.nm small{color:#8a8aa0;font-size:11px;margin-left:6px}
    .vl{font-weight:700;color:#fff;font-variant-numeric:tabular-nums}
    .pnl{font-weight:700;font-variant-numeric:tabular-nums;min-width:90px;text-align:right}
    .dia{font-size:12px;color:#8a8aa0;min-width:60px;text-align:right}
    .b{font-size:10px;padding:2px 6px;border-radius:6px;margin-left:6px;vertical-align:middle}
    .b-list{background:#2ecc7122;color:#2ecc71;border:1px solid #2ecc7155}
    .b-hold{background:#f39c1222;color:#f39c12;border:1px solid #f39c1255}
    .cuerpo{padding:12px 14px;border-top:1px solid #2a2a44;font-size:13px;background:#16162a}
    .muro{background:#101018;border:1px solid #2a2a44;border-radius:8px;padding:8px 10px;margin:8px 0;line-height:1.7;color:#c8c8d8}
    .meta{color:#8a8aa0;font-size:12px;margin-bottom:6px;line-height:1.6}
    a{color:#4aa3ff;text-decoration:none}small{color:#8a8aa0}
    .err summary{color:#e74c3c}
    .foot{color:#666;font-size:11px;margin-top:14px}
    """
    cls_tot = "pos" if pnl_tot >= 0 else "neg"
    sign = "+" if pnl_tot >= 0 else ""
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cartera COMC — {fecha}</title><style>{css}</style></head><body>
<h1>🛸 Cartera COMC <small>· {fecha}</small></h1>
<div class='tot'>
  <div class='lbl'>Valor cartera (neto estimado)</div>
  <div class='big'>${tot_valor:.2f}</div>
  <div class='sub'>Coste ${tot_coste:.2f} · <span class='{cls_tot}'>{sign}${pnl_tot:.2f} ({sign}{pnl_tot_pct:.1f}%)</span> · {len(n1)} activos</div>
</div>
<h2>📦 Inventario ({len(n1)})</h2>
{''.join(tarjeta_activo(d, BASE_INICIAL, hoja) for d in n1)}
<h2>🎯 Objetivos ({len(n2)})</h2>
{''.join(tarjeta_activo(d, {}, {}) for d in n2)}
<h2>📨 Ofertadas ({len(n3)})</h2>
{''.join(tarjeta_activo(d, {}, {}) for d in n3)}
<div class='foot'>P&amp;L neto = precio_ref × 0.95 (fee 5%) − coste · precio_ref = nuestra lista si está bajo el muro, si no el muro · clic en cada carta para su ficha</div>
</body></html>"""
    out = OUT
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]
    with open(out, "w") as fh:
        fh.write(html)
    print(f"✅ Cartera: {out} | valor ${tot_valor:.2f} | P&L {sign}${pnl_tot:.2f} ({sign}{pnl_tot_pct:.1f}%)")

if __name__ == "__main__":
    main()
