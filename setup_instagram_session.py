"""
Manual Instagram Login - establishes session and saves cookies.

Run this ONCE to log in manually and save your session.
After this, automated uploads will work.
"""
import os
import sys

# Load .env file manually (since python-dotenv might not be installed)
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()
    print(f"[INFO] Loaded environment from .env")
else:
    print("[WARNING] No .env file found")

from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator
from radar.session_manager import save_playwright_cookies
from radar.ig_config import get_ig_username, get_ig_password, IG_SESSION_DIR

def main():
    print("=" * 60)
    print("Instagram Manual Login - Session Setup")
    print("=" * 60)
    print()
    print("This will open a browser window where you can log in manually.")
    print("After logging in, press ENTER to save your session.")
    print()
    
    user_data_dir = IG_SESSION_DIR
    cookies_path = os.path.join(user_data_dir, "cookies.json")
    
    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=user_data_dir)
        
        # Try automatic login first
        print(f"Attempting automatic login for: {get_ig_username()}")
        success = automator.login(
            get_ig_username(), 
            get_ig_password(), 
            headless=False,  # Show browser
            timeout=60000
        )
        
        if success:
            print("[SUCCESS] Automatic login successful!")
        else:
            print(f"[WARNING] Automatic login failed: {automator.last_error}")
            print()
            print("Please log in manually in the browser window...")
            print("Complete any 2FA if prompted.")
        
        # Wait for user confirmation
        input("\n>>> Press ENTER after you've logged in successfully...")
        
        # Save the session
        print(f"\n[SAVE] Saving session to {cookies_path}...")
        save_playwright_cookies(automator.context, cookies_path)
        
        # Verify it worked
        current_url = automator.page.url
        if "instagram.com" in current_url and "login" not in current_url:
            print("[SUCCESS] Session saved successfully!")
            print(f"Current URL: {current_url}")
            print()
            print("You can now run automated uploads:")
            print("  python examples/instagram_test_video.py")
            print("  .\\run_ig_upload.ps1 test_video.mp4 \"Caption\"")
        else:
            print("[WARNING] Warning: You may not be logged in. Current URL:", current_url)
        
        print("\nBrowser will close in 5 seconds...")
        automator.page.wait_for_timeout(5000)

if __name__ == "__main__":
    main()
