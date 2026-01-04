"""
Bridge between SeleniumBase (for stealth login) and Playwright (for automation).
"""
import os
import json
import time
from seleniumbase import SB

COOKIES_PATH = "tiktok_session/cookies.json"

def sb_login(headless: bool = False, timeout: int = 300):
    """
    Launches SeleniumBase in UC Mode for interactive login.
    Waits for the user to log in, then dumps cookies.
    """
    print("🚀 Launching Stealth Browser for Login...")
    print("👉 Please log in to TikTok manually in the opened window.")
    
    with SB(uc=True, test=True, headless=headless) as sb:
        # Navigate to login
        sb.uc_open_with_reconnect("https://www.tiktok.com/login", 4)
        
        print("\n" + "="*50)
        print("👉 Log in to TikTok in the browser.")
        print("👉 When you are seeing your dashboard/profile...")
        input("👉 PRESS ENTER HERE IN THE TERMINAL TO SAVE COOKIES AND EXIT >> ")
        print("="*50 + "\n")

        # Export cookies
        cookies = sb.driver.get_cookies()
        
        # Ensure directory exists
        abs_path = os.path.abspath(COOKIES_PATH)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        with open(abs_path, "w") as f:
            json.dump(cookies, f, indent=2)
            
        print(f"💾 Cookies saved to {abs_path}")
        return True

if __name__ == "__main__":
    sb_login(headless=False)
