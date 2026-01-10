import os
import time
from radar.browser import BrowserManager
from radar.tiktok import TikTokAutomator

def main():
    # Persistent session directory for TikTok
    user_data_dir = os.path.join(os.getcwd(), "tiktok_session")
    
    print(f"Starting TikTok Check.")
    print(f"Session directory: {user_data_dir}")
    
    with BrowserManager() as manager:
        # We assume the user wants to see the browser to solve CAPTCHAs
        automator = TikTokAutomator(manager, user_data_dir=user_data_dir)
        
        # This will launch the browser and go to login
        # We pass minimal timeout to just get there, then we wait manually
        print("Launching browser... Please log in manually if needed.")
        automator.login(headless=False)
        
        print("\n--- MANUAL INTERACTION REQUIRED ---")
        print("1. If a Captcha appears, solve it.")
        print("2. Log in with your credentials (QR code or Phone/Email).")
        print("3. Wait until you are on the 'For You' feed or your Profile.")
        print("-----------------------------------")
        
        # Loop to keep script running while user logs in
        try:
            while True:
                if automator.page.is_closed():
                    break
                
                # Check if logged in (url check)
                url = automator.page.url
                if "login" not in url and ("tiktok.com/foryou" in url or "tiktok.com/@" in url):
                    print("\n[+] Detected generic logged-in URL state.")
                    # Optional: Take screenshot
                    # automator.page.screenshot(path="tiktok_login_success.png")
                    
                time.sleep(2)
        except KeyboardInterrupt:
            print("\nStopping script...")

        print("Browser closed. Session should be saved in 'tiktok_session'.")

if __name__ == "__main__":
    main()
