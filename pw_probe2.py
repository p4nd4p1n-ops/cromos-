#!/usr/bin/env python3
"""Probe 2: esperar challenge Cloudflare, capturar pantalla, ver si pasa."""
import sys, time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

PROFILE = "/root/comc-profile"

def main():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE, headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            viewport={"width": 1280, "height": 720},
        )
        page = ctx.new_page()
        Stealth().apply_stealth_sync(page)
        page.goto("https://www.comc.com/", timeout=60000, wait_until="domcontentloaded")
        # esperar a ver si el challenge se resuelve solo (hasta 60s)
        ok = False
        for i in range(12):
            time.sleep(5)
            title = page.title()
            print(f"[{i*5}s] title: {title[:60]}", flush=True)
            if "Just a moment" not in title:
                ok = True
                break
        page.screenshot(path="/tmp/pw_challenge.png")
        print("RESULTADO:", "PASO" if ok else "CHALLENGE PERSISTE", flush=True)
        ctx.close()
        return 0 if ok else 2

if __name__ == "__main__":
    sys.exit(main())
