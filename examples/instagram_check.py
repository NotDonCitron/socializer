import os
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator

def main():
    # Credentials from environment or use dummy for demonstration
    username = os.environ.get("IG_USER", "your_username")
    password = os.environ.get("IG_PASS", "your_password")
    
    # Persistent session directory
    user_data_dir = os.path.join(os.getcwd(), "ig_session")
    
    print(f"Starting Instagram Check for user: {username}")
    
    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=user_data_dir)
        
        # We run headful (headless=False) so the user can see what's happening
        # and solve 2FA/Captchas if it's the first time.
        success = automator.login(username, password, headless=False)
        
        if success:
            print("Successfully logged in or already had a session!")
            print(f"Current URL: {automator.page.url}")
            
            # Simple check: are we on the home feed?
            if "instagram.com" in automator.page.url and "login" not in automator.page.url:
                print("Confirmed: On Instagram Home/Feed.")
                
                # Take a screenshot for verification
                screenshot_path = "ig_home_check.png"
                automator.page.screenshot(path=screenshot_path)
                print(f"Screenshot saved to {screenshot_path}")
            else:
                print("Login successful but not on expected page.")
        else:
            print(f"Login failed! Error: {automator.last_error}")
            
        print("\nScript finished. Browser will close now (due to Context Manager).")

if __name__ == "__main__":
    main()

