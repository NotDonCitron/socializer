"""
Automated TikTok Upload with SMART Content Generation (Phase 2).
Usage: python examples/tiktok_smart_auto.py --video path/to/video.mp4 --vibe funny --engine sb
"""
import os
import asyncio
import argparse
from dotenv import load_dotenv
from radar.browser import BrowserManager
from radar.tiktok import TikTokAutomator
from radar.content import ContentManager

# Load env vars
load_dotenv()

async def get_smart_content(video, context, vibe, force_mock):
    llm = None
    if not force_mock:
        try:
            from radar.llm.gemini import GeminiLLM
            llm = GeminiLLM()
            print("✨ Using Gemini AI for generation")
        except Exception as e:
            print(f"⚠️ Gemini not available ({e}), falling back to Mock")
            
    if not llm:
        from radar.llm.mock import MockLLM
        llm = MockLLM()
        
    content_mgr = ContentManager(llm=llm)
    print(f"🤖 Generating smart caption for {video}...")
    return await content_mgr.generate_smart_caption(video, context=context, vibe=vibe)

def main():
    parser = argparse.ArgumentParser(description="TikTok Smart Uploader")
    parser.add_argument("--video", default="test_video.mp4", help="Path to video file")
    parser.add_argument("--vibe", default="funny", help="Tone of the caption (funny, tech, gaming)")
    parser.add_argument("--context", default="", help="Additional context for AI")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--mock", action="store_true", help="Force use of mock AI")
    parser.add_argument("--engine", default="playwright", choices=["playwright", "sb"], help="Automation engine: 'playwright' (fast) or 'sb' (stable)")
    
    args = parser.parse_args()
    
    # 1. Prepare Smart Content (Async part)
    smart_content = asyncio.run(get_smart_content(args.video, args.context, args.vibe, args.mock))
    
    full_caption = f"{smart_content['caption']} {smart_content['hashtags']}"
    print(f"✨ AI Result: {full_caption}")
    
    # 2. Setup Paths
    user_data_dir = os.path.join(os.getcwd(), "tiktok_session")
    video_path = os.path.abspath(args.video)
    
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found at {video_path}")
        return

    # 3. Automated Upload
    print(f"🚀 Starting Automated Upload (Engine: {args.engine})...")
    
    if args.engine == "sb":
        # Pure SeleniumBase (Stable)
        try:
            from radar.tiktok_sb import TikTokSBAutomator
            automator = TikTokSBAutomator(user_data_dir=user_data_dir)
            success = automator.upload_video(file_path=video_path, caption=full_caption, headless=args.headless)
            if success:
                print("✅ Smart Upload Success (SB)!")
            else:
                print(f"❌ Upload Failed: {automator.last_error}")
        except ImportError as e:
            print(f"❌ Failed to load SeleniumBase engine: {e}")
            
    else:
        # Playwright (Fast)
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
                print("✅ Smart Upload Success!")
            else:
                print(f"❌ Upload Failed: {automator.last_error}")

if __name__ == "__main__":
    main()
