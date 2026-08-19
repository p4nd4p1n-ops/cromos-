import re
import subprocess
import sys

BASE = "/root/comc-scripts"
CHECKLIST = BASE + "/checklist-rc-2025-26-comc.md"
WATCHLIST = BASE + "/watchlist-multideporte.txt"
EXCLUIDOS = {"VJ Edgecombe"}

def rookies_nba():
    out = []
    with open(CHECKLIST, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\|\s*([^|]+?)\s*\|\s*c\d+\s*\|\s*\d+\s*\|", line)
            if m:
                out.append(m.group(1).strip())
    return out

def otros_deportes():
    out = []
    with open(WATCHLIST, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#"):
                out.append(s)
    return out

vistos = set()
jugadores = []
for j in otros_deportes() + rookies_nba():
    if j not in EXCLUIDOS and j not in vistos:
        vistos.add(j)
        jugadores.append(j)

lim = int(sys.argv[1]) if len(sys.argv) > 1 else 0
if lim:
    jugadores = jugadores[:lim]
    print("MODO PRUEBA: solo los primeros", lim)

print("Lanzando player_scan.py con " + str(len(jugadores)) + " jugadores", flush=True)
subprocess.run(["/usr/bin/python3", BASE + "/player_scan.py"] + jugadores, check=True)
