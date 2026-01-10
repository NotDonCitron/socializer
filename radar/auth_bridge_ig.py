"""
Bridge between SeleniumBase (for stealth login) and Playwright (for automation) - Instagram Version.
"""
import os
import json
import time
from seleniumbase import SB
from radar.session_manager import get_session_path

# Use standardized path: ig_session/cookies.json
COOKIES_PATH = get_session_path("ig", "cookies.json")

def sb_login(username: str = None, password: str = None, headless: bool = True, timeout: int = 60):
    """
    Launches SeleniumBase in UC Mode for automated stealth login.
    Dumps cookies for Playwright.
    """
    if not username or not password:
        from dotenv import load_dotenv
        load_dotenv()
        username = username or os.getenv("IG_USERNAME")
        password = password or os.getenv("IG_PASSWORD")

    if not username or not password:
        print("❌ Error: credentials not provided and not found in .env")
        return False

    print(f"🚀 Launching Stealth Browser for Instagram Login ({username})...")
    
    try:
        with SB(uc=True, test=True, headless=headless, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36") as sb:
            # Navigate to login
            sb.uc_open_with_reconnect("https://www.instagram.com/accounts/login/", 4)
            sb.sleep(3)

            # Ensure username field is present
            try:
                sb.wait_for_element_visible('input[name="username"]', timeout=20)
            except Exception:
                print("❌ Username field not found; retrying after refresh.")
                sb.uc_open_with_reconnect("https://www.instagram.com/accounts/login/", 4)
                sb.sleep(3)
                sb.wait_for_element_visible('input[name=\"username\"]', timeout=20)

            # Handle Cookie Banner (Enriched selectors)
            # UC mode is good at clicking these
            popups = [
                "button:contains('Allow all cookies')",
                "button:contains('Alle Cookies erlauben')",
                "button:contains('Allow Essential and Optional Cookies')",
                "button:contains('Only allow essential cookies')",
                "button:contains('Decline optional cookies')",
                "button:contains('Alles akzeptieren')",
                "button[data-cookiebanner='accept_button']",
            ]
            for selector in popups:
                if sb.is_element_visible(selector):
                    print(f"✅ Dismissing cookie wall: {selector}")
                    sb.click(selector)
                    sb.sleep(1)
                    break

            # Fill Login
            print("📝 Filling credentials...")
            sb.type('input[name="username"]', username)
            sb.type('input[name="password"]', password)
            sb.sleep(1)
            
            print("👆 Clicking login...")
            sb.click('button[type="submit"]')
            sb.sleep(5)

            # Check if login succeeded or if there's a "Save Login" popup
            if sb.is_element_visible("button:contains('Not Now')") or sb.is_element_visible("button:contains('Nicht jetzt')"):
                print("✅ Handling 'Save Login' popup...")
                sb.click("button:contains('Not Now')")
                sb.sleep(2)

            # Verification: looking for a logged-in indicator (e.g., Search icon or Profile)
            # wait_for_element_visible will wait for the element to appear
            try:
                print("⌛ Waiting for search icon as login confirmation...")
                sb.wait_for_element_visible("svg[aria-label*='Search']", timeout=15)
                login_confirmed = True
            except:
                try:
                    sb.wait_for_element_visible("svg[aria-label*='Suche']", timeout=15)
                    login_confirmed = True
                except:
                    login_confirmed = False

            if login_confirmed:
                print("🎉 Login Successful!")
                # Export cookies
                cookies = sb.driver.get_cookies()
                
                # Ensure directory exists
                abs_path = os.path.abspath(COOKIES_PATH)
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                
                with open(abs_path, "w") as f:
                    json.dump(cookies, f, indent=2)
                    
                print(f"💾 Cookies saved to {abs_path}")
                return True
            else:
                print("❌ Login confirmation failed. Check credentials or challenge.")
                # Optional: save screenshot for debugging in headless mode
                sb.save_screenshot("ig_login_failed_sb.png")
                return False
                
    except Exception as e:
        print(f"❌ SB Login Exception: {e}")
        return False

if __name__ == "__main__":
    # In interactive mode, we might want headless=False for debugging
    sb_login(headless=True)
