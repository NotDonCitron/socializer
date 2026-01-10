"""
TikTok automation module with advanced anti-detection and retry logic.
"""
from playwright.sync_api import Page, BrowserContext
from radar.browser import BrowserManager
from radar.ig_selectors import SelectorStrategy, TIKTOK_SELECTORS
from radar.human_behavior import human_delay, human_type, human_click, wait_human
from radar.session_manager import validate_tiktok_session, load_playwright_cookies
import time
import os
import datetime

class TikTokAutomator:
    """
    TikTok upload automation with anti-detection measures.
    
    Features:
    - Human-like interaction patterns
    - Multi-strategy selectors with fallbacks
    - Retry logic with exponential backoff
    - Session validation and shadowban detection
    """
    
    def __init__(self, manager: BrowserManager, user_data_dir: str):
        self.manager = manager
        self.user_data_dir = user_data_dir
        self.context: BrowserContext = None
        self.page: Page = None
        self.last_error: str = None
        self.upload_attempts: int = 0
        self.max_retries: int = 3
        self.debug = os.environ.get("DEBUG", "0") == "1"

    def login(self, username=None, password=None, headless=False, timeout=30000):
        """
        Initialize browser and check login status.
        """
        self.last_error = None
        if not self.context:
            self.context = self.manager.launch_persistent_context(
                self.user_data_dir,
                headless=headless,
                randomize=True,  # Use randomized viewport/UA
            )
            # Try to load SeleniumBase cookies if available
            load_playwright_cookies(self.context)
        
        self.page = self.manager.new_page(self.context, stealth=True)
        
        try:
            print("Browser context launched. Navigating to TikTok...")
            self.page.goto("https://www.tiktok.com/upload", wait_until="domcontentloaded", timeout=timeout)
            wait_human(self.page, 'navigate')
            
            validation = validate_tiktok_session(self.page)
            if validation['valid']:
                print(f"Session valid: {validation['reason']}")
                return True
            
            print(f"Session invalid: {validation['reason']}")
            print("💡 TIP: Run 'python -m radar.auth_bridge' to log in interactively with SeleniumBase UC Mode.")
            return False
            
        except Exception as e:
            self.last_error = f"Login navigation failed: {e}"
            print(self.last_error)
            return False

    def enable_monitoring(self):
        """
        Enables active monitoring by printing browser console logs to stdout.
        """
        if self.page:
            self.page.on("console", lambda msg: print(f"BROWSER: {msg.text}"))
            print("Active monitoring enabled: streaming browser console logs.")

    def _debug_screenshot(self, step_name: str):
        """Helper to take timestamped screenshots if DEBUG is enabled."""
        if self.debug and self.page:
            ts = datetime.datetime.now().strftime("%H%M%S")
            filename = f"debug_{ts}_{step_name}.png"
            try:
                self.page.screenshot(path=filename)
                print(f"[DEBUG] Saved screenshot: {filename}")
            except Exception as e:
                print(f"[DEBUG] Failed to save screenshot: {e}")

    def _wait_for_video_ready(self, timeout: int = 180) -> bool:
        """
        Wait for video processing to complete.
        Checks multiple indicators: spinner gone, copyright check done, progress bar 100%.
        """
        selector = SelectorStrategy(self.page)
        start_time = time.time()
        
        print("Waiting for video processing...")
        self._debug_screenshot("wait_start")
        
        while time.time() - start_time < timeout:
            # 1. Check for explicit completion signals
            if selector.is_any_visible(TIKTOK_SELECTORS['processing_complete']):
                print("Processing complete signal detected!")
                self._debug_screenshot("wait_complete_signal")
                return True

            # 2. Check if loading indicators are gone
            is_loading = selector.is_any_visible(TIKTOK_SELECTORS['loading_indicator'])
            
            if not is_loading:
                # 3. Check if post button is enabled (ultimate truth)
                post_btn = selector.find(TIKTOK_SELECTORS['post_button'], timeout=1000)
                if post_btn:
                    try:
                        # Check disabled state
                        is_disabled = post_btn.is_disabled()
                        if not is_disabled:
                            print("Post button is enabled! Video ready.")
                            self._debug_screenshot("wait_complete_button")
                            return True
                    except Exception:
                        pass
            
            time.sleep(3)
            
            elapsed = int(time.time() - start_time)
            if elapsed % 15 == 0:
                print(f"  Still processing... ({elapsed}s)")
                self._debug_screenshot(f"processing_{elapsed}s")
        
        print("Timeout waiting for video processing.")
        self._debug_screenshot("wait_timeout")
        return False

    def _dismiss_overlays(self):
        """Dismiss tour overlays or popups that might block interaction."""
        selector = SelectorStrategy(self.page)
        
        # 0. Handle Cookie Banners (High Priority)
        cookie_btn = selector.find_any_visible(TIKTOK_SELECTORS['cookie_banner'])
        if cookie_btn:
            try:
                print("Found cookie banner, clicking accept/close...")
                cookie_btn.click(timeout=2000)
                wait_human(self.page, 'click')
            except Exception:
                pass

        # 1. Try common overlay selectors
        if selector.is_any_visible(TIKTOK_SELECTORS['tour_overlay']):
            print("Detected feature tour/overlay. Attempting to dismiss...")
            self.page.keyboard.press("Escape")
            wait_human(self.page, 'click')
        
        # 2. Try to find and click dismiss buttons
        dismiss_btn = selector.find_any_visible(TIKTOK_SELECTORS['dismiss_button'])
        if dismiss_btn:
            try:
                print("Found dismiss button, clicking...")
                dismiss_btn.click(timeout=2000)
                wait_human(self.page, 'click')
            except Exception:
                pass

    def _verify_success(self, timeout: int = 15) -> bool:
        """
        Verify if the video was successfully posted.
        """
        selector = SelectorStrategy(self.page)
        start_time = time.time()
        
        print("Verifying upload success...")
        
        while time.time() - start_time < timeout:
            if selector.is_any_visible(TIKTOK_SELECTORS['post_success_dialog']):
                print("SUCCESS: Post success dialog detected!")
                self._debug_screenshot("success_dialog")
                return True
            
            if "upload" not in self.page.url and "tiktok.com" in self.page.url:
                print(f"SUCCESS: Redirected away from upload page to: {self.page.url}")
                return True
            
            content = self.page.content()
            if "uploaded" in content.lower() and "video" in content.lower():
                print("SUCCESS: Found success message in page content.")
                return True
                
            time.sleep(2)
            
        print("Warning: Could not definitively confirm upload success.")
        self._debug_screenshot("verify_timeout")
        return False

    def upload_video(
        self, 
        file_path: str, 
        caption: str = "", 
        timeout: int = 60000,
        retry: bool = True
    ) -> bool:
        """
        Uploads a video to TikTok with advanced error handling.
        """
        self.last_error = None
        self.upload_attempts += 1
        
        if not self.page:
            self.last_error = "Page not initialized. Call login() first."
            return False
        
        if not os.path.exists(file_path):
            self.last_error = f"Video file not found: {file_path}"
            return False
            
        self.enable_monitoring()
        
        # Start Tracing if Debug
        if self.debug and self.context:
            print("[DEBUG] Starting trace recording...")
            self.context.tracing.start(screenshots=True, snapshots=True)

        selector = SelectorStrategy(self.page, timeout=10000)

        try:
            # 1. Navigate
            print("Navigating to upload page...")
            try:
                self.page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=timeout)
            except Exception:
                self.page.goto("https://www.tiktok.com/upload", wait_until="domcontentloaded", timeout=timeout)
            
            wait_human(self.page, 'navigate')
            self._dismiss_overlays()
            self._debug_screenshot("navigated")
            
            # 2. Upload
            print("Looking for file input...")
            file_input = selector.find(TIKTOK_SELECTORS['file_input'], state="attached", timeout=20000)
            
            if not file_input:
                self.last_error = "Could not find file upload input"
                return self._handle_failure(retry, file_path, caption, timeout)
            
            print(f"Uploading file: {file_path}")
            self.page.set_input_files(selector.last_successful_selector, file_path)
            wait_human(self.page, 'navigate')
            self._debug_screenshot("file_selected")
            
            # 3. Caption
            print("Waiting for caption area...")
            caption_input = selector.find(TIKTOK_SELECTORS['caption_area'], timeout=30000)
            
            if not caption_input:
                self.last_error = "Caption area did not appear"
                return self._handle_failure(retry, file_path, caption, timeout)
            
            wait_human(self.page, 'click')
            print(f"Entering caption...")
            try:
                human_type(self.page, selector.last_successful_selector, caption, clear_first=True)
            except Exception:
                self.page.fill(selector.last_successful_selector, caption)
            self._debug_screenshot("caption_entered")
            
            # 5. Wait for Ready
            if not self._wait_for_video_ready():
                self.last_error = "Video processing timed out"
                return self._handle_failure(retry, file_path, caption, timeout)
            
            # 6. Click Post
            self._dismiss_overlays()
            post_btn = selector.find(TIKTOK_SELECTORS['post_button'])
            if not post_btn:
                self.last_error = "Could not find Post button"
                return self._handle_failure(retry, file_path, caption, timeout)
            
            # Debug: Check button state
            try:
                btn_html = post_btn.evaluate("el => el.outerHTML")
                is_disabled = post_btn.is_disabled()
                print(f"[DEBUG] Post Button State: Disabled={is_disabled}")
                # print(f"[DEBUG] HTML: {btn_html[:100]}...") 
            except Exception:
                pass

            print(f"Clicking Post button...")
            self._debug_screenshot("before_post")
            wait_human(self.page, 'click')
            
            try:
                human_click(self.page, selector.last_successful_selector)
            except Exception:
                self.page.click(selector.last_successful_selector, force=True)
            
            # 6.5 Confirmation
            time.sleep(2)
            confirm_btn = selector.find(TIKTOK_SELECTORS['confirmation_button'], timeout=5000)
            if confirm_btn:
                print("Detected confirmation dialog, clicking...")
                self._debug_screenshot("confirmation_dialog")
                confirm_btn.click()
                wait_human(self.page, 'click')

            # 7. Verify
            success = self._verify_success()
            
            # Stop Tracing
            if self.debug and self.context:
                trace_path = f"trace_{int(time.time())}.zip"
                self.context.tracing.stop(path=trace_path)
                print(f"[DEBUG] Trace saved to {trace_path}")

            if success:
                self.upload_attempts = 0
            return success

        except Exception as e:
            self.last_error = f"TikTok upload failed: {e}"
            print(self.last_error)
            self._save_debug_screenshot()
            
            if self.debug and self.context:
                self.context.tracing.stop(path=f"trace_fail_{int(time.time())}.zip")

            return self._handle_failure(retry, file_path, caption, timeout)

    def _handle_failure(self, retry, file_path, caption, timeout) -> bool:
        self._save_debug_screenshot()
        
        if retry and self.upload_attempts < self.max_retries:
            wait_time = 30 * (2 ** (self.upload_attempts - 1))
            print(f"Retry {self.upload_attempts}/{self.max_retries} in {wait_time}s...")
            time.sleep(wait_time)
            
            try:
                self.page.reload()
                wait_human(self.page, 'navigate')
            except Exception:
                pass
            
            return self.upload_video(file_path, caption, timeout, retry=True)
        
        print(f"UPLOAD FAILED after {self.upload_attempts} attempts: {self.last_error}")
        self.upload_attempts = 0
        return False

    def _save_debug_screenshot(self):
        if self.page:
            try:
                filename = f"error_upload_debug_{int(time.time())}.png"
                self.page.screenshot(path=filename, full_page=True)
                print(f"Screenshot saved to '{filename}'")
            except Exception as e:
                print(f"Failed to save error screenshot: {e}")