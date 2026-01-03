import os
import time
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator

def main():
    username = os.environ.get("IG_USER")
    password = os.environ.get("IG_PASS")
    user_data_dir = os.path.join(os.getcwd(), "ig_session")
    
    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=user_data_dir)
        # Headful to see it
        automator.login(username, password, headless=False)
        
        print("Logged in. Waiting for DOM to settle...")
        automator.page.wait_for_timeout(5000)
        
        # Analyze potential upload buttons
        print("\n--- Analyzing Buttons/SVGs ---")
        svgs = automator.page.query_selector_all("svg")
        for i, svg in enumerate(svgs):
            label = svg.get_attribute("aria-label")
            if label:
                print(f"SVG {i}: aria-label='{label}'")
                
        # Also check for inputs of type file, sometimes they are hidden
        file_inputs = automator.page.query_selector_all("input[type='file']")
        print(f"\nFound {len(file_inputs)} file inputs.")
        
        print("\nScript finished.")
        # Keep open briefly
        time.sleep(5)

if __name__ == "__main__":
    main()

