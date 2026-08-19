#!/usr/bin/env python3
"""Login COMC via Playwright headful (Xvfb). More patient approach."""
import sys, time, json, os, re, subprocess, atexit
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

USER = "dragon941"
PASS = "passkobe1234+"
PROFILE = "/root/comc-profile-pw2"

def kill_xvfb():
    subprocess.run(["pkill", "-f", "Xvfb :99"], capture_output=True)
atexit.register(kill_xvfb)

def main():
    os.makedirs(PROFILE, exist_ok=True)
    
    # Start Xvfb
    kill_xvfb()
    time.sleep(1)
    subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x800x24", "-ac"])
    time.sleep(2)
    os.environ["DISPLAY"] = ":99"
    print("Xvfb started", flush=True)
    
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            PROFILE,
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
            viewport={"width": 1280, "height": 800},
        )
        
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        Stealth().apply_stealth_sync(page)
        
        # Helper: wait for page to not be Cloudflare challenge
        def wait_for_cf(page, timeout=60):
            """Wait until page is NOT on Cloudflare challenge."""
            deadline = time.time() + timeout
            while time.time() < deadline:
                title = page.title()
                if "Just a moment" not in title and "challenge" not in title.lower():
                    return True
                print("  Waiting for Cloudflare... ({:.0f}s left)".format(deadline - time.time()), flush=True)
                time.sleep(3)
            return False
        
        # Step 1: Navigate to COMC home
        print("Step 1: COMC home...", flush=True)
        page.goto("https://www.comc.com/", timeout=120000, wait_until="domcontentloaded")
        if not wait_for_cf(page, 90):
            page.screenshot(path="/root/comc-data/cf-stuck-home.png")
            print("STUCK on Cloudflare at home", flush=True)
            ctx.close()
            return 1
        
        print("Home loaded:", page.title()[:80], flush=True)
        
        # Step 2: Navigate to login
        print("Step 2: Login page...", flush=True)
        page.goto("https://www.comc.com/Account/Login", timeout=120000, wait_until="domcontentloaded")
        if not wait_for_cf(page, 90):
            page.screenshot(path="/root/comc-data/cf-stuck-login.png")
            print("STUCK on Cloudflare at login", flush=True)
            ctx.close()
            return 1
        
        print("Login page:", page.title()[:100], flush=True)
        print("Login URL:", page.url[:100], flush=True)
        page.screenshot(path="/root/comc-data/login-loaded.png")
        
        # Step 3: Find and fill login form
        # Check if we're on Azure B2C or COMC's own login
        if "b2clogin" in page.url or "microsoftonline" in page.url:
            print("Azure B2C detected", flush=True)
            
            # Wait for email field
            try:
                page.wait_for_selector("input[type='email'], #signInName, #logonIdentifier", timeout=15000)
            except:
                pass
            
            time.sleep(3)
            
            # Fill email
            email_sel = "input[type='email'], #signInName, input[name='signInName'], #email"
            email_el = page.locator(email_sel).first
            if email_el.count() > 0 and email_el.is_visible():
                email_el.click()
                email_el.fill(USER)
                print("Filled email", flush=True)
                time.sleep(1)
                page.screenshot(path="/root/comc-data/b2c-email-filled.png")
                
                # Click Next
                page.keyboard.press("Enter")
                time.sleep(5)
                
                # Wait for password
                try:
                    page.wait_for_selector("input[type='password']", timeout=15000)
                    time.sleep(2)
                except:
                    pass
                
                pw_el = page.locator("input[type='password']").first
                if pw_el.count() > 0 and pw_el.is_visible():
                    pw_el.click()
                    pw_el.fill(PASS)
                    print("Filled password", flush=True)
                    time.sleep(1)
                    page.screenshot(path="/root/comc-data/b2c-pw-filled.png")
                    
                    # Click Sign In or press Enter
                    page.keyboard.press("Enter")
                    time.sleep(5)
                    
                    # Check for "Stay signed in" prompt (Azure MFA)
                    if "Stay signed in" in page.content() or "Keep me signed in" in page.content():
                        print("Stay signed in prompt", flush=True)
                        page.keyboard.press("Enter")
                        time.sleep(3)
                    
                    # Wait for redirect back to COMC
                    print("Waiting for redirect to COMC...", flush=True)
                    for i in range(40):
                        if "comc.com" in page.url and "b2clogin" not in page.url and "microsoftonline" not in page.url:
                            print("Redirected to COMC!", flush=True)
                            break
                        time.sleep(2)
                        print("  URL:", page.url[:80], flush=True)
            else:
                print("Email field not found!", flush=True)
                page.screenshot(path="/root/comc-data/b2c-no-email.png")
                # Dump page text
                try:
                    text = page.locator("body").inner_text()
                    print("BODY:", text[:2000], flush=True)
                except:
                    pass
        else:
            print("COMC native login (not B2C)", flush=True)
            page.screenshot(path="/root/comc-data/login-native.png")
            body = page.locator("body").inner_text()[:2000] if page.locator("body").count() > 0 else ""
            print("BODY:", body, flush=True)
        
        # Step 4: Navigate to card page to test
        print("\nStep 4: Testing on card page...", flush=True)
        page.goto("https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639",
                  timeout=60000, wait_until="domcontentloaded")
        wait_for_cf(page, 30)
        time.sleep(2)
        
        content = page.content()
        logged_in = bool(re.search(r'Sign\s*Out|Log\s*Out', content, re.I))
        print("Logged in:", logged_in, flush=True)
        print("Has '4 year sales':", "4 year sales" in content, flush=True)
        print("Has 'View Chart':", "View Chart" in content, flush=True)
        page.screenshot(path="/root/comc-data/card-page-logged.png")
        
        # Step 5: Try AJAX from browser context
        print("\nStep 5: AJAX call...", flush=True)
        result = page.evaluate("""
            async () => {
                try {
                    const res = await fetch('/CardPopupService.asmx/GetHistoricalSalesInfo', {
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
                    const text = await res.text();
                    return {status: res.status, ok: res.ok, text: text.substring(0, 3000)};
                } catch(e) {
                    return {error: String(e)};
                }
            }
        """)
        print("AJAX:", json.dumps(result, indent=2)[:3000], flush=True)
        
        # Step 6: Save all cookies
        cookies = ctx.cookies()
        with open("/root/comc-data/auth-cookies-pw.json", "w") as f:
            json.dump(cookies, f, indent=2)
        print("\n{} cookies saved".format(len(cookies)), flush=True)
        for c in cookies:
            if c.get("name") in ("AuthCookie", ".ASPXAUTH", "__AntiXsrfToken"):
                print("  {}: {}...".format(c.get("name"), str(c.get("value",""))[:50]), flush=True)
        
        ctx.close()
    
    print("\nDONE", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(main())
