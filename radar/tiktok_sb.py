"""
TikTok Automation using ONLY SeleniumBase (UC Mode) for maximum stability.
Slower than Playwright, but much harder to detect.
"""
import os
import time
from seleniumbase import SB

class TikTokSBAutomator:
    def __init__(self, user_data_dir: str = "tiktok_session"):
        self.user_data_dir = user_data_dir
        self.last_error = None

    def upload_video(self, file_path: str, caption: str, headless: bool = False):
        """
        Uploads video using pure SeleniumBase.
        """
        if not os.path.exists(file_path):
            self.last_error = f"File not found: {file_path}"
            return False

        print(f"🐢 Starting Stable Upload (SeleniumBase) for {os.path.basename(file_path)}...")
        
        with SB(uc=True, test=True, headless=headless, user_data_dir=self.user_data_dir) as sb:
            try:
                # 1. Goto Upload Page
                print("🌍 Navigating to upload page...")
                sb.uc_open_with_reconnect("https://www.tiktok.com/upload", 5)
                
                # Check if we got redirected to login
                if "login" in sb.get_current_url():
                    self.last_error = "Not logged in! Run 'python -m radar.auth_bridge' first."
                    print(f"❌ {self.last_error}")
                    return False

                # 2. Handle File Input
                # TikTok's file input is hidden, we need to unhide it or use special SB methods
                print("📂 Uploading file...")
                
                # Wait for the iframe or main content
                sb.wait_for_element_present('input[type="file"]', timeout=15)
                sb.choose_file('input[type="file"]', file_path)
                
                # 3. Wait for Upload & Caption Box
                print("⏳ Waiting for upload to process...")
                # The caption box usually appears after upload starts
                sb.wait_for_element_visible('div[contenteditable="true"]', timeout=60)
                
                # 4. Set Caption
                print("✍️  Writing caption...")
                # Click to focus
                sb.uc_click('div[contenteditable="true"]')
                # Clear existing (Ctrl+A, Del) if needed, usually empty on new upload
                sb.type('div[contenteditable="true"]', caption)
                
                # 5. Wait for "Post" button to be clickable
                # TikTok disables the button while processing
                print("👀 Waiting for 'Post' button...")
                post_btn_selector = 'button:contains("Post")'
                
                # Custom wait loop for button enablement
                for _ in range(20):
                    if sb.is_element_visible(post_btn_selector) and sb.is_element_enabled(post_btn_selector):
                        break
                    time.sleep(2)
                    print(".", end="", flush=True)
                print()

                # 6. Click Post
                print("🚀 Clicking Post!")
                sb.uc_click(post_btn_selector)
                
                # 7. Verification
                print("🔎 Verifying...")
                sb.wait_for_element_visible('div:contains("uploaded")', timeout=30)
                print("✅ Upload Success!")
                return True

            except Exception as e:
                self.last_error = f"SB Error: {e}"
                print(f"❌ {self.last_error}")
                filename = f"error_sb_{int(time.time())}.png"
                sb.save_screenshot(filename)
                print(f"📸 Saved debug screenshot: {filename}")
                return False
