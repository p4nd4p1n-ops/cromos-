import json
D = "/root/comc-data"
d = json.load(open(D + "/inventario-scan.json"))
rows = []
for c in (d.get("niveles") or {}).get("N1", []):
    rows.append([c.get("codigo") or "", c.get("nombre") or "",
                 c.get("url") or ""])
with open(D + "/inventario.txt", "w", encoding="utf-8") as f:
    f.write("# codigo ; nombre ; url\n")
    for r in rows:
        f.write(" ; ".join(r) + "\n")
print("escritas", len(rows), "cartas en inventario.txt")
