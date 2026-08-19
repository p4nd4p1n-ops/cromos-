#!/usr/bin/env python3
"""Login COMC cuenta fantasma vía Playwright+stealth 2.x, perfil persistente."""
import sys, time
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

USER = "dragon941"
PASS = "passkobe1234+"
PROFILE = "/root/comc-profile"

def main():
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE,
            headless=False,
            args=["--disable-blink-features=AutomationControlled",
                  "--no-sandbox", "--start-maximized"],
            viewport={"width": 1280, "height": 720},
        )
        page = ctx.new_page()
        Stealth().apply_stealth_sync(page)
        print("-> navegando a COMC", flush=True)
        page.goto("https://www.comc.com/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(3)
        title = page.title()
        print("title:", title[:80], flush=True)
        if "Just a moment" in title or "challenge" in title.lower():
            print("RESULTADO: CHALLENGE CLOUDFLARE", flush=True)
            ctx.close()
            return 2
        page.goto("https://signin.comc.com/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(3)
        print("url login:", page.url, flush=True)
        inputs = page.locator("input").all()
        print("inputs:", len(inputs), flush=True)
        for i, inp in enumerate(inputs[:8]):
            try:
                print(f"  [{i}] type={inp.get_attribute('type')} name={inp.get_attribute('name')} id={inp.get_attribute('id')} ph={inp.get_attribute('placeholder')}", flush=True)
            except Exception:
                pass
        ctx.close()

if __name__ == "__main__":
    sys.exit(main())
