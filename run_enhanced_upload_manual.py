#!/usr/bin/env python3
from radar.instagram_enhanced import EnhancedInstagramAutomator
from radar.browser import BrowserManager
import os
import sys
import time

os.environ["DEBUG"] = "1"


def main():
    with BrowserManager() as manager:
        # Initialize automator
        automator = EnhancedInstagramAutomator(manager, "ig_session")

        # Initialize context and page
        print("Initializing browser context...")
        automator.context = manager.launch_persistent_context(
            "ig_session",
            headless=False,  # Keep visible for manual login
            viewport={"width": 1280, "height": 800},
        )
        automator.context.on("page", automator._handle_new_page)

        automator.page = manager.new_page(automator.context, stealth=True)

        # Navigate to Instagram
        print("Navigating to Instagram...")
        automator.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        automator.page.wait_for_timeout(5000)

        # Take a screenshot to see the current state
        automator._debug_log("Current state", screenshot=True)

        # Check if logged in
        if "login" in automator.page.url or "login" in automator.page.content().lower():
            print("⚠️  Not logged in. Please log in manually in the browser window.")
            print("Waiting for you to log in...")
            print("Press ENTER when you're logged in and ready to upload...")
            input()

            # Refresh to check login status
            automator.page.reload()
            automator.page.wait_for_timeout(3000)

        # Verify we're logged in now
        if "login" in automator.page.url:
            print("❌ Still appears to be on login page. Please try again.")
            print("Keeping browser open for 60 seconds for manual inspection...")
            time.sleep(60)
            return False

        print("✅ Appears to be logged in. Starting upload...")

        # Run the upload
        success = automator.robust_upload_video("test_video.mp4", "Test caption")
        print(f"Upload result: {success}")

        # Keep browser open for a bit to see the result
        if success:
            print("✅ Upload successful! Keeping browser open for 30 seconds...")
            time.sleep(30)
        else:
            print("❌ Upload failed. Keeping browser open for 60 seconds...")
            time.sleep(60)

        return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
