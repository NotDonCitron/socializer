import json
import os
from pathlib import Path
from playwright.sync_api import BrowserContext, Page
from radar.ig_selectors import SelectorStrategy

def get_session_path(platform: str, filename: str) -> str:
    """Returns the standardized path for session artifacts."""
    return os.path.join(f"{platform}_session", filename)

COOKIES_PATH = get_session_path("instagram", "cookies.json")

def load_playwright_cookies(context: BrowserContext, path: str):
    """
    Loads cookies from a JSON file into a Playwright context.
    Args:
        context: The Playwright BrowserContext.
        path: Path to the cookies JSON file.
    """
    if Path(path).exists():
        try:
            with open(path, "r") as f:
                cookies = json.load(f)
                
            # Playwright expects 'sameSite' to be 'Strict', 'Lax', or 'None'
            # Selenium might export it as a boolean or lowercase string.
            # Selenium uses 'expiry', Playwright uses 'expires'
            cleaned_cookies = []
            for cookie in cookies:
                # Rename expiry to expires
                if "expiry" in cookie and "expires" not in cookie:
                    cookie["expires"] = cookie["expiry"]
                
                if "sameSite" in cookie:
                    # SeleniumBase might set sameSite=None or False or a string.
                    # We ensure it's a valid Playwright value.
                    val = str(cookie["sameSite"]).capitalize()
                    if val not in ["Strict", "Lax", "None"]:
                        del cookie["sameSite"]
                    else:
                        cookie["sameSite"] = val
                cleaned_cookies.append(cookie)
                
            context.add_cookies(cleaned_cookies)
            print(f"Loaded {len(cleaned_cookies)} cookies from {path}")
        except Exception as e:
            print(f"Failed to load cookies: {e}")
    else:
        print(f"No cookies found at {path}")

def save_playwright_cookies(context: BrowserContext, path: str | None = None):
    """
    Saves cookies from a Playwright context to a JSON file.
    Args:
        context: The Playwright BrowserContext.
        path: Path to the cookies JSON file.
    """
    target_path = path or COOKIES_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    cookies = context.cookies()
    with open(target_path, "w") as f:
        json.dump(cookies, f, indent=2)
    print(f"Cookies saved to {target_path}")

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

def validate_instagram_session(page: Page) -> dict:
    """
    Validates if the current Playwright page session appears logged into Instagram.
    """
    selector = SelectorStrategy(page)
    
    # 1. Check for profile link/icon (sidebar)
    profile_icon = selector.find_any_visible([
        'a[href*="/generated_username/"]', # Placeholder
        'svg[aria-label="Profile"]', 
        'svg[aria-label="Profil"]',
        'img[alt*="profile picture"]',
        'a[role="link"] img[alt*="profile"]'
    ])
    
    # Instagram specific check: The 'Log in' button should NOT be there
    login_btn = selector.find_any_visible(['a[href="/accounts/login/"]', 'button:has-text("Log In")'])
    
    if profile_icon and not login_btn:
        return {'valid': True, 'reason': 'Profile icon visible'}

    if "login" in page.url:
        return {'valid': False, 'reason': 'On login page'}

    # Strong indicator of being logged out on home: "Log In" or "Sign Up" text
    if selector.find_any_visible(['text="Log In"', 'text="Sign Up"']):
        return {'valid': False, 'reason': 'Login/Signup text visible'}
        
    return {'valid': True, 'reason': 'Navigated away from login page'}
