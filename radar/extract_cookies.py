"""
Extracts cookies from an existing Chrome profile in 'tiktok_session'.
"""
import os
import json
import time
from seleniumbase import SB

USER_DATA_DIR = "tiktok_session"
COOKIES_PATH = os.path.join(USER_DATA_DIR, "cookies.json")

def extract():
    print(f"🕵️‍♂️ Inspecting session in '{USER_DATA_DIR}'...")
    
    # Launch headless first to check
    with SB(uc=True, test=True, headless=True, user_data_dir=USER_DATA_DIR) as sb:
        print("🌍 Navigating to TikTok...")
        sb.uc_open_with_reconnect("https://www.tiktok.com/upload", 5)
        
        # Check login status
        if "login" not in sb.get_current_url() and not sb.is_element_visible('a[href*="login"]'):
            print("✅ Session appears LOGGED IN!")
            
            # Extract cookies
            cookies = sb.driver.get_cookies()
            with open(COOKIES_PATH, "w") as f:
                json.dump(cookies, f, indent=2)
            print(f"🍪 Extracted {len(cookies)} cookies to {COOKIES_PATH}")
            return True
        else:
            print("❌ Session appears LOGGED OUT (Redirected to login or login button visible).")
            print(f"Current URL: {sb.get_current_url()}")
            return False

if __name__ == "__main__":
    extract()
