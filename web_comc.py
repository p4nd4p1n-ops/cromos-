#!/usr/bin/env python3
"""web_comc.py — genera la WEB LOCAL de la cartera COMC (Pin 13/08/2026).
- index.html con las 21 cartas (10 inventario + 9 objetivos + 2 ofertadas)
- main: coste, break-even, mercado (1º/2º escalón + nuestra lista), P&L, mini-gráfica
  de EVOLUCIÓN del muro (1er escalón) desde el primer snapshot que tenemos
- ficha por carta: por qué la compré (DIARIO-OPERACIONES), historial, enlace COMC
Corre en el VPS (usa gog para la hoja) y sube el HTML al CT kobe (red local de Pin).
"""
import subprocess, json, sys, os, re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

SSH = ["ssh", "-J", "root@100.89.234.7", "root@192.168.0.102"]
GOG = "/root/.config/gogcli/run-gog.sh"
SHEET_ID = "1akdKxf9d5I6u8rM6z0EuwU7AtUujpj3ffVuadjtCH1s"
WEB_DIR_CT = "/root/comc-web"
OUT_LOCAL = "/root/.openclaw/workspace/comc/index.html"

# ── las 21 cartas: (codigo, nombre, id_comc, url) ─────────────────────────────
CARTAS = [
    # inventario
    ("TC25-251.1-B", "Flagg Chrome #251.1", "31038638", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2511/Cooper_Flagg/31038638"),
    ("TC25-271.1-B", "Riley Chrome #271.1", "31038659", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2711/Will_Riley/31038659"),
    ("TC25-268.1-B", "Clayton Chrome #268.1", "31038656", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2681/Walter_Clayton_Jr/31038656"),
    ("TC25-264-B", "Bryant Chrome #264", "31038652", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/264/Carter_Bryant/31038652"),
    ("TC25-228.1-B", "Castle Chrome #228.1", "31038614", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2281/Stephon_Castle/31038614"),
    ("TC25-253.1-B", "Edgecombe Chrome #253.1", "31038640", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2531/VJ_Edgecombe/31038640"),
    ("TC25-252.1-B", "Harper Chrome #252.1", "31038639", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"),
    ("TC25-254.1-B", "Knueppel Chrome #254.1", "31038641", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2541/Kon_Knueppel/31038641"),
    ("DOPT24-248-B", "Daniels Optic #248", "28874190", "https://www.comc.com/Cards/Football/2024/Panini_Donruss_Optic_-_Base/248/Rated_Rookie_-_Jayden_Daniels/28874190"),
    ("BUC24-22-B", "Harper Bowman Univ #22", "28629778", "https://www.comc.com/Cards/Basketball/2024-25/Bowman_University_Chrome_-_Base/22/Dylan_Harper/28629778"),
    # objetivos
    ("PM-HUGO", "Hugo Gonzalez Chrome #278.1", "31038666", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2781/Hugo_Gonzalez/31038666"),
    ("PM-CURRY135", "Curry Topps #135", "30579169", "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/135/Stephen_Curry/30579169"),
    ("PM-WEMBY195", "Wemby Topps #195", "30579229", "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/195/Victor_Wembanyama/30579229"),
    ("PM-HARPER202", "Harper Topps #202", "30579236", "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/202/Dylan_Harper/30579236"),
    ("PM-FLAGGH161", "Flagg Holiday #H161", "30774590", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Holiday_-_Base/H161/Cooper_Flagg/30774590"),
    ("PM-CURRYMP", "Curry Monopoly PS8", "25179047", "https://www.comc.com/Cards/Basketball/2023-24/Panini_Prizm_Monopoly_-_Prizm_Skills/PS8/Stephen_Curry/25179047"),
    ("PM-BRONNY1", "Bronny+LeBron Topps Now #1", "26528513", "https://www.comc.com/Cards/Basketball/2024-25/Topps_Now_-_Online_Exclusive_Base/1/Bronny_James_LeBron_James/26528513"),
    ("PM-WILL50", "Williams Bowman Univ #50.1", "22165612", "https://www.comc.com/Cards/Football/2022/Bowman_University_Chrome_-_Base/501/Caleb_Williams/22165612"),
    ("PM-DANPRIZ347", "Daniels Prizm #347", "27382105", "https://www.comc.com/Cards/Football/2024/Panini_Prizm_-_Base/347/Rookies_-_Jayden_Daniels/27382105"),
    # ofertadas
    ("OP-007", "Wemby Chrome #221.1 (IvIase $2.00)", "31038608", "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2211/Victor_Wembanyama/31038608"),
    ("OP-008", "Flagg Topps #201 (shawnmenard $3.20)", "30579235", "https://www.comc.com/Cards/Basketball/2025-26/Topps_-_Base/201/Cooper_Flagg/30579235"),
]

INV = {c[0] for c in CARTAS[:10]}
OBJ = {c[0] for c in CARTAS[10:19]}
OFT = {c[0] for c in CARTAS[19:]}

# ── por qué la compré (DIARIO-OPERACIONES.md, resumido) ───────────────────────
MOTIVOS = {
    "TC25-251.1-B": "Compra original (pack inicial, ~23/06): la carta principal de la colección — Flagg rookie nº1, única con liquidez real sostenida (vel 1.43).",
    "TC25-271.1-B": "Compra original (pack inicial, ~23/06): rookie barato de Topps Chrome 2025-26 — compra de rotación, sin motivo detallado registrado.",
    "TC25-268.1-B": "Compra original (pack inicial, ~23/06): rookie barato — compra de rotación, sin motivo detallado registrado.",
    "TC25-264-B": "OP-004 · ERROR RECONOCIDO: compra en calentón con dead money de una cuenta eBay olvidada ($2.29) → sin liquidez, se liquidó (listada $1.09).",
    "TC25-228.1-B": "OP-005 · HOLD a noviembre: compra dead money eBay ($3.78); Castle titular de los Spurs (finalistas 2026) → la demanda vuelve en temporada NBA.",
    "TC25-253.1-B": "OP-003 · Comprada $1.50 (07/08) y listada $1.99 = 1er escalón del muro (1¢ bajo el 2º real $2.00) → +26% neto. Liquidez cayendo (⚠️ vigilar).",
    "TC25-252.1-B": "OP-001 · Oferta $6.00 aceptada (muro 1º $7.50): vel 1.71/día, P67 historial → listada $7.49. ⚠️ Muro ha bajado a $5.50: nuestra lista ya no compite.",
    "TC25-254.1-B": "OP-002 · HOLD a noviembre: mercado en mínimos (P14.8, colapso $15→$3); catalizador = temporada NBA de Knueppel → vender cuando esté caliente.",
    "DOPT24-248-B": "OP-006 · Comprada $3.50 (12/08): el 2º escalón del muro negoció (82.7% de su listado) → listada $4.49 = +22% neto. Vel 1.43, la más viva del PM.",
    "BUC24-22-B": "OP-009 · Comprada $0.85 en la rebaja de nchopp139 (12/08, terminaba al día siguiente) → listada $0.99 = 1er escalón +10.65% neto. Vel 16/semana.",
    "PM-HUGO": "Punto de mira: español, catalizador = temporada NBA (oct). ⚠️ v7d 0 — no pasa el corte de liquidez.",
    "PM-CURRY135": "Punto de mira: Curry Topps #135, vel 20/semana — liquidez alta.",
    "PM-WEMBY195": "Punto de mira: Wemby Topps #195, vel 20/semana.",
    "PM-HARPER202": "Punto de mira: Harper Topps #202, vel 8/semana.",
    "PM-FLAGGH161": "Punto de mira: Flagg Holiday #H161, vel 18/semana.",
    "PM-CURRYMP": "Punto de mira: Curry Monopoly PS8, vel 12/semana.",
    "PM-BRONNY1": "Punto de mira: Bronny+LeBron Topps Now #1, vel 19/semana.",
    "PM-WILL50": "Punto de mira: Williams Bowman Univ #50.1 (NFL), vel 12/semana.",
    "PM-DANPRIZ347": "Punto de mira: Daniels Prizm #347 (NFL), vel 7/semana (justo en el corte).",
    "OP-007": "OP-007 · Oferta $1.70→$1.85 a IvIase (listado $2.00) RECHAZADA (13/08). IvIase = 1er escalón real del muro, no baja de $2.00. Decisión pendiente de Pin.",
    "OP-008": "OP-008 · Oferta $3.20 a shawnmenard (listado $3.64) PENDIENTE. Mercado agosto ~$3.56, venta realista $3.70-3.80. Muro actual 1º $3.59 (jseau ×9).",
}


def ssh_cat(patrones):
    """cat de los snapshots del CT que matchean patrones → dict {nombre: contenido}"""
    expr = " ".join(f"{p}" for p in patrones)
    r = subprocess.run(SSH + [f"cd /root/comc-data/snapshots && for f in {expr}; do printf '\n===FILE:%s===\n' \"$f\"; cat $f 2>/dev/null; done; for f in /root/comc-data/inventario-scan-*.json; do printf '\n===FILE:%s===\n' \"$f\"; cat $f 2>/dev/null; done"],
                       capture_output=True, text=True, timeout=90)
    out = {}
    if r.returncode != 0:
        return out
    cur = None
    for line in r.stdout.splitlines():
        if line.startswith("===FILE:"):
            cur = line[len("===FILE:"):].strip().rstrip("=")
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


def get_hoja():
    r = subprocess.run([GOG, "-p", "sheets", "get", SHEET_ID, "Inventario!A1:L16"],
                       capture_output=True, text=True, timeout=90)
    out = {}
    if r.returncode != 0:
        return out
    for line in [l for l in r.stdout.splitlines() if l.strip()][1:]:
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
        out[cod] = {"coste": num(parts[3]), "be": num(parts[4]),
                    "lista": num(lista_raw.split(" ")[0]) if lista_raw else None,
                    "estado": "HOLD" if "HOLD" in lista_raw.upper() else ("LIST" if "list" in lista_raw.lower() else "NO_VENTA")}
    return out


def serie_por_id(snaps):
    """{(codigo o id): [(fecha_iso, precio_min), ...]} desde todos los snapshots."""
    serie = {}
    for nombre, contenido in snaps.items():
        try:
            d = json.loads(contenido)
        except Exception:
            continue
        fecha = d.get("fecha", "")
        if re.match(r"^\d{8}-\d{6}$", fecha):
            fecha = f"{fecha[:4]}-{fecha[4:6]}-{fecha[6:8]} {fecha[9:11]}:{fecha[11:13]}:{fecha[13:]}"
        if not fecha:
            m = re.search(r"(\d{8})-(\d{6})", nombre)
            if m:
                fecha = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]} {m.group(2)[:2]}:{m.group(2)[2:4]}:{m.group(2)[4:]}"
        # inventario-scan: niveles con codigo+min
        if "niveles" in d:
            for nivel in d["niveles"].values():
                for item in nivel:
                    if "min" in item and "codigo" in item:
                        serie.setdefault(item["codigo"], []).append((fecha, item["min"]))
            continue
        items = d.get("items", [])
        # agrupar por id → precio mínimo del feed de esa carta
        por_id = {}
        for it in items:
            cid = str(it.get("id", ""))
            if cid and it.get("precio") is not None:
                por_id.setdefault(cid, []).append(float(it["precio"]))
        for cid, ps in por_id.items():
            ps_f = [p for p in ps if p != 1.49] or ps  # filtrar subasta típica $1.49 del feed (13/08)
            serie.setdefault(cid, []).append((fecha, min(ps_f)))
    # ordenar por fecha
    for k in serie:
        serie[k] = sorted(serie[k], key=lambda x: x[0])
    return serie


def sparkline(puntos, w=150, h=34):
    """SVG sparkline de la serie [(fecha, precio)]. Devuelve svg string."""
    if len(puntos) < 2:
        return "<span class='no-data'>sin historial</span>"
    vals = [p[1] for p in puntos]
    vmin, vmax = min(vals), max(vals)
    rango = (vmax - vmin) or 1
    pad = 4
    def px(i, v):
        x = pad + i * (w - 2 * pad) / (len(vals) - 1)
        y = h - pad - (v - vmin) / rango * (h - 2 * pad)
        return x, y
    pts = " ".join(f"{px(i, v)[0]:.1f},{px(i, v)[1]:.1f}" for i, v in enumerate(vals))
    color = "#2ecc71" if vals[-1] >= vals[0] else "#e74c3c"
    titulo = " · ".join(f"{p[0][:10]} ${p[1]:.2f}" for p in puntos)
    return (f"<svg class='spark' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>"
            f"<polyline points='{pts}' fill='none' stroke='{color}' stroke-width='1.6'/>"
            f"<circle cx='{px(len(vals)-1, vals[-1])[0]:.1f}' cy='{px(len(vals)-1, vals[-1])[1]:.1f}' r='2.2' fill='{color}'/>"
            f"<title>{titulo}</title></svg>")


def fmt_fecha(fecha):
    try:
        dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return dt.astimezone(ZoneInfo("Europe/Madrid")).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return fecha


def main():
    print("Leyendo snapshots del CT…", flush=True)
    snaps = ssh_cat(["player-*.json", "feed-set-*.json", "feed-carta-*.json", "inventario-scan-*.json"])
    serie = serie_por_id(snaps)
    hoja = get_hoja()
    # último snapshot para el estado actual
    ultimo = None
    for nombre in sorted(snaps):
        if "inventario-scan-" in nombre:
            try:
                ultimo = json.loads(snaps[nombre])
            except Exception:
                pass
    estado = {}
    if ultimo:
        for nivel in ultimo["niveles"].values():
            for it in nivel:
                if "min" in it:
                    estado[it["codigo"]] = it
    fecha = fmt_fecha(ultimo.get("fecha", "?")) if ultimo else "?"
    # construir HTML
    css = """
    *{box-sizing:border-box}body{font-family:system-ui,sans-serif;margin:0;padding:16px;background:#101018;color:#e8e8f0}
    h1{font-size:20px;margin:0}h1 small{color:#8a8aa0;font-size:13px;font-weight:normal}
    .tot{background:#1a1a2e;border:1px solid #2a2a44;border-radius:14px;padding:14px;margin:10px 0 16px;text-align:center}
    .tot .big{font-size:28px;font-weight:800;color:#fff}.tot .sub{font-size:13px;color:#8a8aa0}
    .pos{color:#2ecc71}.neg{color:#e74c3c}
    h2{font-size:13px;color:#8a8aa0;text-transform:uppercase;letter-spacing:1px;margin:18px 0 8px;border-bottom:1px solid #2a2a44;padding-bottom:6px}
    .card{background:#1a1a2e;border:1px solid #2a2a44;border-radius:12px;margin:6px 0;overflow:hidden}
    .card summary{cursor:pointer;padding:10px 12px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:13px}
    .card summary:hover{background:#22223a}
    .nm{flex:1;min-width:140px}.nm small{color:#8a8aa0;font-size:10px;margin-left:5px}
    .vl{font-weight:700;color:#fff;font-variant-numeric:tabular-nums;min-width:52px;text-align:right}
    .pnl{font-weight:700;font-variant-numeric:tabular-nums;min-width:86px;text-align:right}
    .spark{margin-left:4px}
    .b{font-size:9px;padding:1px 5px;border-radius:5px;margin-left:5px;vertical-align:middle}
    .b-list{background:#2ecc7122;color:#2ecc71;border:1px solid #2ecc7155}.b-hold{background:#f39c1222;color:#f39c12;border:1px solid #f39c1255}
    .cuerpo{padding:10px 12px;border-top:1px solid #2a2a44;font-size:12px;background:#16162a;line-height:1.7}
    .mot{background:#101018;border-left:3px solid #4aa3ff;padding:7px 10px;border-radius:5px;margin:6px 0;color:#c8c8d8}
    .muro{background:#101018;border:1px solid #2a2a44;border-radius:6px;padding:7px 9px;margin:6px 0;line-height:1.6;color:#c8c8d8}
    .meta{color:#8a8aa0;font-size:11px}.no-data{color:#666;font-size:10px}
    a{color:#4aa3ff;text-decoration:none}.foot{color:#666;font-size:10px;margin-top:12px}
    """
    def tarjeta(cod, nombre, idc, url, nivel):
        d = estado.get(cod, {})
        h = hoja.get(cod, {})
        if "min" not in d:
            return f"<details class='card err'><summary><span class='nm'>{nombre}</span><span style='color:#e74c3c'>sin datos</span></summary></details>"
        coste = h.get("coste")
        estado_l = h.get("estado", "")
        ref = d["min"]
        if h.get("lista") is not None and estado_l == "LIST":
            ref = min(h["lista"], d["min"])
        pnl_txt = "—"
        if coste:
            neto = ref * 0.95 - coste
            pct = neto / coste * 100
            cls = "pos" if neto >= 0 else "neg"
            pnl_txt = f"<span class='pnl {cls}'>{'+' if neto >= 0 else ''}{neto:.2f}$ ({'+' if pct >= 0 else ''}{pct:.1f}%)</span>"
        badge = {"LIST": "<span class='b b-list'>LIST</span>", "HOLD": "<span class='b b-hold'>HOLD</span>"}.get(estado_l, "")
        serie_c = sorted((serie.get(cod) or []) + (serie.get(idc) or []), key=lambda x: x[0])
        spark = sparkline(serie_c)
        be_txt = f"${h['be']:.2f}" if h.get("be") else "—"
        cos_txt = f"${coste:.2f}" if coste else "—"
        lista_txt = f"${h['lista']:.2f}" if h.get("lista") else "—"
        muro_html = d.get("muro_txt", "").replace("; ", "<br>")
        motivo = MOTIVOS.get(cod, "—")
        hist_txt = ""
        if serie_c:
            primero, ult = serie_c[0], serie_c[-1]
            hist_txt = (f"Evolución del muro: {primero[0][:10]} ${primero[1]:.2f} → "
                        f"{ult[0][:10]} ${ult[1]:.2f} ({len(serie_c)} datos)")
        summary = (f"<summary><span class='nm'>{nombre}<small>{cod}</small>{badge}</span>"
                   f"<span class='vl'>${ref:.2f}</span>{pnl_txt}{spark}</summary>")
        cuerpo = (f"<div class='cuerpo'>"
                  f"<div class='mot'><b>Por qué:</b> {motivo}</div>"
                  f"<div class='meta'>Coste {cos_txt} · Break-even {be_txt} · Nuestra lista {lista_txt} · "
                  f"1º ${d['min']:.2f} · 2º ${d.get('seg', 0):.2f} · copias {d['copias_totales']} · v7d {d['v7d']}</div>"
                  f"{f'<div class=\"muro\"><b>Muro:</b><br>{muro_html}</div>' if muro_html else ''}"
                  f"<div class='meta'>{hist_txt}</div>"
                  f"<div><a href='{url}' target='_blank'>Ver en COMC ↗</a></div></div>")
        return f"<details class='card'>{summary}{cuerpo}</details>"

    # totales cartera
    tot_c = tot_v = 0.0
    for cod, nombre, idc, url in CARTAS[:10]:
        d = estado.get(cod, {})
        if "min" not in d:
            continue
        h = hoja.get(cod, {})
        coste = h.get("coste")
        if not coste:
            continue
        ref = d["min"]
        if h.get("lista") is not None and h.get("estado") == "LIST":
            ref = min(h["lista"], d["min"])
        tot_c += coste
        tot_v += ref * 0.95
    pnl = tot_v - tot_c
    pnl_pct = pnl / tot_c * 100 if tot_c else 0
    cls = "pos" if pnl >= 0 else "neg"
    sign = "+" if pnl >= 0 else ""
    html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cartera COMC — {fecha}</title><style>{css}</style></head><body>
<h1>🛸 Cartera COMC <small>· datos del {fecha}</small></h1>
<div class='tot'><div class='big'>${tot_v:.2f}</div>
<div class='sub'>Coste ${tot_c:.2f} · <span class='{cls}'>{sign}${pnl:.2f} ({sign}{pnl_pct:.1f}%)</span> · {len(INV)} activos</div></div>
<h2>📦 Inventario ({len(INV)})</h2>
{''.join(tarjeta(*c, "N1") for c in CARTAS[:10])}
<h2>🎯 Objetivos ({len(OBJ)})</h2>
{''.join(tarjeta(*c, "N2") for c in CARTAS[10:19])}
<h2>📨 Ofertadas ({len(OFT)})</h2>
{''.join(tarjeta(*c, "N3") for c in CARTAS[19:])}
<div class='foot'>Mini-gráfica = evolución del 1er escalón (snapshots diarios; hasta el 12/08 fuente = feed COMC, puede incluir subastas; desde el 13/08 = muro real verificado) · P&amp;L neto = ref×0.95 − coste · web local del CT kobe</div>
</body></html>"""
    with open(OUT_LOCAL, "w") as fh:
        fh.write(html)
    # subir al CT
    r = subprocess.run(SSH + [f"mkdir -p {WEB_DIR_CT}"], capture_output=True, text=True, timeout=60)
    r = subprocess.run(["scp", "-J", "root@100.89.234.7", OUT_LOCAL, f"root@192.168.0.102:{WEB_DIR_CT}/index.html"],
                       capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        print("ERROR scp:", r.stderr[-300:])
        return
    print(f"✅ Web generada y subida: {WEB_DIR_CT}/index.html | {len(INV)}+{len(OBJ)}+{len(OFT)} cartas | P&L {sign}${pnl:.2f}")

if __name__ == "__main__":
    main()
