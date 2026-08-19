#!/usr/bin/env python3
"""pihole_alerts.py v3 — análisis DNS minimalista, solo señales reales.

Filosofía v3: en una red doméstica, el 99.9% del tráfico DNS es legítimo.
Los CDN (CloudFront, Fastly, Akamai) usan subdominios aleatorios por diseño.
La entropía de dominios permitidos NO es señal de amenaza.
La señal real está en: (1) dominios BLOQUEADOS por categoría, (2) DNS tunneling,
(3) dispositivos NUEVOS en la LAN, (4) queries a TLDs de alto riesgo.

Eliminado de v2:
- Detección DGA/entropía en TODOS los dominios (falsos positivos masivos con CDN)
- Alerta de "sin categorizar" en bloqueos (la mayoría son ads)
- Umbrales de volumen (ya ajustados, no alertan si todo normal)
"""
import re, os, datetime, subprocess
from collections import Counter, defaultdict

# ─── CONFIG ──────────────────────────────────────────────────────────────────
LOG_HOST = "/var/log/pihole/pihole.log"
ALERT_FILE = "/root/comc-data/pihole-alert.txt"
VENTANA_HORAS = 26

CONOCIDOS = {
    "192.168.0.1":   ("router Lowi",      "router"),
    "192.168.0.10":  ("PC Pin",            "pc"),
    "192.168.0.13":  ("TV Sony",           "tv"),
    "192.168.0.30":  ("tablet",            "iot"),
    "192.168.0.50":  ("RPi?",              "iot"),
    "192.168.0.58":  ("RPi?",              "iot"),
    "192.168.0.101": ("móvil Pin",         "phone"),
    "192.168.0.102": ("CT kobe",           "server"),
    "192.168.0.129": ("portátil",          "pc"),
    "127.0.0.1":     ("localhost",         "infra"),
    "127.0.0.53":    ("systemd-resolved",  "infra"),
    "172.17.0.1":    ("Docker gateway",    "infra"),
    "0.0.0.0":       ("blocked-reply",     "infra"),
}

# Umbrales de volumen por tipo (consultas/24h)
UMBRAL_VOLUMEN = {
    "pc":     15000,
    "tv":      5000,
    "phone":   3000,
    "server": 10000,
    "iot":      500,
    "router":  1000,
    "infra":   2000,
    None:      2000,
}

# ─── DOMINIOS LEGÍTIMOS ─────────────────────────────────────────────────────
# Marcas y sus sufijos oficiales + dominios relacionados legítimos
MARCAS_OFICIALES = {
    "whatsapp":   [".whatsapp.net", ".whatsapp.com", ".whatsapp.org"],
    "facebook":   [".facebook.com", ".facebook.net", ".fb.com", ".fbcdn.net",
                   ".facebookmail.com", ".meta.com", ".messenger.com",
                   ".oculus.com", ".atlassolutions.com"],
    "google":     [".google.com", ".google.es", ".google",  # .google es TLD de Google
                   ".googleapis.com", ".gstatic.com", ".googleusercontent.com",
                   ".google-analytics.com", ".googletagmanager.com",
                   ".googleadservices.com", ".googlesyndication.com",
                   ".googlevideo.com", ".googlemail.com", ".gmail.com",
                   ".youtube.com", ".ytimg.com", ".googletraveladservices.com",
                   ".chrome.com", ".chromium.org"],
    "amazon":     [".amazon.com", ".amazon.es", ".amazonaws.com",
                   ".amazon.co.uk", ".amazon.de", ".amazon.fr", ".amazon.it",
                   ".amazon-adsystem.com",  # publicidad legítima de Amazon
                   ".amazon.dev", ".aws.dev"],
    "apple":      [".apple.com", ".icloud.com", ".apple-dns.net", ".mzstatic.com",
                   ".apple.news", ".cdn-apple.com"],
    "microsoft":  [".microsoft.com", ".microsoftonline.com", ".live.com",
                   ".office.com", ".office.net", ".windows.com", ".msn.com",
                   ".bing.com", ".xboxlive.com", ".azure.com",
                   ".visualstudio.com", ".github.com", ".linkedin.com",
                   ".skype.com", ".sharepoint.com"],
    "paypal":     [".paypal.com", ".paypal.es", ".paypalobjects.com"],
    "netflix":    [".netflix.com", ".netflix.net", ".nflxvideo.net",
                   ".nflxext.com", ".nflximg.com"],
    "twitter":    [".twitter.com", ".twimg.com", ".x.com"],
    "instagram":  [".instagram.com", ".cdninstagram.com"],
    "spotify":    [".spotify.com", ".spotifycdn.com", ".scdn.co"],
    "dropbox":    [".dropbox.com", ".dropboxapi.com", ".dropboxstatic.com"],
    "ebay":       [".ebay.com", ".ebay.es", ".ebaystatic.com", ".ebayimg.com"],
}

# CDNs / infraestructura cloud — NO escanear dominio principal para marcas
# si el dominio TERMINA con uno de estos sufijos (son rutas de CDN, no phishing)
CDN_SUFFIXES = [
    ".fastly.net", ".fastly-edge.com", ".fastlylb.net",
    ".cloudfront.net",
    ".akamai.net", ".akamaiedge.net", ".akamaihd.net", ".edgesuite.net",
    ".edgekey.net", ".akamaitechnologies.com",
    ".gcdn.co",  # G-Core CDN
    ".cdn77.org", ".cdn77.com",
    ".keycdn.com",
    ".b-cdn.net", ".bunnycdn.com",
    ".cdninstagram.com",  # Facebook CDN
    ".cdninstagram.com",
    ".fbcdn.net",
]

# ─── PATRONES DE ALTO RIESGO (C2, malware, phishing genérico) ───────────────
HIGH_RISK = [
    r"(?i)(stratum\+tcp|nicehash|minexmr|coinhive|cryptonight|monerohash|nanopool)",
    r"(?i)(botnet|command.{0,3}control|ransomware|keylogger|trojan\.)",
    r"(?i)(account-verif(?:y|ication)|secure-verif|login-verify|update-account|"
    r"password-reset|account-recovery|billing-alert)",
    r"(?i)(\.duckdns\.org|\.hopto\.org|\.no-ip\.|\.ddns\.|\.zapto\.org)",
]

# TLDs de alto riesgo (baratos, usados en phishing/malware)
# No alertar solo por el TLD, solo combinado con otra señal
RISKY_TLDS = {".top", ".xyz", ".icu", ".click", ".gq", ".tk", ".ml", ".cf",
              ".ga", ".pw", ".cc", ".work", ".date", ".men", ".loan", ".win"}

# ─── FUNCIONES AUXILIARES ───────────────────────────────────────────────────

def es_ip_interna(ip):
    """True para LAN de Pin, Docker, localhost."""
    if ip.startswith("192.168.0."):
        return True
    if re.match(r"^172\.(1[6-9]|2\d|3[01])\.", ip):  # 172.16.0.0/12 (Docker)
        return True
    if ip.startswith("127.") or ip == "0.0.0.0":
        return True
    return False


def es_cdn(dominio):
    """True si el dominio está bajo un CDN conocido (los subdominios aleatorios son normales)."""
    dominio_l = dominio.lower().rstrip(".")
    for cdn in CDN_SUFFIXES:
        if dominio_l.endswith(cdn):
            return True
    return False


def es_sospechoso_por_marca(dominio):
    """Detecta typos de marca. Solo alerta si NO es CDN y NO es sufijo oficial."""
    dominio_l = dominio.lower().rstrip(".")

    # Si es CDN, los subdominios con nombres de marca son normales
    # (ej: platform.twitter.map.fastly.net → Twitter usando Fastly CDN)
    if es_cdn(dominio_l):
        return None

    for marca, sufijos in MARCAS_OFICIALES.items():
        if marca not in dominio_l:
            continue

        for sufijo in sufijos:
            if dominio_l.endswith(sufijo) or dominio_l == sufijo.lstrip("."):
                return None  # legítimo

        # La marca aparece en el dominio, no bajo sufijo oficial, no es CDN
        # Verificar que la marca sea un token separado (no parte de otra palabra)
        idx = dominio_l.find(marca)
        before_ok = idx == 0 or dominio_l[idx-1] in ".-"
        after_ok = idx + len(marca) == len(dominio_l) or dominio_l[idx + len(marca)] in ".-"
        if before_ok and after_ok:
            return (marca, dominio_l)

    return None


def entropia_subdominio(dominio):
    """Detecta posibles subdominios de DNS tunneling.
    Un label > 50 chars con alta variedad de caracteres → posible encoding."""
    dominio_l = dominio.lower().rstrip(".")
    # Dividir en labels (partes entre puntos)
    labels = dominio_l.split(".")
    for label in labels:
        if len(label) > 50:
            unique = len(set(label))
            ratio = unique / len(label)
            # Base64/hex encoding → >50% caracteres únicos en string largo
            if ratio > 0.5:
                return True
    return False


def categorizar_bloqueo(dominio):
    """Categoriza un dominio bloqueado.
    Cobertura amplia de ad/tracking para minimizar 'unknown' (falsos positivos)."""
    d = dominio.lower()

    # Malware/C2/phishing — SEÑALES REALES DE ALERTA
    for s in [
        r"malware", r"ransom", r"trojan", r"botnet", r"c2", r"exploit",
        r"spyware", r"keylog", r"rootkit", r"dropper", r"coinminer?",
        r"cryptomin", r"miner", r"stealer",
    ]:
        if re.search(s, d):
            return "malware"

    # Phishing
    for s in [
        r"phish", r"fake.{0,3}(login|bank|paypal|apple|google|microsoft|amazon)",
        r"account.{0,5}verif", r"login.{0,3}verify", r"steam.{0,3}commun",
    ]:
        if re.search(s, d):
            return "phishing"

    # Tracking / analytics / telemetría
    for s in [
        r"telemetry", r"analytics", r"track", r"pixel", r"beacon",
        r"collect", r"metrics?", r"stats?\d*\.", r"log\.", r"logging",
        r"mmstat\.com", r"amplitude\.com", r"klaviyo\.com",
        r"sentry\.io", r"customer\.io", r"izooto\.com",
        r"firebaselogging", r"app-measurement", r"crashlytics",
        r"pub\.network", r"truste\.com",
    ]:
        if re.search(s, d):
            return "tracking"

    # Ads
    for s in [
        r"doubleclick", r"googlesyndication", r"googletagmanager",
        r"googleadservices", r"pagead", r"ads", r"advert",
        r"sponsor", r"banner", r"popup", r"adserver",
        r"mmstat\.com", r"pub\.network",
    ]:
        if re.search(s, d):
            return "ads"

    # Si tiene TLD de alto riesgo + no categorizado → potencialmente malicioso
    tld = "." + d.split(".")[-1] if "." in d else ""
    if tld in RISKY_TLDS:
        return "risky-tld"

    return "unknown"


# ─── LECTURA DEL LOG ─────────────────────────────────────────────────────────

def leer_log():
    try:
        r = subprocess.run(
            ["docker", "exec", "pihole", "sh", "-c", f"cat {LOG_HOST}"],
            capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return r.stdout
    except Exception:
        pass
    try:
        if os.path.exists(LOG_HOST):
            return open(LOG_HOST, errors="ignore").read()
    except Exception:
        pass
    return ""


def parse_log():
    contenido = leer_log()
    if not contenido:
        return defaultdict(list), defaultdict(list)

    ahora = datetime.datetime.now()
    corte = ahora - datetime.timedelta(hours=VENTANA_HORAS)

    queries = defaultdict(list)
    bloqueadas_por_ip = defaultdict(list)

    line_re = re.compile(
        r"^([A-Z][a-z]{2}\s+\d{1,2}\s+[\d:]+)\s+\w+\[\d+\]:\s+"
    )
    ultima_ip = None

    for line in contenido.splitlines():
        m = line_re.match(line)
        if not m:
            continue
        fecha_s = m.group(1)
        resto = line[m.end():]

        try:
            ts = datetime.datetime.strptime(fecha_s, "%b %d %H:%M:%S")
            ts = ts.replace(year=ahora.year)
            if ts > ahora + datetime.timedelta(days=1):
                ts = ts.replace(year=ahora.year - 1)
        except ValueError:
            continue
        if ts < corte:
            continue

        # Query normal
        qm = re.match(r"query\[\w+\]\s+(\S+)\s+from\s+([\d.]+)", resto)
        if qm:
            dominio, ip = qm.groups()
            ultima_ip = ip
            queries[ip].append(dominio.rstrip("."))
            continue

        # Bloqueada — asociar a última IP (aproximación razonable para logs no-concurrentes)
        bm = re.match(r"gravity blocked (\S+) is ", resto)
        if bm:
            dominio = bm.group(1).rstrip(".")
            ip = ultima_ip if ultima_ip else "_desconocida"
            bloqueadas_por_ip[ip].append(dominio)

    return queries, bloqueadas_por_ip


# ─── DETECCIÓN ───────────────────────────────────────────────────────────────

def detectar(queries, bloqueadas_por_ip):
    alertas = []
    severidad = {"ALTA": [], "MEDIA": [], "BAJA": []}

    # ── 0. Bloqueadas de alto riesgo (SEÑAL PRINCIPAL) ──────────────────
    for ip, dominios in bloqueadas_por_ip.items():
        categorias = Counter()
        dominios_riesgosos = []
        for d in dominios:
            cat = categorizar_bloqueo(d)
            categorias[cat] += 1
            if cat in ("malware", "phishing", "risky-tld"):
                dominios_riesgosos.append(d)

        nombre = CONOCIDOS.get(ip, (ip,))[0]

        # Solo alertar si hay malware, phishing, o >5 unknowns (patrón raro)
        if categorias.get("malware", 0) > 0:
            severidad["ALTA"].append(
                f"🚨 MALWARE BLOQUEADO: {nombre} ({ip})\n"
                f"   {categorias['malware']} dominios — ej: {', '.join(list(set(dominios_riesgosos))[:3])}"
            )
        if categorias.get("phishing", 0) > 0:
            severidad["ALTA"].append(
                f"🎣 PHISHING BLOQUEADO: {nombre} ({ip})\n"
                f"   {categorias['phishing']} dominios — ej: {', '.join(list(set(dominios_riesgosos))[:3])}"
            )
        if categorias.get("risky-tld", 0) > 0:
            severidad["MEDIA"].append(
                f"⚠️ TLD RIESGOSO BLOQUEADO: {nombre} ({ip})\n"
                f"   {categorias['risky-tld']} dominios en TLDs peligrosos"
            )

    # ── 1. Dispositivos NUEVOS en la LAN ──────────────────────────────
    for ip in set(queries.keys()) | set(bloqueadas_por_ip.keys()):
        if ip in ("_desconocida", "_sin_ip") or ip in CONOCIDOS:
            continue
        if es_ip_interna(ip) and ip.startswith("192.168.0."):
            n = len(queries.get(ip, []))
            if n >= 3:
                severidad["ALTA"].append(
                    f"🆕 NUEVO DISPOSITIVO EN LAN: {ip} ({n} consultas)"
                )

    # ── 2. Dominios de phishing/typos ──────────────────────────────────
    for ip, dominios in queries.items():
        nombre = CONOCIDOS.get(ip, (ip,))[0]
        contador = Counter(dominios)

        for dominio, n in contador.items():
            # 2a. Marca fuera de dominio oficial
            marca_match = es_sospechoso_por_marca(dominio)
            if marca_match:
                marca, dom = marca_match
                # Verificar si es TLD de alto riesgo también (doble confirmación)
                tld = "." + dom.split(".")[-1] if "." in dom else ""
                if tld in RISKY_TLDS:
                    severidad["ALTA"].append(
                        f"🎣 PHISHING PROBABLE: {dom} ({n} consultas)\n"
                        f"   Marca '{marca}' en TLD sospechoso — desde {nombre} ({ip})"
                    )
                else:
                    # Marca fuera de su dominio oficial pero en TLD normal
                    severidad["MEDIA"].append(
                        f"⚠️ DOMINIO NO OFICIAL: {dom} ({n} consultas)\n"
                        f"   Marca '{marca}' fuera de dominio oficial — desde {nombre} ({ip})"
                    )

            # 2b. Patrones de alto riesgo en dominio PERMITIDO
            for pat in HIGH_RISK:
                if re.search(pat, dominio):
                    severidad["ALTA"].append(
                        f"💀 DOMINIO PELIGROSO PERMITIDO: {dominio} ({n} consultas)\n"
                        f"   Patrón: {pat} — desde {nombre} ({ip})"
                    )
                    break

    # ── 3. DNS Tunneling ───────────────────────────────────────────────
    for ip, dominios in queries.items():
        nombre = CONOCIDOS.get(ip, (ip,))[0]
        for dominio, n in Counter(dominios).items():
            if entropia_subdominio(dominio):
                severidad["ALTA"].append(
                    f"🔍 POSIBLE DNS TUNNELING: {dominio} ({n} consultas)\n"
                    f"   Label >50 chars con alta entropía — desde {nombre} ({ip})"
                )

    # ── 4. Volumen anómalo ─────────────────────────────────────────────
    for ip, dominios in queries.items():
        n = len(dominios)
        if n == 0:
            continue
        nombre, tipo_disp = CONOCIDOS.get(ip, (ip, None))
        umbral = UMBRAL_VOLUMEN.get(tipo_disp, UMBRAL_VOLUMEN[None])
        if n > umbral:
            severidad["BAJA"].append(
                f"📊 ALTO VOLUMEN DNS: {nombre} ({ip}) — {n} consultas\n"
                f"   Umbral: {umbral} — suele ser normal para este dispositivo"
            )

    # ── Consolidar ─────────────────────────────────────────────────────
    if severidad["ALTA"]:
        alertas.append("═══ 🚨 ALERTAS DE SEGURIDAD 🚨 ═══")
        alertas.extend(severidad["ALTA"])
    if severidad["MEDIA"]:
        alertas.append("\n═══ ⚠️ AVISOS ⚠️ ═══")
        alertas.extend(severidad["MEDIA"])
    if severidad["BAJA"]:
        alertas.append("\n═══ ℹ️ INFORMACIÓN ℹ️ ═══")
        alertas.extend(severidad["BAJA"])

    return alertas


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    queries, bloqueadas = parse_log()

    if not queries and not any(bloqueadas.values()):
        open(ALERT_FILE, "w").write("")
        return

    alertas = detectar(queries, bloqueadas)

    total_disp = len(set(queries.keys()) | {k for k in bloqueadas if k not in ("_sin_ip", "_desconocida")})
    total_queries = sum(len(v) for v in queries.values())
    total_bloq = sum(len(v) for v in bloqueadas.values())

    if alertas:
        contenido = "\n".join(alertas)
        contenido += (
            f"\n\n─── Resumen ───\n"
            f"Ventana: últimas {VENTANA_HORAS}h\n"
            f"Consultas: {total_queries} | Bloqueadas: {total_bloq} "
            f"({total_bloq*100//max(total_queries,1)}%)\n"
            f"Dispositivos: {total_disp}"
        )
        open(ALERT_FILE, "w").write(contenido)
        print(contenido)
    else:
        open(ALERT_FILE, "w").write("")
        print(
            f"✅ Todo normal ({total_queries} consultas, {total_bloq} bloqueadas, "
            f"{total_disp} dispositivos)"
        )


if __name__ == "__main__":
    main()
