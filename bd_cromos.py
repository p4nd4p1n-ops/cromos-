#!/usr/bin/env python3
"""BD de cromos COMC — fichas completas por carta (SQLite).
Crea comc/cromos.db con tablas: cromos, historiales, muros, decisiones.
Uso: python3 bd_cromos.py [crear|ficha <codigo>|todas|decisiones <codigo>]
"""
import sqlite3, sys, os, json

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cromos.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS cromos (
  codigo TEXT PRIMARY KEY,
  nombre TEXT,
  set TEXT,
  url TEXT,
  coste_compra REAL,
  coste_anadir REAL DEFAULT 0,
  coste_total REAL,
  fecha_compra TEXT,
  dias_cartera INTEGER,
  dead_money INTEGER DEFAULT 0,
  estado TEXT,               -- hold / venta / parada
  precio_listado REAL,
  fecha_listado TEXT,
  break_even REAL,
  fecha_dato TEXT
);
CREATE TABLE IF NOT EXISTS historiales (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo TEXT,
  ventas_limpias INTEGER,
  media_ultimas10 REAL,
  media_ultimas20 REAL,
  p50 REAL, p60 REAL, p65 REAL, p70 REAL, p75 REAL,
  percentil REAL,
  vel_dia REAL,
  ventas_7d INTEGER,
  rango TEXT,
  outliers TEXT,
  fecha_dato TEXT
);
CREATE TABLE IF NOT EXISTS muros (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo TEXT,
  fecha TEXT,
  escalon1 REAL, escalon2 REAL,
  copias INTEGER,
  hay_remotos INTEGER DEFAULT 0,
  ojo REAL,
  detalle TEXT
);
CREATE TABLE IF NOT EXISTS decisiones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo TEXT,
  fecha TEXT,
  tipo TEXT,        -- comprar/listar/subir/bajar/hold
  precio REAL,
  razon TEXT,
  hipotesis TEXT,
  resultado TEXT,
  leccion TEXT
);
"""

# ------------------------- DATOS (11/08/2026) -------------------------

CROMOS = [
    # Harper
    dict(codigo="TC25-252.1-B", nombre="Dylan Harper", set="2025-26 Topps Chrome [Base]",
         url="https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639",
         coste_compra=6.00, coste_anadir=0, fecha_compra="2026-08-07", dias_cartera=1,
         dead_money=0, estado="venta", precio_listado=7.49, fecha_listado="2026-08-11",
         break_even=6.95, fecha_dato="2026-08-11"),
    # Flagg
    dict(codigo="TC25-251.1-B", nombre="Cooper Flagg", set="2025-26 Topps Chrome [Base]",
         url="https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2511/Cooper_Flagg/31038638",
         coste_compra=22.60, coste_anadir=0, fecha_compra="2026-06-20", dias_cartera=51,
         dead_money=0, estado="hold", precio_listado=None, fecha_listado=None,
         break_even=26.17, fecha_dato="2026-08-11"),
    # Knueppel
    dict(codigo="TC25-254.1-B", nombre="Kon Knueppel", set="2025-26 Topps Chrome [Base]",
         url="https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2541/Kon_Knueppel/31038641",
         coste_compra=3.00, coste_anadir=0, fecha_compra="2026-06-20", dias_cartera=3,
         dead_money=0, estado="hold", precio_listado=None, fecha_listado=None,
         break_even=3.47, fecha_dato="2026-08-11"),
    # Edgecombe
    dict(codigo="TC25-253.1-B", nombre="VJ Edgecombe", set="2025-26 Topps Chrome [Base]",
         url="https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2531/VJ_Edgecombe/31038640",
         coste_compra=1.50, coste_anadir=0, fecha_compra="2026-08-07", dias_cartera=3,
         dead_money=0, estado="venta", precio_listado=1.99, fecha_listado="2026-08-11",
         break_even=1.74, fecha_dato="2026-08-11"),
    # Bryant
    dict(codigo="TC25-264-B", nombre="Carter Bryant", set="2025-26 Topps Chrome [Base]",
         url="https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/264/Carter_Bryant/31038652",
         coste_compra=2.29, coste_anadir=2.00, fecha_compra="2026-06-24", dias_cartera=44,
         dead_money=1, estado="venta", precio_listado=1.09, fecha_listado="2026-08-11",
         break_even=2.65, fecha_dato="2026-08-11"),
    # Castle
    dict(codigo="TC25-228.1-B", nombre="Stephon Castle", set="2025-26 Topps Chrome [Base]",
         url="https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2281/Stephon_Castle/31038614",
         coste_compra=1.78, coste_anadir=2.00, fecha_compra="2026-06-24", dias_cartera=44,
         dead_money=1, estado="hold", precio_listado=None, fecha_listado=None,
         break_even=4.38, fecha_dato="2026-08-11"),
    # Riley
    dict(codigo="TC25-271.1-B", nombre="Will Riley", set="2025-26 Topps Chrome [Base]",
         url="https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2711/Will_Riley/31038659",
         coste_compra=0.57, coste_anadir=0, fecha_compra="2026-06-20", dias_cartera=51,
         dead_money=0, estado="parada", precio_listado=None, fecha_listado=None,
         break_even=0.66, fecha_dato="2026-08-11"),
    # Clayton
    dict(codigo="TC25-268.1-B", nombre="Walter Clayton Jr.", set="2025-26 Topps Chrome [Base]",
         url="https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2681/Walter_Clayton_Jr/31038656",
         coste_compra=0.59, coste_anadir=0, fecha_compra="2026-06-20", dias_cartera=51,
         dead_money=0, estado="parada", precio_listado=None, fecha_listado=None,
         break_even=0.68, fecha_dato="2026-08-11"),
]

HISTORIALES = [
    dict(codigo="TC25-252.1-B", ventas_limpias=69, media_ultimas10=7.49, media_ultimas20=None,
         p50=None, p60=None, p65=7.29, p70=None, p75=None, percentil=67.1, vel_dia=1.71, ventas_7d=12,
         rango="ago 2026", outliers=None, fecha_dato="2026-08-11"),
    dict(codigo="TC25-251.1-B", ventas_limpias=403, media_ultimas10=19.49, media_ultimas20=None,
         p50=None, p60=None, p65=None, p70=None, p75=None, percentil=85.2, vel_dia=2.43, ventas_7d=17,
         rango="ago 2026", outliers=None, fecha_dato="2026-08-11"),
    dict(codigo="TC25-254.1-B", ventas_limpias=331, media_ultimas10=3.30, media_ultimas20=None,
         p50=None, p60=None, p65=None, p70=None, p75=None, percentil=14.8, vel_dia=1.71, ventas_7d=12,
         rango="ago 2026", outliers="20.34 y 93.71 fuera", fecha_dato="2026-08-11"),
    dict(codigo="TC25-253.1-B", ventas_limpias=246, media_ultimas10=None, media_ultimas20=1.94,
         p50=1.95, p60=2.12, p65=2.17, p70=2.17, p75=2.20, percentil=44.7, vel_dia=0.86, ventas_7d=6,
         rango="24 jul - 8 ago", outliers=None, fecha_dato="2026-08-11"),
    dict(codigo="TC25-264-B", ventas_limpias=30, media_ultimas10=None, media_ultimas20=0.85,
         p50=0.88, p60=0.90, p65=0.95, p70=0.99, p75=1.00, percentil=None, vel_dia=0.14, ventas_7d=1,
         rango="6 mar - 6 ago", outliers=None, fecha_dato="2026-08-11"),
    dict(codigo="TC25-228.1-B", ventas_limpias=21, media_ultimas10=None, media_ultimas20=0.86,
         p50=0.88, p60=0.89, p65=0.90, p70=0.92, p75=0.98, percentil=None, vel_dia=0.0, ventas_7d=0,
         rango="22 feb - 28 jul", outliers="2.00, 2.04x2, 3.04 fuera (picos evento)", fecha_dato="2026-08-11"),
    dict(codigo="TC25-271.1-B", ventas_limpias=None, media_ultimas10=None, media_ultimas20=None,
         p50=None, p60=None, p65=None, p70=None, p75=None, percentil=None, vel_dia=0.0, ventas_7d=0,
         rango=None, outliers=None, fecha_dato="2026-08-11"),
    dict(codigo="TC25-268.1-B", ventas_limpias=None, media_ultimas10=None, media_ultimas20=None,
         p50=None, p60=None, p65=None, p70=None, p75=None, percentil=None, vel_dia=0.0, ventas_7d=0,
         rango=None, outliers=None, fecha_dato="2026-08-11"),
]

MUROS = [
    dict(codigo="TC25-252.1-B", fecha="2026-08-11 13:21", escalon1=7.00, escalon2=7.25, copias=54,
         hay_remotos=0, ojo=7.00, detalle="G23sports 1x7.00+2x7.25, FrescoCards 7.50, 8.50x2, 13.49(nosotros), 13.50x2, 15.49, 17, 18x37, 20.50"),
    dict(codigo="TC25-251.1-B", fecha="2026-08-11 11:26", escalon1=24.49, escalon2=24.89, copias=29,
         hay_remotos=0, ojo=24.49, detalle="scan inventario"),
    dict(codigo="TC25-253.1-B", fecha="2026-08-11 11:26", escalon1=1.94, escalon2=2.00, copias=64,
         hay_remotos=0, ojo=1.94, detalle="nuestra copia a 1.99 (1er escalón tras subir)"),
    dict(codigo="TC25-264-B", fecha="2026-08-11 11:26", escalon1=1.02, escalon2=1.10, copias=30,
         hay_remotos=0, ojo=1.10, detalle="1.02 = rebaja azp (no cuenta), real 1.10"),
    dict(codigo="TC25-228.1-B", fecha="2026-08-11 11:26", escalon1=0.89, escalon2=0.95, copias=32,
         hay_remotos=0, ojo=0.89, detalle="scan inventario"),
    dict(codigo="TC25-271.1-B", fecha="2026-08-11 11:26", escalon1=0.87, escalon2=0.87, copias=28,
         hay_remotos=0, ojo=0.87, detalle="scan inventario"),
    dict(codigo="TC25-268.1-B", fecha="2026-08-11 11:26", escalon1=0.60, escalon2=0.64, copias=62,
         hay_remotos=0, ojo=0.60, detalle="scan inventario"),
]

DECISIONES = [
    dict(codigo="TC25-252.1-B", fecha="2026-08-10", tipo="listar", precio=13.49,
         razon="1¢ bajo el que se creía 2º escalón real (13.50); $8.50 asumidos REMOTOS (no contaban). Marco 3 precios de Pin: más barato 7.49 / 1¢ bajo 2º real 13.49 / listar alto. Evidencia: 2 ventas >9$ el 7/08.",
         hipotesis="o vende rápido a precio alto, o en 7 días bajamos a 7.49",
         resultado="NO vendió en 2 días. Muro real distinto (8.50 no eran remotos)",
         leccion="verificar el muro EN VIVO antes de listar alto — no asumir remotos sin confirmar (L-018)"),
    dict(codigo="TC25-252.1-B", fecha="2026-08-11", tipo="bajar", precio=7.49,
         razon="muro NO era como se pensaba (8.50 no remotos → competencia real). Mercado real agosto: ventas 5-7.75, media 6.72. El 13.49 era el doble de la media.",
         hipotesis="a 7.49 está en la zona donde el mercado compra esta semana",
         resultado="PENDIENTE (cambio de precio en COMC por Pin)",
         leccion=None),
    dict(codigo="TC25-251.1-B", fecha="2026-08-10", tipo="hold", precio=None,
         razon="comprada para futuro GRADEADO (PSA 10 = 265-300$, +1100%). Tesis de gradeo. Primer candidato a liberar si aprieta la liquidez.",
         hipotesis="sube más con gradeo que vendiendo ahora",
         resultado="PENDIENTE", leccion=None),
    dict(codigo="TC25-254.1-B", fecha="2026-08-10", tipo="hold", precio=None,
         razon="mercado en MÍNIMOS (percentil 14.8, colapso 15→3). Catalizador: noviembre vuelve a jugar (temporada NBA) → recuperará al ~50.",
         hipotesis="sube del percentil 14.8 al ~50 en noviembre",
         resultado="PENDIENTE (noviembre)", leccion="el sistema incluye TESIS DE CATALIZADOR, no solo matemática (M-006)"),
    dict(codigo="TC25-253.1-B", fecha="2026-08-11", tipo="subir", precio=1.99,
         razon="ya era 1er escalón (1.94); subir 5¢ → sigue siendo el más barato (1¢ bajo 2º real 2.00). Percentil 41.5→44.7. Neto 22.9%→26.0%. Liquidez cayendo + 64 copias → no ser avaricioso.",
         hipotesis="vende igual de rápido con +26% neto",
         resultado="PENDIENTE", leccion="subir SIN perder posición = ganancia casi gratis (M-001)"),
    dict(codigo="TC25-264-B", fecha="2026-08-11", tipo="listar", precio=1.09,
         razon="liquidez MALA (1 venta/7d) pese a SRP 2.50. Regla del céntimo sobre 1er escalón REAL (1.10; el 1.02 era rebaja temporal de azp). DEAD MONEY de eBay → impacto bankroll 0. Error reconocido: comprar sin liquidez (L-015).",
         hipotesis="rota como primer escalón real",
         resultado="PENDIENTE", leccion="liquidez primero en TODA compra, incluso gratis (L-015)"),
    dict(codigo="TC25-228.1-B", fecha="2026-08-11", tipo="hold", precio=None,
         razon="'1 pavo le podemos sacar' — Castle titular de los Spurs (finalistas 2026), demanda vuelve en temporada. Picos julio = hype mini-camp París + playoffs, NO Summer League (no juega). DEAD MONEY, hold sin coste real.",
         hipotesis="en noviembre se puede sacar ~1$ (P70+)",
         resultado="PENDIENTE (noviembre)", leccion="no forzar correlaciones sin verificar (L-017)"),
]

# ------------------------- CREAR / CONSULTAR -------------------------

def crear():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    for c in CROMOS:
        c["coste_total"] = round(c["coste_compra"] + c["coste_anadir"], 2)
        con.execute("""INSERT INTO cromos (codigo,nombre,set,url,coste_compra,coste_anadir,coste_total,
                       fecha_compra,dias_cartera,dead_money,estado,precio_listado,fecha_listado,break_even,fecha_dato)
                       VALUES (:codigo,:nombre,:set,:url,:coste_compra,:coste_anadir,:coste_total,
                       :fecha_compra,:dias_cartera,:dead_money,:estado,:precio_listado,:fecha_listado,:break_even,:fecha_dato)""", c)
    for h in HISTORIALES:
        con.execute("""INSERT INTO historiales (codigo,ventas_limpias,media_ultimas10,media_ultimas20,
                       p50,p60,p65,p70,p75,percentil,vel_dia,ventas_7d,rango,outliers,fecha_dato)
                       VALUES (:codigo,:ventas_limpias,:media_ultimas10,:media_ultimas20,
                       :p50,:p60,:p65,:p70,:p75,:percentil,:vel_dia,:ventas_7d,:rango,:outliers,:fecha_dato)""", h)
    for m in MUROS:
        con.execute("""INSERT INTO muros (codigo,fecha,escalon1,escalon2,copias,hay_remotos,ojo,detalle)
                       VALUES (:codigo,:fecha,:escalon1,:escalon2,:copias,:hay_remotos,:ojo,:detalle)""", m)
    for d in DECISIONES:
        con.execute("""INSERT INTO decisiones (codigo,fecha,tipo,precio,razon,hipotesis,resultado,leccion)
                       VALUES (:codigo,:fecha,:tipo,:precio,:razon,:hipotesis,:resultado,:leccion)""", d)
    con.commit()
    print(f"BD creada: {DB}")
    for t in ["cromos", "historiales", "muros", "decisiones"]:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n} registros")
    con.close()

def ficha(codigo):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    c = con.execute("SELECT * FROM cromos WHERE codigo=?", (codigo,)).fetchone()
    if not c:
        print(f"No existe {codigo}"); return
    print("=" * 60)
    print(f"FICHA: {c['nombre']} ({c['codigo']})")
    print(f"  Set: {c['set']}")
    print(f"  Coste: {c['coste_compra']}$ + añadir {c['coste_anadir']}$ = {c['coste_total']}$"
          + (" (DEAD MONEY)" if c['dead_money'] else ""))
    print(f"  Compra: {c['fecha_compra']} · {c['dias_cartera']} días")
    print(f"  Estado: {c['estado']} · listado: {c['precio_listado']}$ ({c['fecha_listado']})")
    print(f"  Break even: {c['break_even']}$")
    h = con.execute("SELECT * FROM historiales WHERE codigo=? ORDER BY fecha_dato DESC LIMIT 1", (codigo,)).fetchone()
    if h and h['ventas_limpias']:
        print(f"  Historial: {h['ventas_limpias']} ventas limpias · vel {h['vel_dia']}/día · {h['ventas_7d']}v/7d"
              + (f" · P{h['percentil']}" if h['percentil'] is not None else ""))
        print(f"    media10: {h['media_ultimas10']} · media20: {h['media_ultimas20']}"
              + (f" · P50-75: {h['p50']}/{h['p60']}/{h['p65']}/{h['p70']}/{h['p75']}" if h['p50'] is not None else "")
              + (f" · outliers: {h['outliers']}" if h['outliers'] else ""))
    m = con.execute("SELECT * FROM muros WHERE codigo=? ORDER BY fecha DESC LIMIT 1", (codigo,)).fetchone()
    if m:
        print(f"  Muro ({m['fecha']}): {m['escalon1']} / {m['escalon2']} · {m['copias']} copias"
              + (" · REMOTOS" if m['hay_remotos'] else "")
              + (f" · ojo {m['ojo']}" if m['ojo'] else ""))
        if m['detalle']: print(f"    {m['detalle']}")
    print("  Decisiones:")
    for d in con.execute("SELECT * FROM decisiones WHERE codigo=? ORDER BY fecha", (codigo,)):
        print(f"    [{d['fecha']}] {d['tipo'].upper()} {d['precio'] if d['precio'] else ''}")
        print(f"      por qué: {d['razon']}")
        if d['hipotesis']: print(f"      hipótesis: {d['hipotesis']}")
        if d['resultado']: print(f"      resultado: {d['resultado']}")
        if d['leccion']: print(f"      lección: {d['leccion']}")
    print("=" * 60)
    con.close()

def todas():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    for c in con.execute("SELECT * FROM cromos ORDER BY estado, nombre"):
        print(f"{c['codigo']} | {c['nombre']:<18} | {c['estado']:<6} | list {c['precio_listado']} | coste {c['coste_total']}"
              + (" 💀" if c['dead_money'] else ""))
    con.close()

def decisiones(codigo=None):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    q = "SELECT * FROM decisiones"
    args = ()
    if codigo:
        q += " WHERE codigo=?"
        args = (codigo,)
    for d in con.execute(q + " ORDER BY fecha", args):
        print(f"[{d['fecha']}] {d['codigo']} {d['tipo'].upper()} {d['precio'] if d['precio'] else ''}")
        print(f"    por qué: {d['razon'][:120]}")
    con.close()

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "crear"
    if cmd == "crear":
        crear()
    elif cmd == "ficha" and len(sys.argv) > 2:
        ficha(sys.argv[2])
    elif cmd == "todas":
        todas()
    elif cmd == "decisiones":
        decisiones(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        print("Uso: bd_cromos.py [crear|ficha <codigo>|todas|decisiones [codigo]]")
