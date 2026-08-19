#!/usr/bin/env python3
"""mlb_roy_poll.py — trae el Rookie of the Year poll de MLB.com vía FlareSolverr,
guarda el HTML y extrae la lista de jugadores con puntos/votos."""
import json, urllib.request, re, sys, datetime

FS = "http://127.0.0.1:8191/v1"
URL = "https://www.mlb.com/news/mlb-rookie-of-the-year-poll-august-2026"

def fs(payload, timeout=90000):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(FS, data=body, headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=timeout + 30).read())

def main():
    d = fs({"cmd": "request.get", "url": URL, "maxTimeout": 60000})
    hh = d.get("solution", {}).get("response", "")
    print("HTML len:", len(hh))
    if len(hh) < 5000:
        print("BLOQUEADO o vacío")
        return
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    open(f"/root/comc-data/mlb-roy-poll-{ts}.html", "w").write(hh)
    print("guardado mlb-roy-poll-" + ts + ".html")

    # extraer entradas del poll: "**N. Nombre , Equipo (X total vote points, Y first-place votes)**"
    pat = re.compile(r"\*\*(\d+)\.\s+([A-Za-z\.\' ]+?)\s*,\s*([A-Za-z ]+?)\s*\((\d+) total vote points(?:,\s*(\d+) first-place votes)?\)\*\*", re.S)
    print("\n=== RANKING (del poll de agosto 2026) ===")
    for m in pat.finditer(hh):
        num, nombre, equipo, puntos, primeros = m.groups()
        print(f"  {num:>2}. {nombre.strip():25} {equipo.strip():22} | {puntos} pts | {primeros or 0} votos 1º")

    # "Others receiving votes"
    m2 = re.search(r"Others receiving votes:\s*([^\"}]+)", hh)
    if m2:
        print("\nOthers:", m2.group(1).strip()[:300])

if __name__ == "__main__":
    main()
