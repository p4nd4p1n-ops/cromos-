#!/usr/bin/env python3
"""Siembra punto-mira.json desde el estado reconstruido del markdown."""
import json, glob, os

DATA = "/root/comc-data"
SALIDA = DATA + "/punto-mira.json"

SEMILLA = [
    {"codigo": "TC25-WEMBY-B", "nombre": "Wemby Chrome", "nivel": "VIGILAR",
     "precio_gatillo": None, "nota": "entro 11/08 por liquidez",
     "claves": ["Topps Chrome", "Wembanyama"]},
    {"codigo": "T25-201-B", "nombre": "Flagg Topps #201", "nivel": "VIGILAR",
     "precio_gatillo": None, "nota": "entro 11/08",
     "claves": ["Topps - [Base] #201", "Flagg"]},
    {"codigo": "TLS25-11-B", "nombre": "Flagg Living #11", "nivel": "VIGILAR",
     "precio_gatillo": None, "nota": "entro 11/08",
     "claves": ["Living Set", "#11", "Flagg"]},
    {"codigo": "DO24-248-B", "nombre": "Daniels Optic #248 (NFL)", "nivel": "VIGILAR",
     "precio_gatillo": 3.53, "nota": "gap 7.9%; oferta 3.50 rechazada (min vendedor 3.92); catalizador sep-2026 es hipotesis (L-017)",
     "claves": ["Optic", "248", "Daniels"]},
    {"codigo": "BUC24-22-B", "nombre": "Harper Bowman Univ #22", "nivel": "OBSERVAR",
     "precio_gatillo": 0.90, "nota": "VENDIDA 13/08 a 0.98 (+9.4% neto). Recompra 0.85-0.90; mercado subiendo",
     "claves": ["Bowman University Chrome", "#22", "Harper"]},
    {"codigo": "TC25-253.1-B", "nombre": "Edgecombe Chrome #253.1", "nivel": "OBSERVAR",
     "precio_gatillo": None, "nota": "VENDIDA 14/08 a 1.99 (+26.0% neto). Reentrar solo con gap >=5% y v7d >=7",
     "claves": ["Topps Chrome", "253", "Edgecombe"]},
]

def indice_urls():
    """titulo -> url, a partir de todo lo escaneado hasta hoy."""
    idx = {}
    for f in glob.glob(DATA + "/snapshots/player-*.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for c in d.get("items", []):
            if c.get("titulo") and c.get("url"):
                idx[c["titulo"]] = c["url"]
    for f in glob.glob(DATA + "/snapshots/fino-*.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for r in d:
            if r.get("titulo") and r.get("url"):
                idx[r["titulo"]] = r["url"]
    return idx

def resolver(claves, idx):
    hits = [(t, u) for t, u in idx.items()
            if all(k.lower() in t.lower() for k in claves)]
    if not hits:
        return None, None
    hits.sort(key=lambda x: len(x[0]))
    return hits[0]

idx = indice_urls()
print("titulos indexados:", len(idx))
print()

cartas = []
for s in SEMILLA:
    titulo, url = resolver(s["claves"], idx)
    estado = "OK " if url else "SIN URL"
    print(estado, "|", s["nombre"], "->", (titulo or "no encontrado")[:65])
    cartas.append({
        "codigo": s["codigo"], "nombre": s["nombre"], "url": url,
        "titulo_comc": titulo, "nivel": s["nivel"],
cd /root/.openclaw/workspace/comc && cat > seed_punto_mira.py << 'PYEOF'
#!/usr/bin/env python3
"""Siembra punto-mira.json desde el estado reconstruido del markdown."""
import json, glob, os

DATA = "/root/comc-data"
SALIDA = DATA + "/punto-mira.json"

SEMILLA = [
    {"codigo": "TC25-WEMBY-B", "nombre": "Wemby Chrome", "nivel": "VIGILAR",
     "precio_gatillo": None, "nota": "entro 11/08 por liquidez",
     "claves": ["Topps Chrome", "Wembanyama"]},
    {"codigo": "T25-201-B", "nombre": "Flagg Topps #201", "nivel": "VIGILAR",
     "precio_gatillo": None, "nota": "entro 11/08",
     "claves": ["Topps - [Base] #201", "Flagg"]},
    {"codigo": "TLS25-11-B", "nombre": "Flagg Living #11", "nivel": "VIGILAR",
     "precio_gatillo": None, "nota": "entro 11/08",
     "claves": ["Living Set", "#11", "Flagg"]},
    {"codigo": "DO24-248-B", "nombre": "Daniels Optic #248 (NFL)", "nivel": "VIGILAR",
     "precio_gatillo": 3.53, "nota": "gap 7.9%; oferta 3.50 rechazada (min vendedor 3.92); catalizador sep-2026 es hipotesis (L-017)",
     "claves": ["Optic", "248", "Daniels"]},
    {"codigo": "BUC24-22-B", "nombre": "Harper Bowman Univ #22", "nivel": "OBSERVAR",
     "precio_gatillo": 0.90, "nota": "VENDIDA 13/08 a 0.98 (+9.4% neto). Recompra 0.85-0.90; mercado subiendo",
     "claves": ["Bowman University Chrome", "#22", "Harper"]},
    {"codigo": "TC25-253.1-B", "nombre": "Edgecombe Chrome #253.1", "nivel": "OBSERVAR",
     "precio_gatillo": None, "nota": "VENDIDA 14/08 a 1.99 (+26.0% neto). Reentrar solo con gap >=5% y v7d >=7",
     "claves": ["Topps Chrome", "253", "Edgecombe"]},
]

def indice_urls():
    """titulo -> url, a partir de todo lo escaneado hasta hoy."""
    idx = {}
    for f in glob.glob(DATA + "/snapshots/player-*.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for c in d.get("items", []):
            if c.get("titulo") and c.get("url"):
                idx[c["titulo"]] = c["url"]
    for f in glob.glob(DATA + "/snapshots/fino-*.json"):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for r in d:
            if r.get("titulo") and r.get("url"):
                idx[r["titulo"]] = r["url"]
    return idx

def resolver(claves, idx):
    hits = [(t, u) for t, u in idx.items()
            if all(k.lower() in t.lower() for k in claves)]
    if not hits:
        return None, None
    hits.sort(key=lambda x: len(x[0]))
    return hits[0]

idx = indice_urls()
print("titulos indexados:", len(idx))
print()

cartas = []
for s in SEMILLA:
    titulo, url = resolver(s["claves"], idx)
    estado = "OK " if url else "SIN URL"
    print(estado, "|", s["nombre"], "->", (titulo or "no encontrado")[:65])
    cartas.append({
        "codigo": s["codigo"], "nombre": s["nombre"], "url": url,
        "titulo_comc": titulo, "nivel": s["nivel"],
        "precio_gatillo": s["precio_gatillo"], "nota": s["nota"],
        "desde": "2026-08-18",
    })

doc = {"actualizado": "2026-08-18", "objetivo_min": 18, "objetivo_max": 20,
       "cartas": cartas}
os.makedirs(DATA, exist_ok=True)
json.dump(doc, open(SALIDA, "w"), ensure_ascii=False, indent=1)
print()
print("escrito:", SALIDA, "-", len(cartas), "cartas")
