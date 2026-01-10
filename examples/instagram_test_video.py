import os
import sys
import time
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator

def main():
    # Set DEBUG=1 to see screenshots
    os.environ["DEBUG"] = "1"
    
    # video_path = os.path.join(os.getcwd(), "test_video.mp4")
    video_path = os.path.join(os.getcwd(), "test_image.jpg") # DEBUG: Try image first
    user_data_dir = os.path.abspath("ig_session")
    
    if not os.path.exists(video_path):
        print(f"Error: {video_path} not found.")
        return

    print(f"Starting Instagram Video Upload Test...")
    print(f"Video: {video_path}")
    
    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=user_data_dir)
        
        # 1. Login (using existing session)
        if not automator.login(username="", password="", headless=True):
            print(f"Login failed: {automator.last_error}")
            return
            
        print("Logged in. Starting upload process...")
        
        # 2. Upload Video
        success = automator.upload_video(
            file_path=video_path,
            caption="Test video upload via automated script. #automation #playwright"
        )
        
        if success:
            print("SUCCESS: Video uploaded to Instagram!")
        else:
            print(f"UPLOAD FAILED: {automator.last_error}")
            
        # Keep alive a bit for debugging if needed
        time.sleep(5)

if __name__ == "__main__":
    main()
