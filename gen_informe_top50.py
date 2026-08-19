#!/usr/bin/env python3
"""gen_informe_top50.py — genera informe markdown del escaneo top-50 Chrome Base 2025-26."""
import json, datetime

d = json.load(open("/root/comc-data/scan-top50-2026-08-07.json"))

def v(r, k):
    x = r.get(k)
    return x if isinstance(x, (int, float)) else 0.0

con = sorted([r for r in d if v(r, "ventas_7d") > 0], key=lambda x: v(x, "ventas_7d"), reverse=True)
sin = [r for r in d if v(r, "ventas_7d") == 0]

L = []
A = L.append
A("# Informe Top-50 NBA · Topps Chrome Base 2025-26\n")
A(f"**Escaneo completado:** 2026-08-07 21:43 UTC · **45 cartas** (de 50 jugadores; 5 sin carta en el set: Luka, Zion, KAT, Ingram, Avdija) · 3 precargadas del escaneo previo (Flagg, Knueppel, Castle)\n")
A("\n---\n")
A("\n## Resumen ejecutivo\n")
A(f"- **{len(con)} de 45** cartas con ventas en los últimos 7 días (suma total: **{sum(v(r,'ventas_7d') for r in d):.0f} ventas**).")
A(f"- **{len(sin)} cartas sin ventas** en 7 días → el set base de veteranos está parado; solo rookies y superestrellas mueven.")
A("- **El jugador más líquido: Wembanyama** (18 ventas/7d) pero con gap 0% — sin margen.")
A("- **Oportunidades reales (gap > 5% + liquidez):** Flagg (gap 6,4%), KD (5,4%), Curry (6,7%), Jokic (6,3%), SGA (16% con solo 2 copias).")
A("- ⚠️ Gaps grandes con **0 ventas** (Booker 26,7%, Bam 36,7%, Barnes 20%...) son trampa: sin demanda no hay oportunidad.")
A("\n---\n")
A("\n## Cartas con ventas (7 días)\n")
A("\n| Jugador | Min $ | 2º $ | Gap % | Copias | Ventas 7d | Vel/día | Días inventario | Turnover % |")
A("|---|---|---|---|---|---|---|---|---|")
for r in con:
    A(f"| {r['nombre']} | {v(r,'min'):.2f} | {v(r,'seg'):.2f} | {v(r,'gap'):.1f} | {v(r,'copias'):.0f} | {v(r,'ventas_7d'):.0f} | {v(r,'vel_dia'):.2f} | {r.get('dias_inv') or '—'} | {v(r,'turnover'):.1f} |")

A("\n## Detalle de ventas recientes (top líquidos)\n")
for r in con:
    A(f"\n### {r['nombre']} — min ${v(r,'min'):.2f} · gap {v(r,'gap'):.1f}% · {v(r,'copias'):.0f} copias · {v(r,'ventas_7d'):.0f} ventas/7d")
    A(f"\n[COMC](https://www.comc.com{r['path']}) · num={r.get('num')}")
    A("\n| Fecha | Precio $ |")
    A("|---|---|")
    for f_, p in (r.get("sales") or [])[:12]:
        A(f"| {f_} | {p} |")

A("\n---\n")
A("\n## Resto de cartas (sin ventas 7d)\n")
A("\n| Jugador | Min $ | Gap % | Copias |")
A("|---|---|---|---|")
for r in sorted(sin, key=lambda x: v(x, "gap"), reverse=True):
    A(f"| {r['nombre']} | {v(r,'min'):.2f} | {v(r,'gap'):.1f} | {v(r,'copias'):.0f} |")

A("\n---\n")
A(f"\n_Generado automáticamente por Kobe 🛸 · {datetime.datetime.utcnow().isoformat()} UTC · datos: /root/comc-data/scan-top50-2026-08-07.json_\n")

out = "/root/comc-data/informe-top50-2026-08-07.md"
open(out, "w").write("\n".join(L))
print("escrito:", out, len(L), "lineas")
