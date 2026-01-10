"""
Interactive Instagram Upload - Manual mode with prompts and hashtag selection.
"""
import os
import time
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator

# Instagram Hashtag Presets
HASHTAG_PRESETS = {
    "1": ("Viral/Explore", "#instagood #photooftheday #instagram #explore #viral"),
    "2": ("Photography", "#photography #photo #picoftheday #photographer #nature"),
    "3": ("Lifestyle", "#lifestyle #life #love #happy #beautiful"),
    "4": ("Fitness", "#fitness #gym #workout #fitnessmotivation #health"),
    "5": ("Food", "#food #foodie #foodporn #instafood #yummy"),
    "6": ("Travel", "#travel #travelgram #travelphotography #wanderlust #vacation"),
    "7": ("Fashion", "#fashion #style #ootd #fashionblogger #outfit"),
    "8": ("Tech", "#tech #technology #coding #programming #developer"),
    "9": ("Custom", None),
    "0": ("None", ""),
}


def select_hashtags() -> str:
    """Interactive hashtag selection menu."""
    print("\n📌 Hashtag Selection:")
    print("-" * 45)
    for key, (name, tags) in HASHTAG_PRESETS.items():
        if tags:
            print(f"  [{key}] {name}: {tags[:35]}...")
        else:
            print(f"  [{key}] {name}")
    print("-" * 45)
    
    choice = input("Choose hashtag preset (or multiple like '1,3'): ").strip()
    
    if not choice or choice == "0":
        return ""
    
    selected_tags = []
    for c in choice.split(","):
        c = c.strip()
        if c in HASHTAG_PRESETS:
            name, tags = HASHTAG_PRESETS[c]
            if c == "9":  # Custom
                custom = input("Enter your custom hashtags: ").strip()
                selected_tags.append(custom)
            elif tags:
                selected_tags.append(tags)
    
    return " ".join(selected_tags)


def main():
    user_data_dir = os.path.join(os.getcwd(), "ig_session")
    
    # Find image file
    image_path = os.path.join(os.getcwd(), "test_image.jpg")
    if not os.path.exists(image_path):
        # Try other formats
        for ext in [".png", ".jpeg", ".webp"]:
            alt_path = os.path.join(os.getcwd(), f"test_image{ext}")
            if os.path.exists(alt_path):
                image_path = alt_path
                break
        else:
            print("Error: No test_image found. Put test_image.jpg/png in current directory.")
            custom_path = input("Or enter full path to image: ").strip()
            if custom_path and os.path.exists(custom_path):
                image_path = custom_path
            else:
                return

    print("=== Interactive Instagram Upload ===")
    
    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=user_data_dir)
        
        print("\n1. Opening browser (mobile layout)...")
        # Don't require credentials - use saved session
        automator.context = manager.launch_persistent_context(
            user_data_dir,
            headless=False,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        )
        automator.page = manager.new_page(automator.context, stealth=True)
        
        automator.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        
        input("\n>>> Press ENTER when you're logged in and on Instagram home...")
        
        # Handle popups
        automator.handle_popups()
        
        print("\n2. Opening create flow in desktop UI...")
        automator.page.goto("https://www.instagram.com/create/select/", wait_until="domcontentloaded")
        input(">>> Press ENTER once the file picker is open...")
        
        print(f"\n3. Setting image file: {os.path.basename(image_path)}")
        try:
            # Try to set file via input
            file_input = automator.page.query_selector('input[type="file"]')
            if file_input:
                automator.page.set_input_files('input[type="file"]', image_path)
                print("   ✓ Image file set!")
            else:
                print("   >>> Please select the file manually")
        except Exception as e:
            print(f"   ✗ Could not set file: {e}")
            print("   >>> Please select the file manually")
        
        input("\n>>> Press ENTER after selecting your image and clicking through Crop/Filter...")
        
        # Hashtag Selection
        hashtags = select_hashtags()
        
        # Caption Input
        user_caption = input("\n✏️ Enter your caption (or press ENTER for default): ").strip()
        if not user_caption:
            user_caption = "Check this out! ✨"
        
        # Combine caption + hashtags
        if hashtags:
            full_caption = f"{user_caption}\n.\n.\n{hashtags}"  # IG style: dots before hashtags
        else:
            full_caption = user_caption
        
        print(f"\n4. Entering caption: {full_caption[:50]}...")
        try:
            caption_selectors = [
                'textarea[aria-label*="caption" i]',
                'textarea[aria-label*="Bildunterschrift" i]',
                'textarea',
            ]
            for sel in caption_selectors:
                try:
                    if automator.page.is_visible(sel):
                        automator.page.fill(sel, full_caption)
                        print("   ✓ Caption + Hashtags entered!")
                        break
                except:
                    continue
        except Exception as e:
            print(f"   ✗ Could not enter caption: {e}")
            print(f"   >>> Copy this: {full_caption}")
        
        input("\n>>> Press ENTER to click SHARE (or do it manually)...")
        
        print("\n5. Clicking Share...")
        share_selectors = [
            'text=Share',
            'text=Teilen',
            'button:has-text("Share")',
            'button:has-text("Teilen")',
        ]
        for sel in share_selectors:
            try:
                if automator.page.is_visible(sel):
                    automator.page.click(sel)
                    print("   ✓ Share clicked!")
                    break
            except:
                continue
        
        print("\n=== Upload flow complete! ===")
        input(">>> Press ENTER to close the browser...")


if __name__ == "__main__":
    main()
