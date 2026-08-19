#!/usr/bin/env python3
"""
SOLUCION: Obtener historial de ventas de COMC

RESUMEN DEL DIAGNÓSTICO
========================
El endpoint CardPopupService.asmx/GetHistoricalSalesInfo falla por DOS razones:

1. REQUIERE LOGIN (AuthCookie):
   La página de error muestra "Sign In" con ReturnURL al endpoint AJAX. 
   TODOS los métodos del servicio fallan (GetCardPopupNew, GetSuggestedPriceInfo, 
   GetHistoricalSalesInfo). Solo funciona /CardPopupService.asmx/js (proxy JS).
   La autenticación usa Azure B2C (OAuth con JavaScript → no automatizable vía HTTP POST simple).

2. REQUIERE "HISTORY POINTS" (o "History Points"):
   COMC implementó un sistema de puntos: 1 History Point = $1 de Store Credit añadido.
   Se gasta 1 punto al ver el historial de ventas de un producto (válido 24h).
   Sin puntos, incluso logueado, el popup muestra "View History" en vez de los datos.

Fuentes:
- https://comc.zendesk.com/hc/en-us/articles/7154073803163-The-COMC-Sales-Chart  
- https://www.comc.com/Points

ESTRATEGIA DE SOLUCIÓN
=======================
La solución COMPLETA requiere 3 pasos:
  A) Crear cuenta COMC + añadir Store Credit para History Points
  B) Login manual UNA VEZ vía navegador persistente (Playwright)
  C) Scraping automático usando el perfil persistente

ALTERNATIVA INMEDIATA (sin login ni puntos):
  Usar los precios del MURO (asking prices) como comps, extraídos de la página
  pública de la carta. El script comc-scan*.py ya hace esto. Los 49 precios
  del muro ($10.03 - $20.95 en Harper) dan una buena referencia de mercado.

ESTE SCRIPT
============
Este script implementa la solución B+C: login vía navegador persistente
Playwright (headful con Xvfb si no hay display) y scraping del historial.
"""

import sys, time, json, os, re, subprocess, atexit
from pathlib import Path

PROFILE_DIR = os.path.expanduser("~/.comc-profile")
CARD_URL_TEMPLATE = "https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639"

# ─── helpers ─────────────────────────────────────────────────────────────

def ensure_xvfb():
    """Start virtual display if needed."""
    if os.environ.get("DISPLAY"):
        return
    subprocess.run(["pkill", "-f", "Xvfb :99"], capture_output=True)
    time.sleep(1)
    subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x800x24", "-ac"])
    time.sleep(2)
    os.environ["DISPLAY"] = ":99"
    print("[Xvfb] started on :99", flush=True)


def wait_for_page(page, timeout=30):
    """Wait for page to NOT be Cloudflare challenge."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        title = page.title()
        if "Just a moment" not in title:
            return True
        print("  Cloudflare... ({:.0f}s)".format(deadline - time.time()), flush=True)
        time.sleep(2)
    return False


# ─── login ────────────────────────────────────────────────────────────────

def login_comc(headless=True):
    """Log into COMC using Playwright persistent context.
    
    On first run, opens a browser. Log in manually, then close.
    On subsequent runs, reuses the saved session.
    
    Returns: Playwright browser context (caller must close it).
    """
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth
    
    os.makedirs(PROFILE_DIR, exist_ok=True)
    
    p = sync_playwright().start()
    ctx = p.chromium.launch_persistent_context(
        PROFILE_DIR,
        headless=headless,
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
        ],
        viewport={"width": 1280, "height": 800},
    )
    
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    if not headless:
        Stealth().apply_stealth_sync(page)
    
    # Check if already logged in
    page.goto("https://www.comc.com/", timeout=60000, wait_until="domcontentloaded")
    time.sleep(3)
    
    logged_in = bool(re.search(r"Sign\s*Out|Log\s*Out", page.content(), re.I))
    if logged_in:
        print("[login] Already logged in!", flush=True)
        return ctx, page
    
    print("[login] NOT logged in. Opening login page...", flush=True)
    print("[login] MANUAL STEP: Log in to COMC in the browser window.", flush=True)
    print("[login] After login, press Enter in this terminal to continue.", flush=True)
    
    page.goto("https://www.comc.com/Account/Login", timeout=60000, wait_until="domcontentloaded")
    time.sleep(3)
    
    # Wait for manual login
    input("\n>>> Press Enter after logging in to COMC (or Ctrl+C to cancel)... ")
    
    # Verify login
    page.goto("https://www.comc.com/", timeout=60000, wait_until="domcontentloaded")
    time.sleep(2)
    logged_in = bool(re.search(r"Sign\s*Out|Log\s*Out", page.content(), re.I))
    print("[login] Login status: {}".format("SUCCESS" if logged_in else "FAILED"), flush=True)
    
    # Save cookies
    cookies = ctx.cookies()
    Path("/root/comc-data").mkdir(exist_ok=True)
    with open("/root/comc-data/auth-cookies.json", "w") as f:
        json.dump(cookies, f, indent=2)
    print("[login] Saved {} cookies".format(len(cookies)), flush=True)
    
    return ctx, page


# ─── sales scraping ───────────────────────────────────────────────────────

def scrape_sales_history(page, card_url, card_id=None, item_id=0):
    """Scrape sales history for a card.
    
    Strategy: Navigate to card page, click the "4 year sales" link,
    extract data from the resulting popup/modal.
    """
    # Navigate to card page
    page.goto(card_url, timeout=60000, wait_until="domcontentloaded")
    time.sleep(3)
    
    if not wait_for_page(page, 15):
        print("[scrape] Cloudflare blocked card page", flush=True)
        return []
    
    content = page.content()
    
    # Method A: Check if sales data is inline in the page
    sales_from_dom = page.evaluate("""
        () => {
            const data = [];
            // Look for any element with data-sold-price or sparkline data
            document.querySelectorAll('[data-sold-price], .sale-row, .sale-item, tr[class*="sale"]').forEach(el => {
                const txt = (el.innerText || '').trim();
                data.push(txt);
            });
            return data;
        }
    """)
    if sales_from_dom:
        print("[scrape] Found {} inline sales entries".format(len(sales_from_dom)), flush=True)
        for s in sales_from_dom[:5]:
            print("  {}".format(s[:100]), flush=True)
    
    # Method B: Click "4 year sales" link and scrape popup
    sales_link = page.locator("a:has-text('4 year sales')").first
    if sales_link.count() > 0:
        print("[scrape] Clicking '4 year sales' link...", flush=True)
        sales_link.click()
        time.sleep(3)
        
        # Wait for popup/modal
        try:
            page.wait_for_selector(".modal, .popup, [class*='popup'], [class*='modal'], table", timeout=10000)
        except:
            pass
        time.sleep(2)
        
        # Extract sales rows from popup
        sales_data = page.evaluate("""
            () => {
                const results = [];
                // Try multiple selector patterns for sales history tables
                const selectors = [
                    'table tbody tr', 
                    '.sales-table tr', 
                    '.history-table tr',
                    '[class*="sale"] tr',
                    '.modal table tr',
                    '.popup table tr',
                    'table tr:has(td)'
                ];
                
                for (const sel of selectors) {
                    const rows = document.querySelectorAll(sel);
                    for (const row of rows) {
                        const txt = (row.innerText || '').trim();
                        // Filter: must contain both a date-like pattern and a price
                        if (/\\d{1,2}[\\/\\-]\\d{1,2}[\\/\\-]\\d{2,4}/.test(txt) && /\\$/.test(txt)) {
                            if (!results.includes(txt)) {
                                results.push(txt);
                            }
                        }
                    }
                    if (results.length > 0) break;
                }
                return results;
            }
        """)
        
        if sales_data:
            print("[scrape] Found {} sales entries in popup".format(len(sales_data)), flush=True)
            for s in sales_data[:10]:
                print("  {}".format(s[:150]), flush=True)
            return sales_data
        else:
            print("[scrape] No sales data found in popup (no History Points?)", flush=True)
            # Screenshot for debugging
            page.screenshot(path="/root/comc-data/sales-popup-debug.png")
            print("[scrape] Screenshot saved to /root/comc-data/sales-popup-debug.png", flush=True)
    else:
        print("[scrape] '4 year sales' link NOT found (not logged in?)", flush=True)
    
    # Method C: Try AJAX call (in browser context, carries auth cookies)
    if not sales_from_dom:
        print("[scrape] Trying AJAX call from browser context...", flush=True)
        card_id = card_id or "31038639"
        ajax_result = page.evaluate("""
            async (data) => {
                try {
                    const res = await fetch('/CardPopupService.asmx/GetHistoricalSalesInfo', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json; charset=utf-8',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: JSON.stringify({
                            sourceElement: 'hp' + data.cardId + '_0_',
                            productKey: data.productKey,
                            itemID: data.itemId
                        })
                    });
                    const text = await res.text();
                    return {status: res.status, ok: res.ok, text: text.substring(0, 5000)};
                } catch(e) {
                    return {error: String(e)};
                }
            }
        """, {"cardId": card_id, "productKey": "{} 0 ".format(card_id), "itemId": item_id})
        
        print("[scrape] AJAX result: {}".format(json.dumps(ajax_result)[:500]), flush=True)
        if ajax_result.get("ok") and ajax_result.get("text", "").startswith("{"):
            return [ajax_result["text"]]
    
    return sales_from_dom


# ─── main ─────────────────────────────────────────────────────────────────

def main():
    import argparse
    ap = argparse.ArgumentParser(description="COMC Sales History Scraper")
    ap.add_argument("--login-only", action="store_true", help="Only log in, then exit")
    ap.add_argument("--headless", action="store_true", default=True,
                    help="Run browser headless (default)")
    ap.add_argument("--headful", action="store_true", 
                    help="Run browser headful (with Xvfb)")
    ap.add_argument("--card-url", default=CARD_URL_TEMPLATE,
                    help="Card page URL")
    ap.add_argument("--card-id", default="31038639",
                    help="Card ID for AJAX call")
    ap.add_argument("--item-id", type=int, default=0,
                    help="Item ID for AJAX call (0 = base card)")
    args = ap.parse_args()
    
    headless = not args.headful
    
    if headless:
        print("[main] Headless mode. For manual login, use --headful", flush=True)
    else:
        ensure_xvfb()
    
    try:
        ctx, page = login_comc(headless=headless)
    except Exception as e:
        print("[main] Login failed: {}".format(e), flush=True)
        print("[main] Retry with --headful for manual login.", flush=True)
        return 1
    
    if args.login_only:
        ctx.close()
        return 0
    
    sales = scrape_sales_history(page, args.card_url, args.card_id, args.item_id)
    
    if sales:
        print("\n[main] === SALES HISTORY ===")
        print(json.dumps(sales, indent=2))
    else:
        print("\n[main] NO sales history extracted.")
        print("[main] Cause: COMC requires login + History Points to view sales history.")
        print("[main] Add Store Credit at https://www.comc.com/Points to earn History Points.")
    
    ctx.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
