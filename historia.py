import sys
sys.path.insert(0, "/root/comc-scripts")
import parte as P

cod = sys.argv[1] if len(sys.argv) > 1 else ""
url = ""
for r in [l.strip().split(";") for l in
          open(P.DATA + "/inventario.txt", encoding="utf-8")]:
    if len(r) >= 3 and r[0].strip().upper() == cod.upper():
        url = r[2].strip()
if not url:
    for c in P.lee_pm():
        if c["cod"].upper() == cod.upper():
            url = c["url"]
if not url:
    print("no encuentro el codigo", cod)
    sys.exit(1)

serie = P.historico().get(P.cid(url), [])
print()
print("HISTORIA DE MURO -", cod, "-", len(serie), "mediciones")
print("-" * 50)
for f, m in serie:
    print(" ", f, "  $" + format(m, ".2f"))
print("-" * 50)
if serie:
    vals = [x[1] for x in serie]
    print("  max $" + format(max(vals), ".2f") +
          "   min $" + format(min(vals), ".2f") +
          "   ultimo $" + format(vals[-1], ".2f"))
