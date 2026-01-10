import os
import sys
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator
from radar.session_manager import validate_instagram_session

def verify_session():
    """
    Verifies the Instagram session without performing any actions that might trigger flags.
    """
    user_data_dir = os.path.abspath("ig_session_data")
    print(f"🕵️  Verifying Session...")
    print(f"📂 User Data Dir: {user_data_dir}")

    try:
        with BrowserManager() as manager:
            automator = InstagramAutomator(manager, user_data_dir=user_data_dir)
            
            # 1. Launch & Check Basic Login State
            # We use headless=True for verification to be non-intrusive
            print("🚀 Launching Browser (Headless)...")
            is_logged_in = automator.login("", "", headless=True)
            
            # 2. Strict Validation
            if automator.page:
                status = validate_instagram_session(automator.page)
                print(f"🔍 INSPECTOR: {status}")
                
                if status['valid']:
                    print("✅ Session is ACTIVE and VALID.")
                    sys.exit(0)
                else:
                    print("⚠️  Session appears BROKEN or EXPIRED.")
                    sys.exit(1)
            else:
                print("❌ Could not inspect page (navigation failed completely).")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Verification Failed with Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_session()
