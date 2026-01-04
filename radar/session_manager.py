import json
import os
from pathlib import Path
from playwright.sync_api import BrowserContext, Page
from radar.selectors import SelectorStrategy

COOKIES_PATH = "tiktok_session/cookies.json"

def load_playwright_cookies(context: BrowserContext, path: str = COOKIES_PATH):
    """Loads cookies from a JSON file into a Playwright context."""
    if Path(path).exists():
        try:
            with open(path, "r") as f:
                cookies = json.load(f)
                
            # Playwright expects 'sameSite' to be 'Strict', 'Lax', or 'None'
            # Selenium might export it as a boolean or lowercase string.
            cleaned_cookies = []
            for cookie in cookies:
                if "sameSite" in cookie:
                    if cookie["sameSite"] not in ["Strict", "Lax", "None"]:
                        # Map or remove invalid sameSite values
                        del cookie["sameSite"]
                cleaned_cookies.append(cookie)
                
            context.add_cookies(cleaned_cookies)
            print(f"🍪 Loaded {len(cleaned_cookies)} cookies from {path}")
        except Exception as e:
            print(f"⚠️ Failed to load cookies: {e}")
    else:
        print(f"ℹ️ No cookies found at {path}")

def save_playwright_cookies(context: BrowserContext):
    """Saves cookies from a Playwright context to a JSON file."""
    os.makedirs(os.path.dirname(COOKIES_PATH), exist_ok=True)
    cookies = context.cookies()
    with open(COOKIES_PATH, "w") as f:
        json.dump(cookies, f, indent=2)
    print(f"💾 Cookies saved to {COOKIES_PATH}")

def validate_tiktok_session(page: Page) -> dict:
    """
    Validates if the current Playwright page session appears logged into TikTok.
    """
    selector = SelectorStrategy(page)
    
    # 1. Check for elements visible to logged-in users
    profile_icon = selector.find_any_visible(
        ['[data-e2e="profile-icon"]', '[aria-label*="Profile"]', '[href*="/@"]']
    )
    if profile_icon:
        return {'valid': True, 'reason': 'Profile icon visible'}
        
    # 2. Check if we're redirected away from login/signup pages
    if "login" not in page.url and "signup" not in page.url and "tiktok.com" in page.url:
        return {'valid': True, 'reason': 'Navigated away from login page'}
        
    # 3. Fallback: If we are on a page that requires login, it's likely not logged in
    if "login" in page.url or "signup" in page.url:
        return {'valid': False, 'reason': 'Still on login/signup page'}

    return {'valid': True, 'reason': 'No strong login indicators, but not on login page'}
