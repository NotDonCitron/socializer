import os
# Set DEBUG=1 check BEFORE imports
os.environ["DEBUG"] = "1"

import sys
import time
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator

def main():
    
    # content_video_path = os.path.join(os.getcwd(), "content", "test_video.mp4")
    # root_video_path = os.path.join(os.getcwd(), "test_video.mp4")
    # video_path = content_video_path if os.path.exists(content_video_path) else root_video_path
    
    # DEBUG: Try image
    content_dir = os.path.join(os.getcwd(), "content")
    # root_video_path = os.path.join(os.getcwd(), "test_video.mp4")
    # video_path = content_video_path if os.path.exists(content_video_path) else root_video_path
    
    # DEBUG: Try image
    content_dir = os.path.join(os.getcwd(), "content")
    image_files = [f for f in os.listdir(content_dir) if f.endswith(".jpg")]
    if image_files:
        video_path = os.path.join(content_dir, image_files[0])
    else:
        video_path = "test_image.jpg"
    user_data_dir = os.path.abspath("ig_session")
    
    if not os.path.exists(video_path):
        print(f"Error: {video_path} not found.")
        return

    print(f"Starting Instagram Video Upload Test...")
    print(f"Video: {video_path}")
    
    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=user_data_dir)
        
        # 1. Login (using existing session)
        if not automator.login(username="", password="", headless=False):
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
