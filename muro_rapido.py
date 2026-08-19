#!/usr/bin/env python3
"""muro_rapido.py <url_carta> — muro de HOY de UNA carta, rápido (1 petición).
Imprime: 1er/2º escalón, copias, ventas 7d, primeros vendedores. 12/08/2026."""
import sys, re, json, time, random, datetime
sys.path.insert(0, "/root/comc-scripts")
import muro_scan as ms

def main():
    url = sys.argv[1]
    html = ms.get_html(url)
    if not html or len(html) < 2000:
        print(json.dumps({"error": "sin_html"}))
        return
    # muro
    items = re.findall(r'id="hp(\d+)"[^>]*>\$([\d,]+\.\d{2})<', html)
    owners = {}
    for m in re.finditer(r'Owner: <strong><a href="/Users/([^"]+)"[^>]*>([^<]+)</a></strong>.*?Item: (\d+)', html, re.S):
        owners[m.group(3)] = m.group(2)
    muro = sorted([{"precio": float(p.replace(",", "")), "owner": owners.get(i, "?")} for i, p in items], key=lambda x: x["precio"])
    # copias
    copias = 0
    m = re.search(r'class="allsellers"[^>]*>.*?qtyforsale[^>]*>\s*&nbsp;?\((\d+)\)', html, re.S)
    if m:
        copias = int(m.group(1))
    # ventas 7d
    sales = re.findall(r"([A-Z][a-z]{2} \d{1,2}, \d{4})[^$]*?\$([\d,]+\.\d{2})", html)
    hoy = datetime.date.today()
    v7 = 0
    for fstr, _ in sales:
        try:
            if (hoy - datetime.datetime.strptime(fstr, "%b %d, %Y").date()).days <= 7:
                v7 += 1
        except ValueError:
            pass
    resumen = {}
    for m_ in muro:
        e = resumen.setdefault(m_["precio"], {"copias": 0, "owners": []})
        e["copias"] += 1
        if m_["owner"] not in e["owners"]:
            e["owners"].append(m_["owner"])
    out = {"min": muro[0]["precio"] if muro else None,
           "seg": muro[1]["precio"] if len(muro) > 1 else None,
           "copias": copias, "v7d": v7,
           "muro": "; ".join(f"{p}: {e['copias']} ({'/'.join(e['owners'])})" for p, e in sorted(resumen.items()))[:500]}
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
