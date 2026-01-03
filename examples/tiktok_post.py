import os
import time
from radar.browser import BrowserManager
from radar.tiktok import TikTokAutomator

def main():
    # Persistent session directory (must match the one used in check/login)
    user_data_dir = os.path.join(os.getcwd(), "tiktok_session")
    
    # Path to a video file you want to upload
    video_path = os.path.join(os.getcwd(), "test_video.mp4")
    
    if not os.path.exists(video_path):
        print(f"Error: {video_path} does not exist. Please put a 'test_video.mp4' in the current directory.")
        return

    print("Starting TikTok Upload...")
    
    with BrowserManager() as manager:
        automator = TikTokAutomator(manager, user_data_dir=user_data_dir)
        
        # 1. Login (relies on saved session from tiktok_check.py)
        # We run headless=False so we can see if it works or if a wild Captcha appears
        print("Checking session...")
        if automator.login(headless=False):
            print("Session looks valid (or we are already on the page).")
        else:
            print("Warning: Login method returned False. You might need to log in manually.")
            # We continue anyway to try the upload flow
            
        time.sleep(3)
        
        # 2. Upload
        print(f"Attempting to upload {video_path}...")
        if automator.upload_video(video_path, caption="Automated test upload #robot #test"):
            print("SUCCESS: Video upload initiated!")
        else:
            print(f"UPLOAD FAILED: {automator.last_error}")
            
        # Keep open briefly to see result
        time.sleep(10)

if __name__ == "__main__":
    main()
