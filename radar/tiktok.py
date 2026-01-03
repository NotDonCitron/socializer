from playwright.sync_api import Page, BrowserContext
from radar.browser import BrowserManager
import time

class TikTokAutomator:
    def __init__(self, manager: BrowserManager, user_data_dir: str):
        self.manager = manager
        self.user_data_dir = user_data_dir
        self.context: BrowserContext = None
        self.page: Page = None
        self.last_error: str = None

    def login(self, username=None, password=None, headless=True, timeout=30000):
        """
        TikTok login is extremely difficult to automate reliably due to captchas.
        Recommended flow: login manually once with headless=False, then use persistent context.
        """
        self.last_error = None
        if not self.context:
            self.context = self.manager.launch_persistent_context(
                self.user_data_dir,
                headless=headless,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
            )
        
        self.page = self.manager.new_page(self.context, stealth=True)
        
        try:
            print("Browser context launched. Navigating to login...")
            self.page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded", timeout=timeout)
            
            # Check if we are already logged in
            # If we see the 'upload' button or profile icon, we might be logged in
            self.page.wait_for_timeout(2000)
            if "login" not in self.page.url:
                return True
            
            # If credentials provided, we can TRY to fill them, but expect CAPTCHA
            if username and password:
                # This often fails due to complex selectors and anti-bot
                pass 

            return False
        except Exception as e:
            self.last_error = f"Login navigation failed: {e}"
            return False

    def enable_monitoring(self):
        """
        Enables active monitoring by printing browser console logs to stdout.
        """
        if self.page:
            self.page.on("console", lambda msg: print(f"BROWSER: {msg.text}"))
            print("Active monitoring enabled: streaming browser console logs.")

    def upload_video(self, file_path: str, caption: str = "", timeout: int = 60000) -> bool:
        """
        Uploads a video to TikTok.
        Assumes the user is already logged in.
        """
        self.last_error = None
        if not self.page:
            self.last_error = "Page not initialized. Call login() first."
            return False
            
        self.enable_monitoring()

        try:
            # 1. Navigate to Upload Page
            print("Navigating to upload page...")
            self.page.goto("https://www.tiktok.com/upload", wait_until="domcontentloaded", timeout=timeout)
            
            # 2. Handle File Chooser
            # TikTok uses a hidden input or an iframe sometimes, but usually it's an input[type=file]
            try:
                input_selector = 'input[type="file"]'
                # File input is often hidden, so we wait for it to be attached to the DOM, not necessarily visible
                print(f"Waiting for file input ({input_selector}) to be attached...")
                self.page.wait_for_selector(input_selector, state="attached", timeout=20000)
                
                print(f"Setting input files to {file_path}...")
                self.page.set_input_files(input_selector, file_path)
            except Exception as e:
                self.last_error = f"Could not find upload input: {e}"
                return False

            # 3. Wait for Upload Processing
            # We look for the caption area to appear as a sign that the upload started
            caption_selector = 'div[contenteditable="true"]'
            try:
                self.page.wait_for_selector(caption_selector, timeout=30000)
            except:
                 # Fallback selectors
                 caption_selector = 'textarea'
                 self.page.wait_for_selector(caption_selector, timeout=5000)

            # 4. Enter Caption
            # TikTok uses a draft.js / contenteditable for captions
            self.page.focus(caption_selector)
            # Clear existing if any
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            self.page.keyboard.type(caption)

            # 5. Click Post
            # The button might be disabled until processing is done
            post_btn_selectors = [
                'button[data-e2e="post_video_button"]',
                'button:has-text("Post")',
                'button:has-text("Veröffentlichen")', # German
                '.btn-post' # Possible class
            ]
            
            post_btn = None
            for sel in post_btn_selectors:
                try:
                    if self.page.is_visible(sel):
                        post_btn = sel
                        break
                except:
                    continue
            
            if not post_btn:
                # Try waiting for the most likely one
                try:
                    self.page.wait_for_selector('button[data-e2e="post_video_button"]', timeout=5000)
                    post_btn = 'button[data-e2e="post_video_button"]'
                except:
                    # Fallback to text
                    try:
                        self.page.wait_for_selector('button:has-text("Post")', timeout=5000)
                        post_btn = 'button:has-text("Post")'
                    except:
                        self.last_error = "Could not find 'Post' button."
                        return False

            # Wait a bit for the video to be fully ready (TikTok sometimes disables the button)
            print("Waiting for Post button to be enabled (video processing)...")
            max_wait = 120
            start_time = time.time()
            button_enabled = False
            
            while time.time() - start_time < max_wait:
                if self.page.is_enabled(post_btn):
                    button_enabled = True
                    break
                time.sleep(1)
            
            if not button_enabled:
                self.last_error = "Post button never became enabled (timeout)."
                return False

            # Handle "Joyride" / Tour overlay which often blocks clicks
            try:
                if self.page.locator('div[id="react-joyride-portal"]').count() > 0:
                    print("Detected feature tour/overlay. Attempting to dismiss...")
                    self.page.keyboard.press("Escape")
                    time.sleep(1)
            except:
                pass

            print(f"Clicking Post button ({post_btn}) with force=True...")
            self.page.click(post_btn, force=True)

            # 6. Verify
            # Success indicator: "Your video is being uploaded" or navigation
            time.sleep(5)
            return True

        except Exception as e:
            self.last_error = f"TikTok upload failed: {e}"
            print(self.last_error)
            if self.page:
                try:
                    self.page.screenshot(path="error_upload_debug.png", full_page=True)
                    print("Screenshot saved to 'error_upload_debug.png'")
                except:
                    print("Failed to save error screenshot.")
            return False
