"""
Automated TikTok Upload with Content Manager.
Usage: python examples/tiktok_auto.py --video path/to/video.mp4 --caption "My Video" --tags viral,tech
"""
import os
import time
import argparse
from radar.browser import BrowserManager
from radar.tiktok import TikTokAutomator
from radar.content import ContentManager

def main():
    parser = argparse.ArgumentParser(description="TikTok Auto Uploader")
    parser.add_argument("--video", default="test_video.mp4", help="Path to video file")
    parser.add_argument("--caption", default="Automated Upload", help="Base caption")
    parser.add_argument("--tags", default="viral", help="Comma-separated tag categories (e.g. 'viral,tech')")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    
    args = parser.parse_args()
    
    # 1. Prepare Content
    content_mgr = ContentManager()
    categories = [t.strip() for t in args.tags.split(",") if t.strip()]
    
    full_caption = content_mgr.prepare_caption(args.caption, categories)
    print(f"📝 Prepared Caption: {full_caption}")
    
    # 2. Setup Paths
    user_data_dir = os.path.join(os.getcwd(), "tiktok_session")
    video_path = os.path.abspath(args.video)
    
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found at {video_path}")
        return

    # 3. Automated Upload
    print("🚀 Starting Automated Upload...")
    with BrowserManager() as manager:
        automator = TikTokAutomator(manager, user_data_dir=user_data_dir)
        
        # Login/Session Check
        if not automator.login(headless=args.headless):
            print("⚠️ Session might be invalid, but attempting upload anyway...")
        
        # Upload
        success = automator.upload_video(
            file_path=video_path,
            caption=full_caption,
            retry=True
        )
        
        if success:
            print("✅ Upload Success!")
        else:
            print(f"❌ Upload Failed: {automator.last_error}")

if __name__ == "__main__":
    main()
