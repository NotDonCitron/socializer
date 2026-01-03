"""
TikTok automation module with advanced anti-detection and retry logic.
"""
from playwright.sync_api import Page, BrowserContext
from radar.browser import BrowserManager
from radar.selectors import SelectorStrategy, TIKTOK_SELECTORS
from radar.human_behavior import human_delay, human_type, human_click, wait_human
from radar.session_manager import validate_tiktok_session
import time
import os


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

    def login(self, username=None, password=None, headless=False, timeout=30000):
        """
        Initialize browser and check login status.
        
        TikTok login is extremely difficult to automate reliably due to captchas.
        Recommended flow: login manually once with headless=False, then use 
        persistent context for future runs.
        
        Args:
            username: TikTok username (optional, mostly for reference)
            password: TikTok password (optional)
            headless: Run headless - False recommended to handle captchas
            timeout: Navigation timeout in ms
            
        Returns:
            True if appears logged in, False otherwise
        """
        self.last_error = None
        if not self.context:
            self.context = self.manager.launch_persistent_context(
                self.user_data_dir,
                headless=headless,
                randomize=True,  # Use randomized viewport/UA
            )
        
        self.page = self.manager.new_page(self.context, stealth=True)
        
        try:
            print("Browser context launched. Navigating to TikTok...")
            self.page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded", timeout=timeout)
            
            # Wait with human-like timing
            wait_human(self.page, 'navigate')
            
            # Validate session
            validation = validate_tiktok_session(self.page)
            if validation['valid']:
                print(f"Session valid: {validation['reason']}")
                return True
            
            # If not logged in and credentials provided, we could try,
            # but expect CAPTCHA to block us
            if username and password:
                print("Warning: Automated login is not reliable. Please log in manually.")
            
            print(f"Session invalid: {validation['reason']}")
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

    def _wait_for_video_ready(self, timeout: int = 120) -> bool:
        """
        Wait for video processing to complete.
        
        Watches for loading indicators to disappear and post button to enable.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            True if video is ready to post
        """
        selector = SelectorStrategy(self.page)
        start_time = time.time()
        
        print("Waiting for video processing...")
        
        while time.time() - start_time < timeout:
            # Check if loading indicators are gone
            is_loading = selector.is_any_visible(TIKTOK_SELECTORS['loading_indicator'])
            
            if not is_loading:
                # Check if post button is enabled
                post_btn = selector.find(TIKTOK_SELECTORS['post_button'], timeout=2000)
                if post_btn:
                    try:
                        if self.page.is_enabled(selector.last_successful_selector):
                            print("Video ready for posting!")
                            return True
                    except Exception:
                        pass
            
            time.sleep(2)
            
            # Progress feedback
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0:
                print(f"  Still processing... ({elapsed}s)")
        
        return False

    def _dismiss_overlays(self):
        """Dismiss tour overlays or popups that might block interaction."""
        selector = SelectorStrategy(self.page)
        
        if selector.is_any_visible(TIKTOK_SELECTORS['tour_overlay']):
            print("Detected feature tour/overlay. Attempting to dismiss...")
            self.page.keyboard.press("Escape")
            wait_human(self.page, 'click')

    def upload_video(
        self, 
        file_path: str, 
        caption: str = "", 
        timeout: int = 60000,
        retry: bool = True
    ) -> bool:
        """
        Uploads a video to TikTok with advanced error handling.
        
        Uses human-like interactions and multi-strategy selectors for reliability.
        Implements retry logic with exponential backoff.
        
        Args:
            file_path: Path to video file
            caption: Video caption/description
            timeout: Navigation timeout in ms
            retry: Whether to retry on failure
            
        Returns:
            True if upload successful
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
        selector = SelectorStrategy(self.page, timeout=10000)

        try:
            # 1. Navigate to Upload Page
            print("Navigating to upload page...")
            self.page.goto("https://www.tiktok.com/upload", wait_until="domcontentloaded", timeout=timeout)
            wait_human(self.page, 'navigate')
            
            # Dismiss any overlays
            self._dismiss_overlays()
            
            # 2. Handle File Upload
            print("Looking for file input...")
            file_input = selector.find(
                TIKTOK_SELECTORS['file_input'], 
                state="attached", 
                timeout=20000
            )
            
            if not file_input:
                self.last_error = "Could not find file upload input"
                return self._handle_failure(retry, file_path, caption, timeout)
            
            print(f"Uploading file: {file_path}")
            self.page.set_input_files(selector.last_successful_selector, file_path)
            wait_human(self.page, 'navigate')
            
            # 3. Wait for Video Processing
            print("Waiting for caption area to appear...")
            caption_input = selector.find(
                TIKTOK_SELECTORS['caption_area'],
                timeout=30000
            )
            
            if not caption_input:
                self.last_error = "Caption area did not appear - upload may have failed"
                return self._handle_failure(retry, file_path, caption, timeout)
            
            # 4. Enter Caption with human-like typing
            wait_human(self.page, 'click')
            print(f"Entering caption: {caption[:50]}...")
            
            try:
                # Use human-like typing for the caption
                human_type(self.page, selector.last_successful_selector, caption, clear_first=True)
            except Exception as e:
                # Fallback to regular typing
                print(f"Human typing failed, using fallback: {e}")
                self.page.focus(selector.last_successful_selector)
                self.page.keyboard.press("Control+A")
                self.page.keyboard.press("Backspace")
                self.page.keyboard.type(caption)
            
            # 5. Wait for Video Ready
            if not self._wait_for_video_ready():
                self.last_error = "Video processing timed out"
                return self._handle_failure(retry, file_path, caption, timeout)
            
            # 6. Click Post Button
            self._dismiss_overlays()  # Check again before clicking
            
            post_btn = selector.find(TIKTOK_SELECTORS['post_button'])
            if not post_btn:
                self.last_error = "Could not find Post button"
                return self._handle_failure(retry, file_path, caption, timeout)
            
            print(f"Clicking Post button...")
            wait_human(self.page, 'click')
            
            try:
                human_click(self.page, selector.last_successful_selector)
            except Exception:
                # Fallback to force click
                self.page.click(selector.last_successful_selector, force=True)
            
            # 7. Verify Upload Success
            print("Waiting for upload confirmation...")
            time.sleep(5)
            
            # TODO: Add proper success detection (URL change, success message, etc.)
            print("SUCCESS: Video upload initiated!")
            self.upload_attempts = 0  # Reset on success
            return True

        except Exception as e:
            self.last_error = f"TikTok upload failed: {e}"
            print(self.last_error)
            self._save_debug_screenshot()
            return self._handle_failure(retry, file_path, caption, timeout)

    def _handle_failure(
        self, 
        retry: bool, 
        file_path: str, 
        caption: str, 
        timeout: int
    ) -> bool:
        """Handle upload failure with optional retry."""
        self._save_debug_screenshot()
        
        if retry and self.upload_attempts < self.max_retries:
            # Exponential backoff: 30s, 60s, 120s
            wait_time = 30 * (2 ** (self.upload_attempts - 1))
            print(f"Retry {self.upload_attempts}/{self.max_retries} in {wait_time}s...")
            time.sleep(wait_time)
            
            # Refresh page and retry
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
        """Save a debug screenshot on error."""
        if self.page:
            try:
                filename = f"error_upload_debug_{int(time.time())}.png"
                self.page.screenshot(path=filename, full_page=True)
                print(f"Screenshot saved to '{filename}'")
            except Exception as e:
                print(f"Failed to save error screenshot: {e}")

    def check_shadowban(self) -> dict:
        """
        Check for potential shadowban indicators.
        
        Returns:
            Dict with shadowban status and indicators
        """
        result = {
            'potentially_shadowbanned': False,
            'indicators': [],
            'recommendations': []
        }
        
        if not self.page:
            result['error'] = 'Page not initialized'
            return result
        
        try:
            # Navigate to profile to check video visibility
            self.page.goto("https://www.tiktok.com/@me", wait_until="domcontentloaded")
            wait_human(self.page, 'navigate')
            
            # Check for warning banners
            warning_selectors = [
                '[class*="warning"]',
                '[class*="violation"]',
                '[class*="suspended"]',
            ]
            
            selector = SelectorStrategy(self.page)
            if selector.is_any_visible(warning_selectors):
                result['potentially_shadowbanned'] = True
                result['indicators'].append('Warning banner detected')
            
            # Check if videos are showing
            video_count = self.page.locator('[data-e2e="user-post-item"]').count()
            if video_count == 0:
                result['indicators'].append('No videos visible on profile')
            
            # Recommendations
            if result['potentially_shadowbanned']:
                result['recommendations'] = [
                    'Pause posting for 24-48 hours',
                    'Review content for policy violations',
                    'Avoid rapid/repeated actions',
                    'Consider using a different account for testing',
                ]
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result

