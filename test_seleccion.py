import sys
sys.path.insert(0, "/root/comc-scripts")
import fino_scan as F

cand = F.cargar_candidatas()
print("candidatas totales (sin Non-Sports):", len(cand))
sel = F.seleccionar(cand, 25)
print("seleccionadas:", len(sel))
print()
for i, c in enumerate(sel, 1):
    print(str(i).rjust(2), "|", str(c.get("qty")).rjust(4), "cop |", (c.get("titulo") or "?")[:70])
