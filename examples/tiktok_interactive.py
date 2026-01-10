"""
Interactive TikTok Upload - Manual mode with prompts and hashtag selection.
Use this when the full automation doesn't complete properly.
"""
import os
import time
from radar.browser import BrowserManager
from radar.tiktok import TikTokAutomator
from radar.content import ContentManager

def select_hashtags(mgr: ContentManager) -> str:
    """Interactive hashtag selection menu."""
    print("\n📌 Hashtag Selection:")
    print("-" * 40)
    
    # List available presets with indices
    keys = list(mgr.presets.keys())
    for i, key in enumerate(keys, 1):
        name, tags = mgr.presets[key]
        preview = (tags[:40] + "...") if tags else ""
        print(f"  [{i}] {name} ({key}): {preview}")
        
    print("-" * 40)
    
    choice = input("Choose hashtag preset (e.g. '1', 'tech', or '1,3'): ").strip()
    
    if not choice or choice == "0":
        return ""
    
    # Handle custom input alongside presets
    selected_tags = []
    choices = choice.split(",")
    
    # Filter out "custom" or non-preset entries for the manager
    preset_keys = []
    
    for c in choices:
        c = c.strip()
        # If it's a known key or digit, add to presets to fetch
        if c in mgr.presets or c.isdigit():
            preset_keys.append(c)
        else:
            # Assume it's a direct custom tag if it starts with #, else ignore or treat as custom key?
            # For simplicity in this interactive script, let's keep the "8=Custom" logic 
            # by checking if the user typed "custom" or if we want to support raw input.
            # The original script had a specific "8" for custom.
            pass
            
    # Get tags from manager
    generated_tags = mgr.get_hashtags(preset_keys)
    if generated_tags:
        selected_tags.append(generated_tags)

    # Simple custom addition for now
    if "custom" in choice.lower(): 
        custom = input("Enter your custom hashtags: ").strip()
        if custom:
            selected_tags.append(custom)
    
    return " ".join(selected_tags)


def main():
    content_mgr = ContentManager()
    user_data_dir = os.path.join(os.getcwd(), "tiktok_session")
    video_path = os.path.join(os.getcwd(), "test_video.mp4")
    
    if not os.path.exists(video_path):
        print(f"Error: {video_path} does not exist.")
        return

    print("=== Interactive TikTok Upload ===")
    
    with BrowserManager() as manager:
        automator = TikTokAutomator(manager, user_data_dir=user_data_dir)
        automator.max_retries = 1  # Reduce retries for interactive mode
        
        print("\n1. Opening browser...")
        automator.login(headless=False)
        
        input("\n>>> Press ENTER when you're logged in and ready to upload...")
        
        print("\n2. Navigating to TikTok Studio upload page...")
        automator.page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded")
        
        input("\n>>> Press ENTER once the upload page is loaded...")
        
        print("\n3. Setting video file...")
        try:
            file_input = automator.page.wait_for_selector('input[type="file"]', state="attached", timeout=10000)
            automator.page.set_input_files('input[type="file"]', video_path)
            print("   ✓ Video file set!")
        except Exception as e:
            print(f"   ✗ Could not set file: {e}")
            print("   >>> Please select the file manually in the browser")
        
        input("\n>>> Press ENTER once the video is uploaded and processing is complete...")
        
        # Hashtag Selection
        hashtags = select_hashtags(content_mgr)
        
        # Caption Input
        user_caption = input("\n✏️ Enter your caption (or press ENTER for default): ").strip()
        if not user_caption:
            user_caption = "Check this out!"
        
        # Combine caption + hashtags
        if hashtags:
            full_caption = f"{user_caption} {hashtags}"
        else:
            full_caption = user_caption
        
        print(f"\n4. Entering caption: {full_caption[:50]}...")
        try:
            caption_area = automator.page.query_selector('div[contenteditable="true"]') or \
                           automator.page.query_selector('textarea')
            if caption_area:
                caption_area.click()
                automator.page.keyboard.press("Control+A")
                automator.page.keyboard.press("Backspace")
                automator.page.keyboard.type(full_caption)
                print("   ✓ Caption + Hashtags entered!")
            else:
                print("   >>> Please enter caption manually")
        except Exception as e:
            print(f"   ✗ Could not enter caption: {e}")
        
        input("\n>>> Press ENTER to click the POST button (or do it manually)...")
        
        print("\n5. Clicking Post...")
        try:
            # First: Click the main POST button (red button at bottom)
            main_post_selectors = [
                'button[class*="TUXButton--primary"]',
                'button[class*="primary"]:has-text("Post")',
                'button:has-text("Post")',
                'div[class*="footer"] button',
            ]
            for sel in main_post_selectors:
                try:
                    if automator.page.is_visible(sel):
                        print(f"   Clicking: {sel}")
                        automator.page.click(sel, force=True)
                        break
                except:
                    continue
            
            # Wait for confirmation dialog
            automator.page.wait_for_timeout(1500)
            
            # Second: Handle "Continue to post?" confirmation dialog
            confirm_selectors = [
                'button:has-text("TikTok.com")',  # Red button in dialog
                'button:has-text("Continue")',
                'button[class*="confirm"]',
                'div[class*="modal"] button[class*="primary"]',
                'div[class*="dialog"] button[class*="primary"]',
            ]
            for sel in confirm_selectors:
                try:
                    if automator.page.is_visible(sel):
                        print(f"   Clicking confirm: {sel}")
                        automator.page.click(sel, force=True)
                        print("   ✓ Confirmation clicked!")
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"   ✗ Click failed: {e}")
            print("   >>> Please click Post/Continue manually")
        
        print("\n=== Upload flow complete! ===")
        input(">>> Press ENTER to close the browser...")

if __name__ == "__main__":
    main()
