import os
import sys

# Enable debug screenshots
os.environ["DEBUG"] = "1"

from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator
from radar.ig_config import IG_SESSION_DIR, get_ig_username, get_ig_password

def test_upload():
    video_path = os.path.abspath("test_video.mp4")
    caption = "Test upload for Next button fix #testing"
    
    print(f"Video path: {video_path}")
    if not os.path.exists(video_path):
        print("Error: test_video.mp4 not found")
        return

    print(f"Loading session from {IG_SESSION_DIR}...")
    
    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=IG_SESSION_DIR)
        
        print("Attempting login...")
        if not automator.login(get_ig_username(), get_ig_password(), headless=True):
            print(f"❌ Login failed: {automator.last_error}")
            return
        
        print("✅ Logged in successfully")
        print(f"📤 Uploading video: {video_path}")
        
        success = automator.upload_video(
            file_path=video_path,
            caption=caption
        )
        
        if success:
            print("✅ Upload completed successfully!")
        else:
            print(f"❌ Upload failed: {automator.last_error}")

if __name__ == "__main__":
    test_upload()
