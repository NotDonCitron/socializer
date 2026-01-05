"""
TikTok Login PoC using SeleniumBase UC Mode.
Usage: python examples/tiktok_sb_login.py
"""
from seleniumbase import SB
import time

def verify_login():
    with SB(uc=True, test=True, headless=True) as sb:
        print("🚀 Launching SeleniumBase in UC Mode...")
        
        # 1. Navigate to Login
        url = "https://www.tiktok.com/login"
        sb.uc_open_with_reconnect(url, 4)
        print(f"🌍 Navigated to {sb.get_current_url()}")
        
        # 2. Check for Title/Captcha
        title = sb.get_title()
        print(f"📄 Page Title: {title}")
        
        if "captcha" in title.lower() or "verify" in title.lower():
            print("⚠️ CAPTCHA detected!")
            # UC Mode might handle simple challenges, but interactive is best for login
            sb.uc_gui_click_captcha()
        
        # 3. Check for specific elements
        if sb.is_element_visible('input[name="username"]'):
            print("✅ Login form visible!")
        else:
            print("❌ Login form not found immediately.")
            
        # 4. Save Screenshot
        sb.save_screenshot("tiktok_sb_login.png")
        print("📸 Screenshot saved to tiktok_sb_login.png")

if __name__ == "__main__":
    verify_login()
