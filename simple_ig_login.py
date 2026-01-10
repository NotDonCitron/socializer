"""
Einfacher Instagram Login - ohne Cookies.
"""
import os
import sys

# Load .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator
from radar.session_manager import save_playwright_cookies
from radar.ig_config import get_ig_username, get_ig_password, IG_SESSION_DIR

print("=" * 60)
print("Instagram Simple Login")
print("=" * 60)

username = get_ig_username()
password = get_ig_password()

if not username or not password:
    print("[ERROR] Set IG_USERNAME and IG_PASSWORD in .env")
    sys.exit(1)

print(f"Account: {username}")
print("Opening browser...")

with BrowserManager() as manager:
    automator = InstagramAutomator(manager, user_data_dir=IG_SESSION_DIR)
    
    success = automator.login(username, password, headless=False, timeout=90000)
    
    if success:
        print("[SUCCESS] Login successful!")
        
        # Save cookies
        cookies_path = os.path.join(IG_SESSION_DIR, "cookies.json")
        save_playwright_cookies(automator.context, cookies_path)
        print(f"[SUCCESS] Cookies saved to {cookies_path}")
        
        input("\nPress ENTER to close...")
    else:
        print(f"[ERROR] Login failed: {automator.last_error}")
        input("\nPress ENTER to close...")
