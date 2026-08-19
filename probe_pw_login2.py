#!/usr/bin/env python3
"""Login to COMC via Playwright headless, save auth state, then scrape sales history."""
import sys, time, json, os, re
from playwright.sync_api import sync_playwright

USER = "dragon941"
PASS = "passkobe1234+"
PROFILE = "/root/comc-profile"

def main():
    os.makedirs(PROFILE, exist_ok=True)
    
    with sync_playwright() as p:
        # Use persistent context (saves auth between runs)
        ctx = p.chromium.launch_persistent_context(
            PROFILE,
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",  # reduces memory
                "--disable-extensions",
                "--disable-component-extensions",
                "--disable-background-networking",
            ],
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        
        # Step 1: Go to COMC and check login state
        print("Step 1: Checking login state...", flush=True)
        try:
            page.goto("https://www.comc.com/", timeout=30000, wait_until="domcontentloaded")
        except Exception as e:
            print("ERROR navigating:", str(e)[:200], flush=True)
            # Try with longer timeout
            page.goto("https://www.comc.com/", timeout=60000, wait_until="commit")
        
        time.sleep(3)
        print("URL:", page.url[:100], flush=True)
        print("Title:", page.title()[:100], flush=True)
        
        # Check if already logged in
        content = page.content()
        logged_in = bool(re.search(r'Sign\s*Out|Log\s*Out', content, re.I))
        print("Already logged in:", logged_in, flush=True)
        
        if not logged_in:
            # Step 2: Go to login
            print("Step 2: Navigating to login...", flush=True)
            page.goto("https://www.comc.com/Account/Login", timeout=60000, wait_until="domcontentloaded")
            time.sleep(5)
            print("Login URL:", page.url[:150], flush=True)
            print("Login Title:", page.title()[:100], flush=True)
            
            # Save screenshot for debugging
            page.screenshot(path="/root/comc-data/login-page.png")
            print("Saved screenshot", flush=True)
            
            # Check if we're on Azure B2C
            if "b2clogin" in page.url or "microsoftonline" in page.url:
                print("On Azure B2C login page", flush=True)
                
                # Dump all input fields
                inputs = page.locator("input").all()
                print("Found {} inputs".format(len(inputs)), flush=True)
                for i, inp in enumerate(inputs[:10]):
                    try:
                        attrs = {
                            "type": inp.get_attribute("type"),
                            "name": inp.get_attribute("name"),
                            "id": inp.get_attribute("id"),
                            "placeholder": inp.get_attribute("placeholder"),
                        }
                        print("  [{}] {}".format(i, attrs), flush=True)
                    except:
                        pass
                
                # Step 3: Enter email
                print("Step 3: Entering email...", flush=True)
                email_field = page.locator("input[type='email']").first
                if email_field.count() == 0:
                    # Try other selectors
                    email_field = page.locator("#signInName, input[name='signInName'], #email, input[name='logonIdentifier']").first
                
                if email_field.count() > 0:
                    email_field.fill(USER)
                    print("Email filled", flush=True)
                    time.sleep(1)
                    
                    # Look for Next button
                    for btn_text in ["Next", "Siguiente", "Continue"]:
                        btn = page.locator("button:has-text('{}')".format(btn_text)).first
                        if btn.count() > 0 and btn.is_visible():
                            print("Clicking '{}'".format(btn_text), flush=True)
                            btn.click()
                            time.sleep(5)
                            break
                    else:
                        # Try pressing Enter
                        email_field.press("Enter")
                        time.sleep(5)
                    
                    page.screenshot(path="/root/comc-data/after-email.png")
                    print("URL after email:", page.url[:150], flush=True)
                    print("Title:", page.title()[:100], flush=True)
                    
                    # Step 4: Enter password
                    pw_field = page.locator("input[type='password']").first
                    if pw_field.count() > 0 and pw_field.is_visible():
                        print("Password field found, entering...", flush=True)
                        pw_field.fill(PASS)
                        time.sleep(1)
                        
                        # Click Sign In
                        for btn_text in ["Sign in", "Iniciar sesion", "Sign In"]:
                            btn = page.locator("button:has-text('{}')".format(btn_text)).first
                            if btn.count() > 0 and btn.is_visible():
                                print("Clicking '{}'".format(btn_text), flush=True)
                                btn.click()
                                time.sleep(8)
                                break
                        else:
                            pw_field.press("Enter")
                            time.sleep(8)
                        
                        page.screenshot(path="/root/comc-data/after-password.png")
                        print("URL after password:", page.url[:150], flush=True)
                    else:
                        # Check for error message
                        errors = page.locator("[role='alert'], .error, #error, .alert-danger").all()
                        for err in errors:
                            try:
                                print("ERROR MSG:", err.inner_text()[:200], flush=True)
                            except:
                                pass
                else:
                    print("Email field not found!", flush=True)
                    # Dump visible text
                    body_text = page.locator("body").inner_text()
                    print("BODY TEXT:", body_text[:1000], flush=True)
            else:
                print("NOT on Azure B2C - checking page content", flush=True)
                body_text = page.locator("body").inner_text()[:1000]
                print("BODY:", body_text, flush=True)
            
            # Wait for redirect back to COMC
            print("Step 5: Waiting for redirect back to COMC...", flush=True)
            for i in range(30):
                if "comc.com" in page.url and "b2clogin" not in page.url and "microsoftonline" not in page.url:
                    print("Back on COMC!", flush=True)
                    break
                time.sleep(2)
                print("  waiting... URL:", page.url[:80], flush=True)
        
        # Step 6: Go to card page
        print("\nStep 6: Loading card page...", flush=True)
        page.goto("https://www.comc.com/Cards/Basketball/2025-26/Topps_Chrome_-_Base/2521/Dylan_Harper/31038639",
                  timeout=60000, wait_until="domcontentloaded")
        time.sleep(3)
        
        content = page.content()
        logged_in = bool(re.search(r'Sign\s*Out|Log\s*Out', content, re.I))
        print("Logged in on card page:", logged_in, flush=True)
        
        # Check for sales data
        has_view_chart = "View Chart" in content
        has_sales_link = "4 year sales" in content
        print("Has 'View Chart':", has_view_chart, flush=True)
        print("Has '4 year sales':", has_sales_link, flush=True)
        
        # Step 7: Click the sales history link
        if has_sales_link and logged_in:
            print("Step 7: Clicking 4-year sales link...", flush=True)
            sales_link = page.locator("a:has-text('4 year sales')").first
            if sales_link.count() > 0:
                sales_link.click()
                time.sleep(3)
                page.screenshot(path="/root/comc-data/sales-popup.png")
                print("Popup screenshot saved", flush=True)
                
                # Try to extract data from popup
                popup_content = page.content()
                # Look for table rows with sales data
                sales_rows = page.locator("table tbody tr, .sales-table tr, [class*='sale'] table tr").all()
                if sales_rows:
                    print("Found {} potential sales rows".format(len(sales_rows)), flush=True)
                    for row in sales_rows[:5]:
                        try:
                            print("  Row:", row.inner_text()[:200], flush=True)
                        except:
                            pass
        
        # Step 8: Try AJAX call via page.evaluate
        print("\nStep 8: Trying AJAX call from within browser context...", flush=True)
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
                    return {error: e.message};
                }
            }
        """)
        print("AJAX result:", json.dumps(result, indent=2)[:3000], flush=True)
        
        # Step 9: Save cookies for future use
        cookies = ctx.cookies()
        with open("/root/comc-data/auth-cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)
        print("\nSaved {} cookies to /root/comc-data/auth-cookies.json".format(len(cookies)), flush=True)
        for c in cookies:
            if c.get("name") in ("AuthCookie", ".ASPXAUTH", "__AntiXsrfToken", "ASP.NET_SessionId"):
                print("  {}: {}...".format(c.get("name"), str(c.get("value", ""))[:60]), flush=True)
        
        ctx.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
