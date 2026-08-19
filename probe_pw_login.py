#!/usr/bin/env python3
"""Login to COMC via Playwright (headless) and capture AuthCookie for AJAX calls."""
import sys, time, json, urllib.request
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

USER = "dragon941"
PASS = "passkobe1234+"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled",
                  "--disable-dev-shm-usage"]
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )
        page = ctx.new_page()

        # Enable stealth
        Stealth().apply_stealth_sync(page)

        # Step 1: Navigate to COMC login page
        print("Step 1: Navigating to login page...", flush=True)
        page.goto("https://www.comc.com/Account/Login", timeout=90000, wait_until="domcontentloaded")
        time.sleep(3)
        print("URL:", page.url, flush=True)

        # Check if we're on Azure B2C
        if "b2clogin" in page.url or "microsoftonline" in page.url:
            print("Redirected to Azure B2C login", flush=True)

            # Check for B2C-specific elements
            print("Page title:", page.title(), flush=True)

            # Try to fill in the email/username field
            # Azure B2C typically has email field with placeholder or id
            selectors_to_try = [
                "input[type='email']",
                "input#email",
                "input[name='Email']",
                "input[name='logonIdentifier']",
                "input#logonIdentifier",
                "input[placeholder*='email' i]",
                "input[placeholder*='Email']",
                "input[placeholder*='mail']",
                "#signInName",
                "input[name='signInName']",
            ]

            email_found = False
            for sel in selectors_to_try:
                el = page.locator(sel)
                if el.count() > 0 and el.first.is_visible():
                    print("Found email field:", sel, flush=True)
                    try:
                        el.first.fill(USER)
                        email_found = True
                        time.sleep(1)
                        # Press Enter or click Next
                        next_btn = page.locator("button:has-text('Next'), button:has-text('Siguiente'), input[type='submit']").first
                        if next_btn.count() > 0:
                            print("Clicking Next...", flush=True)
                            next_btn.click()
                            time.sleep(3)
                    except Exception as e:
                        print("Error filling email:", e, flush=True)
                    break

            if not email_found:
                # Dump page content
                print("EMAIL FIELD NOT FOUND. Dumping body...", flush=True)
                body = page.locator("body").first
                if body.count() > 0:
                    text = body.inner_text()
                    print("BODY TEXT (first 2000):", text[:2000], flush=True)
                # Screenshot
                page.screenshot(path="/root/comc-data/login-step1.png")
                print("Saved screenshot to /root/comc-data/login-step1.png", flush=True)

            # Check for password field
            time.sleep(3)
            pw_selectors = [
                "input[type='password']",
                "input#password",
                "input[name='Password']",
                "input[name='passwd']",
                "input#passwd",
            ]

            pw_found = False
            for sel in pw_selectors:
                el = page.locator(sel)
                if el.count() > 0 and el.first.is_visible():
                    print("Found password field:", sel, flush=True)
                    try:
                        el.first.fill(PASS)
                        pw_found = True
                        time.sleep(1)
                        # Click Sign In
                        signin_btn = page.locator("button:has-text('Sign in'), button:has-text('Iniciar sesion'), #idSIButton9, input[value='Sign in']").first
                        if signin_btn.count() > 0:
                            print("Clicking Sign In...", flush=True)
                            signin_btn.click()
                            time.sleep(5)
                    except Exception as e:
                        print("Error filling password:", e, flush=True)
                    break

            if not pw_found:
                page.screenshot(path="/root/comc-data/login-step2.png")
                print("Password field not found, saved screenshot", flush=True)

            # Step 2: Wait for redirect back to COMC
            print("Waiting for redirect back to COMC...", flush=True)
            for i in range(30):
                if "comc.com" in page.url and "b2clogin" not in page.url and "microsoftonline" not in page.url:
                    print("Back on COMC:", page.url[:100], flush=True)
                    break
                time.sleep(2)
                print("  still on:", page.url[:80], flush=True)

        else:
            print("Not redirected to Azure?", flush=True)
            # Try direct form submission
            page.screenshot(path="/root/comc-data/login-direct.png")

        # Step 3: Extract cookies
        print("\nStep 3: Extracting cookies...", flush=True)
        all_cookies = ctx.cookies()
        auth_cookie = None
        for c in all_cookies:
            print("  Cookie: {} = {}...".format(c.get("name"), str(c.get("value", ""))[:50]), flush=True)
            if c.get("name") == "AuthCookie":
                auth_cookie = c

        if auth_cookie:
            print("\nAUTHCOOKIE FOUND!", flush=True)
            print("  Value: {}...".format(auth_cookie.get("value", "")[:80]), flush=True)
            # Step 4: Try AJAX call with this cookie
            print("\nStep 4: Testing AJAX call...", flush=True)
            
            # Navigate to the card page first (establishes session)
            page.goto("https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639",
                      timeout=60000, wait_until="domcontentloaded")
            time.sleep(3)
            print("Card page URL:", page.url[:100], flush=True)
            
            # Extract ASP.NET_SessionId and other cookies
            all_cookies2 = ctx.cookies()
            anti_xsrf = None
            session_id = None
            for c in all_cookies2:
                if c.get("name") == "__AntiXsrfToken":
                    anti_xsrf = c.get("value")
                if c.get("name") == "ASP.NET_SessionId":
                    session_id = c.get("value")

            # Make AJAX call via JavaScript eval
            print("Making AJAX call...", flush=True)
            result = page.evaluate("""
                async () => {
                    const response = await fetch('/CardPopupService.asmx/GetHistoricalSalesInfo', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json; charset=utf-8',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: JSON.stringify({
                            sourceElement: 'hp31038639_0_',
                            productKey: '31038639 0 ',
                            itemID: 0
                        })
                    });
                    const text = await response.text();
                    return {status: response.status, text: text.substring(0, 2000)};
                }
            """)
            print("AJAX result:", json.dumps(result, indent=2)[:2000], flush=True)
        else:
            print("\nNO AUTHCOOKIE - login failed", flush=True)
            page.screenshot(path="/root/comc-data/login-final.png")

        browser.close()

if __name__ == "__main__":
    sys.exit(main())
