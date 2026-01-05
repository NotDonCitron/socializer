#!/usr/bin/env python3
from radar.instagram_enhanced import EnhancedInstagramAutomator
from radar.browser import BrowserManager
import os
import sys

os.environ["DEBUG"] = "1"


def main():
    with BrowserManager() as manager:
        # Initialize automator
        automator = EnhancedInstagramAutomator(manager, "ig_session")

        # Initialize context and page
        print("Initializing browser context...")
        automator.context = manager.launch_persistent_context(
            "ig_session", headless=False, viewport={"width": 1280, "height": 800}
        )
        automator.context.on("page", automator._handle_new_page)

        automator.page = manager.new_page(automator.context, stealth=True)

        # Check if logged in
        print("Checking login status...")
        automator.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        automator.page.wait_for_timeout(3000)

        if "login" in automator.page.url:
            print("⚠️  Not logged in. Please log in manually in the browser.")
            print("Press ENTER when logged in and on Instagram home...")
            input()

        # Run the upload
        print("Starting upload...")
        success = automator.robust_upload_video("test_video.mp4", "Test caption")
        print(f"Upload result: {success}")

        return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
