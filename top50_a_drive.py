#!/usr/bin/env python3
"""top50_a_drive.py — añade pestaña Top-50 al spreadsheet de Drive (COMC - Punto de Mira)."""
import json, urllib.request, urllib.parse, sys

SPREADSHEET_ID = "1akdKxf9d5I6u8rM6z0EuwU7AtUujpj3ffVuadjtCH1s"
CREDS = "/root/.local/share/gogcli/credentials.json"

# --- 1. token OAuth desde credenciales guardadas de gog ---
creds = json.load(open(CREDS))
def find(d, key):
    if isinstance(d, dict):
        for k, v in d.items():
            if k == key:
                return v
            r = find(v, key)
            if r is not None:
                return r
    elif isinstance(d, list):
        for v in d:
            r = find(v, key)
            if r is not None:
                return r
    return None

cid = find(creds, "client_id") or find(creds, "ClientID")
csec = find(creds, "client_secret") or find(creds, "ClientSecret")
rtok = find(creds, "refresh_token") or find(creds, "RefreshToken")
if not (cid and csec and rtok):
    print("ERROR: no encuentro client_id/client_secret/refresh_token en", CREDS)
    print(json.dumps(creds, indent=1)[:800])
    sys.exit(1)

data = urllib.parse.urlencode({
    "client_id": cid, "client_secret": csec, "refresh_token": rtok,
    "grant_type": "refresh_token",
}).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
tok = json.load(urllib.request.urlopen(req))["access_token"]
print("token OK")

def api(url, body=None, method=None):
    h = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    r = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                               headers=h, method=method or ("POST" if body else "GET"))
    try:
        return json.load(urllib.request.urlopen(r))
    except urllib.error.HTTPError as e:
        return {"error": e.code, "msg": e.read().decode()[:500]}

# --- 2. crear pestaña Top-50 si no existe ---
meta = api(f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}?fields=sheets(properties(title,sheetId))")
if "error" in meta:
    print("ERROR meta:", meta); sys.exit(1)
tabs = [s["properties"]["title"] for s in meta["sheets"]]
if "Top-50" not in tabs:
    r = api(f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}:batchUpdate",
            {"requests": [{"addSheet": {"properties": {"title": "Top-50"}}}]})
    print("addSheet:", "OK" if "error" not in r else r)
else:
    print("pestaña Top-50 ya existe")

# --- 3. escribir datos ---
rows = json.load(open("/tmp/scan-top50.json"))
rows.sort(key=lambda r: (r.get("min") is None, r.get("min") or 0))
headers = ["Jugador", "Mín $", "2º $", "Gap %", "Copias", "Al mín", "Cerca mín",
           "Ventas 7d", "Vel/día", "Días inv.", "Turnover %", "Fecha"]
values = [headers]
for r in rows:
    values.append([
        r.get("nombre", ""), r.get("min", ""), r.get("seg", ""), r.get("gap", ""),
        r.get("copias", ""), r.get("n_min", ""), r.get("n_cerca", ""),
        r.get("ventas_7d", ""), r.get("vel_dia", ""), r.get("dias_inv", ""),
        r.get("turnover", ""), r.get("fecha", ""),
    ])

r = api(f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/Top-50!A1:L{len(values)}?valueInputOption=RAW",
        {"values": values}, method="PUT")
print("update:", "OK" if "error" not in r else r)
print("filas:", len(values) - 1)
