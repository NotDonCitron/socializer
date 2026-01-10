import os
import sys
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator

def main():
    user_data_dir = os.path.join(os.getcwd(), "ig_session")
    
    print(f"Checking Instagram Session...")
    
    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=user_data_dir)
        
        # Try to navigate and see if we are logged in
        # We don't provide user/pass here, just relying on cookies
        success = automator.login(username="", password="", headless=True)
        
        if success:
            print(f"Logged in as: {automator.page.url}")
            automator.page.screenshot(path="ig_check.png")
            print("Saved screenshot to ig_check.png")
        else:
            print(f"NOT LOGGED IN: {automator.last_error}")
            automator.page.screenshot(path="ig_fail.png")

if __name__ == "__main__":
    main()
