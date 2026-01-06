"""
Instagram automation module with advanced anti-detection and retry logic.
"""
from typing import Optional
import random
from playwright.sync_api import Page, BrowserContext, ElementHandle
from radar.browser import BrowserManager
from radar.element_selectors import SelectorStrategy, INSTAGRAM_SELECTORS
from radar.session_manager import load_playwright_cookies
from radar.engagement_models import EngagementAction, EngagementResult, EngagementActionType, EngagementPlatform, EngagementStatus
from radar.session_orchestrator import SessionOrchestrator, SessionContext, EngagementPlatform as OrchestratorPlatform
from radar.human_behavior import human_delay, human_click, wait_human
import time
import os
import datetime
from collections import deque

class InstagramAutomator:
    """
    Instagram upload automation with anti-detection measures.

    Features:
    - Human-like interaction patterns
    - Multi-strategy selectors with fallbacks
    - Retry logic with exponential backoff
    - Session validation and shadowban detection
    - Integration with SessionOrchestrator for multi-account support
    """

    def __init__(self, session_context: Optional[SessionContext] = None, account_id: Optional[str] = None):
        """
        Initialize Instagram automator.

        Args:
            session_context: SessionContext from SessionOrchestrator (preferred)
            account_id: Account ID for legacy compatibility
        """
        self.session_context = session_context
        self.account_id = account_id or (session_context.account_id if session_context else None)
        self.context: BrowserContext = session_context.browser_context if session_context else None
        self.page: Page = None
        self.last_error: str = None
        self.upload_attempts: int = 0
        self.max_retries: int = 3
        self.debug = os.environ.get("DEBUG", "0") == "1"
        self._action_timestamps = deque(maxlen=90)  # soft per-minute guard

        # Legacy support - create browser manager if no session context
        if not session_context:
            self.manager = BrowserManager()
            self.user_data_dir = f"data/sessions/instagram/{account_id}" if account_id else "data/instagram_session"
            os.makedirs(self.user_data_dir, exist_ok=True)

        if self.debug:
            os.makedirs("debug_shots", exist_ok=True)

    def _debug_log(self, message: str):
        if self.debug:
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            print(f"[DEBUG] {message}")
            if self.page:
                # Sanitize message for filename: strip newlines, remove bad chars
                clean_msg = message.split('\n')[0] # Only take first line
                safe_msg = "".join([c if c.isalnum() or c in " _-" else "_" for c in clean_msg])
                safe_msg = safe_msg.replace(' ', '_').lower()[:30]
                
                filename = os.path.join("debug_shots", f"debug_ig_{timestamp}_{safe_msg}.png")
                try:
                    self.page.screenshot(path=filename)
                    print(f"[DEBUG] Saved screenshot: {filename}")
                except Exception as e:
                    print(f"[DEBUG] Failed to save screenshot: {e}")
                    pass

    def _handle_new_page(self, page: Page):
        """Handler for new pages/tabs opened by the browser."""
        try:
            # Ignore the primary page
            if self.page and page == self.page:
                return

            url = page.url
            block_list = [
                "facebook.com/help/cancelcontracts",
                "help.instagram.com",
                "transparency.fb.com",
                "chrome-error://",
            ]

            def should_block(u: str) -> bool:
                return any(b in u for b in block_list)

            if should_block(url):
                self._debug_log(f"Auto-closing blocking page (immediate): {url}")
                try:
                    page.close()
                except:
                    pass
                if self.page:
                    self.page.bring_to_front()
                return

            # If it wasn't blocked at creation, still check quickly after load
            page.wait_for_load_state("domcontentloaded", timeout=3000)
            url = page.url
            if should_block(url):
                self._debug_log(f"Auto-closing blocking page (post-load): {url}")
                try:
                    page.close()
                except:
                    pass
                if self.page:
                    self.page.bring_to_front()
            else:
                self._debug_log(f"New page detected (allowed): {url}")
        except Exception:
            # Silent fail for the handler to avoid crashing the main loop
            pass

    def login(self, username=None, password=None, headless=True, timeout=45000):
        """
        Initialize browser and check login status.

        When using SessionOrchestrator, the session context is already set up.
        This method validates the existing session or provides guidance for manual login.
        """
        self.last_error = None

        # If using session orchestrator, context is already available
        if self.session_context:
            self.context = self.session_context.browser_context
            # Update activity timestamp
            self.session_context.update_activity()

        # Legacy support - create browser context if not using orchestrator
        if not self.context:
            self.context = self.manager.launch_persistent_context(
                self.user_data_dir,
                headless=headless,
                viewport={"width": 1280, "height": 800}
            )
            # Try to load SeleniumBase cookies if available
            cookies_path = os.path.join(self.user_data_dir, "cookies.json")
            if not os.path.exists(cookies_path):
                cookies_path = "ig_session/cookies.json"
            load_playwright_cookies(self.context, path=cookies_path)

            # 1. Block the popup at the network layer (Kill it before it's created)
            def abort_and_log(route):
                if self.debug:
                    print(f"[DEBUG] Aborted request: {route.request.url}")
                route.abort()

            self.context.route("**/facebook.com/help/cancelcontracts**", abort_and_log)
            self.context.route("**/help/cancelcontracts?source=instagram.com**", abort_and_log)
            self.context.route("**/help.instagram.com/**", abort_and_log)
            self.context.route("**/transparency.fb.com/**", abort_and_log)

            # Auto-close new tabs/windows that might be popups or redirects
            self.context.on("page", self._handle_new_page)

        # Create page if not exists
        if not self.page:
            self.page = self.manager.new_page(self.context, stealth=True)

        try:
            print("Browser context launched. Navigating to Instagram...")
            self.page.goto("https://www.instagram.com/explore/", wait_until="domcontentloaded", timeout=timeout)
            wait_human(self.page, 'navigate')

            # Check for Facebook redirect (Consumer rights/Contract cancel pages)
            if "facebook.com" in self.page.url:
                self._debug_log(f"Detected Facebook redirect ({self.page.url}). Forcing return to Instagram...")
                self.page.goto("https://www.instagram.com/explore/", wait_until="domcontentloaded", timeout=timeout)
                wait_human(self.page, 'navigate')

            # Check if we are already logged in
            if "login" not in self.page.url:
                self.handle_popups()
                # Update session persistence if using orchestrator
                if self.session_context and self.session_context.session_data:
                    from radar.session_persistence import SessionPersistence
                    persistence = SessionPersistence()
                    persistence.update_login_status(self.account_id, True, True)
                return True

            print(f"Session invalid - redirected to login page")
            print("💡 TIP: Run 'python -m radar.auth_bridge' to log in interactively with SeleniumBase UC Mode.")
            # Update session persistence if using orchestrator
            if self.session_context and self.session_context.session_data:
                from radar.session_persistence import SessionPersistence
                persistence = SessionPersistence()
                persistence.update_login_status(self.account_id, False, False)
            return False

        except Exception as e:
            self.last_error = f"Login navigation failed: {e}"
            print(self.last_error)
            # Mark session error if using orchestrator
            if self.session_context:
                self.session_context.mark_error()
            return False

    def handle_popups(self, timeout=5000):
        """Closes common Instagram popups."""
        popups = [
            "text=Not Now", "text=Nicht jetzt", 
            "button:has-text('Not Now')", "button:has-text('Nicht jetzt')",
            "text=Abbrechen", "text=Cancel",
            # Cookie/consent variants seen across regions
            "button:has-text('Decline optional cookies')",
            "button:has-text('Only allow essential cookies')",
            "button:has-text('Allow essential cookies')",
            "button:has-text('Allow all cookies')",
            "button:has-text('Accept all')",
            "button:has-text('Accept All')",
            "button:has-text('Accept')",
            "button:has-text('Reject all')",
            "button:has-text('Reject All')",
            "text=Allow all cookies", "text=Alle Cookies zulassen",
            "button:has-text('Got it')", "button:has-text('OK')",
            "button:has-text('Next')", "button:has-text('Weiter')", # Sometimes these are "feature discovery" next buttons
            "[aria-label='Close']", "[aria-label='Schließen']",
            "button[aria-label='Close']", 
            "div[role='button']:has-text('Not Now')",
            "div[role='button']:has-text('Nicht jetzt')",
            "div[role='dialog'] button:has-text('OK')", # Generic dialog OK
            "div[role='dialog'] button:has-text('Done')",
            "text=New! separate tabs", # Feature discovery
            "text=Neu! separate Tabs",
            # Notification prompts
            "button:has-text('Turn On')",
            "button:has-text('Turn on notifications')",
            "button:has-text('Enable notifications')",
            "button:has-text('Maybe later')",
            "button:has-text('Maybe Later')",
            "text=Turn on notifications",
            "text=Benachrichtigungen aktivieren",
        ]
        
        for selector in popups:
            try:
                if self.page.is_visible(selector, timeout=500):
                    # Be careful not to close the *upload* Next button if we are in that phase,
                    # but usually handle_popups is called before/during specific waits.
                    # We might need to be context-aware, but for now, let's just close annoyances.
                    # If 'Next' is in popups, it might click the upload Next button prematurely?
                    # valid point. Let's remove generic 'Next' from here to be safe.
                    if "Next" in selector or "Weiter" in selector:
                        continue

                    self._debug_log(f"Closing popup: {selector}")
                    self.page.click(selector)
                    self.page.wait_for_timeout(500)
            except:
                continue

    def _click_create_button(self, strategy: SelectorStrategy, timeout: int = 15000) -> bool:
        """
        Waits for the Create/New Post button to be clickable with multiple fallbacks.
        Retries while clearing popups that can obscure the sidebar.
        """
        create_selectors = [
            'svg[aria-label="New post"]',
            'svg[aria-label="Create"]',
            'svg[aria-label="Erstellen"]',
            'svg[aria-label="Neuer Beitrag"]',
            'svg[aria-label*="post" i]',
            'svg[aria-label*="create" i]',
            '[data-testid="new-post-button"]',
            'div[role="button"][aria-label*="Create" i]',
            'button[aria-label*="Create" i]',
            'button:has-text("Create")',
            'button:has-text("Erstellen")',
            'div[role="button"]:has-text("Create")',
            'div[role="button"]:has-text("New post")',
            'div[role="button"]:has-text("Erstellen")',
            'div[role="button"]:has-text("Neuer Beitrag")',
            'div[role="link"]:has-text("Create")',
            'a[role="link"]:has-text("Create")',
            'a[role="link"]:has-text("Erstellen")',
            'span:has-text("Create")',
            'span:has-text("New post")',
            'span:has-text("Erstellen")',
            'span:has-text("Neuer Beitrag")'
        ]

        # Sidebar can be delayed even when DOMContentLoaded fires
        try:
            self.page.wait_for_selector('nav[role="navigation"]', timeout=5000)
        except Exception:
            pass

        deadline = time.time() + (timeout / 1000)
        force_click = False

        while time.time() < deadline:
            self.handle_popups()
            selector = strategy.wait_for_any(create_selectors, timeout=1500)
            if not selector:
                self.page.wait_for_timeout(300)
                continue

            element = self.page.query_selector(selector)
            if not element:
                self.page.wait_for_timeout(200)
                continue

            try:
                element.scroll_into_view_if_needed(timeout=2000)
                # Fail fast on click so we can retry with force
                if force_click:
                     # JS Click is the nuclear option for overlays
                    self._debug_log(f"Attempting JS click on {selector}")
                    # Use dispatchEvent for SVGs which lack .click()
                    element.evaluate("el => { if (el.click) { el.click(); } else { el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window})); } }")
                    return True
                else:
                    element.click(timeout=2000)
                    return True
            except Exception as e:
                self._debug_log(f"Create click retry ({selector}): {e}")
                force_click = True # Enable force/JS click for next try
                self.page.wait_for_timeout(400)

        return False

    def _upload_media(self, file_path: str, retry: bool = True):
        """
        Robustly handles the media upload dialog on Instagram Desktop.
        """
        if self.page:
            self.page.bring_to_front()

        dialog = self.page.locator('div[role="dialog"]').first
        dialog.wait_for(state="visible", timeout=8000)
        # Small settle to let Instagram replace the input after the button click
        self.page.wait_for_timeout(500)
        
        # Click on dialog to ensure focus
        try:
            dialog.click(position={"x": 10, "y": 10})
        except:
            pass

        input_locator = dialog.locator('input[type="file"]').first
        # If the input is not there yet, fall back to clicking the button to spawn it
        try:
            input_locator.wait_for(state="visible", timeout=1000)
        except Exception:
            pass
            
        if not input_locator.is_visible():
            select_btn = dialog.locator('button:has-text("Select from computer"), button:has-text("Von Computer auswählen")').first
            if select_btn.is_visible():
                with self.page.expect_file_chooser() as fc:
                    select_btn.click()
                input_locator = fc.value
            else:
                # Last resort: wait for the input to attach
                input_locator = self.page.wait_for_selector('div[role="dialog"] input[type="file"]', state="attached", timeout=5000)

        abs_path = os.path.abspath(file_path)
        # Handle both FileChooser and Locator objects
        if hasattr(input_locator, "set_files"):
            input_locator.set_files(abs_path)
        else:
            input_locator.set_input_files(abs_path)

        # Fire change/input for safety (sometimes helps React register)
        try:
            # If it's a FileChooser, we might not have element_handle easily, but usually we do for locators
            if hasattr(input_locator, "element_handle"):
                element_handle = input_locator.element_handle()
                element_handle.evaluate("""(el) => {
                    ['input','change', 'blur', 'focus'].forEach(ev => el.dispatchEvent(new Event(ev, { bubbles: true })));
                }""")
        except Exception:
            pass
        
        # Bring back to front in case popups stole focus
        if self.page:
            self.page.bring_to_front()

        # Check for immediate upload errors
        try:
            error_msg = dialog.locator('h2:has-text("Couldn\'t select file"), div[role="alert"]').first
            if error_msg.is_visible(timeout=2000):
                self._debug_log(f"Upload error detected: {error_msg.inner_text()}")
        except:
            pass

        # Wait for potential internal IG processing spinner to disappear
        try:
            dialog.wait_for_selector('[data-visualcompletion="loading-state"]', state="detached", timeout=10000)
        except:
            pass

        # Wait for preview/Next to appear; if the dialog vanished, reopen
        # Expanded selectors for Next button, scoped to the dialog
        next_selectors = [
            'div._ac7d [role="button"]', # Scoped to the common header container
            'button:has-text("Next")', 
            'button:has-text("Weiter")',
            'div[role="button"]:has-text("Next")',
            'div[role="button"]:has-text("Weiter")',
            '[aria-label="Next"]',
            '[aria-label="Weiter"]',
            'div[role="button"] >> text=/Next|Weiter/'
        ]
        
        # Iterate and click the first visible Next button
        found_next = False
        start_time = time.time()
        while time.time() - start_time < 30:
            for selector in next_selectors:
                btn = dialog.locator(selector).first
                if btn.is_visible():
                    self._debug_log(f"Found visible Next button: {selector}")
                    btn.click()
                    self.page.wait_for_timeout(1000)
                    found_next = True
                    return # Success, return to upload_video
            self.page.wait_for_timeout(500)

        if not found_next:
            is_dialog_visible = False
            try:
                is_dialog_visible = dialog.is_visible()
                self._debug_log(f"Upload stalled. Dialog visible: {is_dialog_visible}")
                if is_dialog_visible:
                     # Log available buttons for debugging
                    try:
                        buttons = dialog.locator("button, [role='button']").all_inner_texts()
                        self._debug_log(f"Buttons found in dialog: {buttons}")
                    except:
                        pass
                    self._debug_log(f"Dialog text: {dialog.inner_text()[:300]}")
            except:
                pass

            if retry and not is_dialog_visible:
                # Modal likely closed; reopen and retry once
                self._debug_log("Modal vanished during upload, retrying...")
                if self._click_create_button(SelectorStrategy(self.page)):
                    return self._upload_media(file_path, retry=False)
            
            self._debug_log("IG_UPLOAD_FAIL: Upload stalled or modal vanished.")
            raise Exception("Next button not found")

    def upload_video(self, file_path: str, caption: str = "", timeout: int = 300000) -> bool:
        """
        Uploads a video (Reel) to Instagram via Desktop UI.
        """
        self.last_error = None
        if not self.page:
            self.last_error = "Page not initialized."
            return False

        strategy = SelectorStrategy(self.page)
        
        try:
            # Only navigate if not already on home
            if "instagram.com" not in self.page.url:
                self.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            
            self.handle_popups()

            # 1. Click 'Create' button in sidebar
            self._debug_log("Clicking Create")
            if not self._click_create_button(strategy, timeout=60000):
                self._debug_log("IG_UPLOAD_FAIL: Could not find 'Create' button.")
                self.last_error = "Could not find 'Create' button."
                return False

            # 2. File Upload
            self._debug_log("Handling file input")
            try:
                self._upload_media(file_path)
            except Exception as e:
                self._debug_log(f"IG_UPLOAD_FAIL: File selection failed: {e}")
                self.last_error = f"File selection failed: {e}"
                return False

            # 3. Handle 'Crop' / Aspect Ratio
            # Wait for 'Next' to appear (means upload/preview started)
            self._debug_log("Waiting for Next button")
            
            # Use dialog scoped locator for the click as well
            dialog = self.page.locator('div[role="dialog"]').last
            next_selectors = [
                'div._ac7d [role="button"]',
                'button:has-text("Next")',
                'button:has-text("Weiter")',
                'div[role="button"]:has-text("Next")',
                'div[role="button"]:has-text("Weiter")',
                '[aria-label="Next"]',
                '[aria-label="Weiter"]',
                'div[role="button"] >> text=/Next|Weiter/'
            ]
            combined_selector = ", ".join(next_selectors)
            next_btn = dialog.locator(combined_selector).first

            try:
                next_btn.wait_for(state="visible", timeout=30000)
            except Exception:
                # Log available buttons for debugging
                buttons = dialog.locator("button, [role='button']").all_inner_texts()
                self._debug_log(f"Buttons found in dialog: {buttons}")
                
                # Check for Crop header
                crop_header = dialog.locator('h1:has-text("Crop"), h1:has-text("Zuschneiden")')
                if crop_header.is_visible():
                     self._debug_log("Crop header visible, but Next button missing.")
                     # Last resort: Click top right corner of dialog where Next usually is
                     box = dialog.bounding_box()
                     if box:
                         x = box["x"] + box["width"] - 40
                         y = box["y"] + 40
                         self._debug_log(f"Attempting coordinate click at {x},{y}")
                         self.page.mouse.click(x, y)
                         self.page.wait_for_timeout(2000)
                         return # Assume success and return control to upload_video

                self._debug_log("IG_UPLOAD_FAIL: Next button did not appear after upload.")
                self.last_error = "Next button did not appear after upload."
                
                # HTML Dump logic...
                try:
                    timestamp = datetime.datetime.now().strftime("%H%M%S")
                    html_filename = os.path.join("debug_shots", f"debug_ig_{timestamp}_dialog_dump.html")
                    with open(html_filename, "w", encoding="utf-8") as f:
                        f.write(dialog.inner_html())
                    self._debug_log(f"Saved dialog HTML dump: {html_filename}")
                except Exception as e:
                    self._debug_log(f"Failed to dump HTML: {e}")
                return False

            # For Reels, we usually want 9:16. 
            # We can click the aspect ratio button if needed, but IG often defaults to 9:16 for videos.
            next_btn.click()
            self.page.wait_for_timeout(1000)

            # 4. Handle 'Edit' (Filter/Trim) screen
            self._debug_log("Edit screen")
            # Reuse robust selectors
            # We assume we are on Edit screen if Next is visible.
            # We need to click Next to get to Caption.
            
            # Try to transition to Caption screen
            transitioned_to_caption = False
            
            # Robust share selectors (from Step 6)
            share_selectors = [
                'div._ac7d [role="button"]', 
                'button:has-text("Share")', 
                'button:has-text("Teilen")',
                'div[role="button"]:has-text("Share")',
                'div[role="button"]:has-text("Teilen")',
                'div[role="button"] >> text=/Share|Teilen/'
            ]

            caption_selectors = [
                'div[aria-label*="Write a caption"]',
                'div[role="textbox"]',
                'textarea[aria-label*="caption"]'
            ]

            for attempt in range(3):
                # Check if we are already at caption (Share button visible?)
                # We iterate because combined locator might fail on hidden elements
                found_share_check = False
                for s in share_selectors:
                    if dialog.locator(s).first.is_visible():
                         # We need to distinguish Share from Next. Next is also in div._ac7d [role="button"]
                         # The text content helps.
                         txt = dialog.locator(s).first.inner_text()
                         if "Share" in txt or "Teilen" in txt:
                            found_share_check = True
                            break
                
                if found_share_check:
                    self._debug_log("Share button visible, assuming Caption screen.")
                    transitioned_to_caption = True
                    break

                # Check if Next button is there (Edit screen)
                found_next_edit = False
                for selector in next_selectors:
                    btn = dialog.locator(selector).first
                    if btn.is_visible():
                        # Verify it's not Share
                        if "Share" not in btn.inner_text() and "Teilen" not in btn.inner_text():
                             self._debug_log(f"Found Next button (Edit screen): {selector}")
                             btn.click()
                             found_next_edit = True
                             self.page.wait_for_timeout(2000) # Wait for transition
                             break
                
                if not found_next_edit:
                    self._debug_log("No Next button found on Edit screen. checking if we are already at Caption...")
                
                # Check if Caption box appeared
                if strategy.find(caption_selectors, timeout=5000):
                    self._debug_log("Caption box found.")
                    transitioned_to_caption = True
                    break
                
                self._debug_log(f"Transition to caption failed (attempt {attempt+1}). Retrying...")
                self.page.wait_for_timeout(1000)

            # 5. Caption screen
            self._debug_log("Caption screen")
            caption_box = strategy.find(caption_selectors, timeout=5000)
            if caption_box:
                caption_box.fill(caption)
                self.page.wait_for_timeout(500)
            elif not transitioned_to_caption:
                 self._debug_log("IG_UPLOAD_FAIL: Could not reach Caption screen.")
                 return False
            
            # 6. Final Share
            self._debug_log("Clicking Share")
            share_selectors = [
                'div._ac7d [role="button"]', # Often the same position as Next
                'button:has-text("Share")', 
                'button:has-text("Teilen")',
                'div[role="button"]:has-text("Share")',
                'div[role="button"]:has-text("Teilen")',
                'div[role="button"] >> text=/Share|Teilen/'
            ]
            
            # Use same iterative visible check
            dialog = self.page.locator('div[role="dialog"]').first
            found_share = False
            for selector in share_selectors:
                btn = dialog.locator(selector).first
                if btn.is_visible():
                    self._debug_log(f"Found visible Share button: {selector}")
                    btn.click()
                    found_share = True
                    break

            if not found_share:
                self._debug_log("IG_UPLOAD_FAIL: Could not find 'Share' button.")
                self.last_error = "Could not find 'Share' button."
                return False

            # 7. Verification
            self._debug_log("Waiting for success")
            success_selectors = [
                'text="Your reel has been shared"',
                'text="Dein Reel wurde geteilt"',
                'text="Your post has been shared"',
                'text="Dein Beitrag wurde geteilt"',
                'h2:has-text("shared")',
                'svg[aria-label="Animated checkmark"]'
            ]
            
            # This can take time for video processing
            if strategy.find(success_selectors, timeout=60000):
                self._debug_log("Upload Success!")
                return True
            else:
                # Disappearance of 'Sharing' indicator is also a hint
                if not self.page.is_visible('text="Sharing"'):
                    self._debug_log("Sharing indicator gone, assuming success")
                    return True
                
            self._debug_log("IG_UPLOAD_FAIL: Success message not found.")
            self.last_error = "Success message not found."
            return False

        except Exception as e:
            self._debug_log(f"IG_UPLOAD_FAIL: Exception: {e}")
            self.last_error = str(e)
            return False

    def upload_photo(self, file_path: str, caption: str = "", timeout: int = 45000) -> bool:
        """Original photo upload (keeping for compat)."""
        # Logic remains similar but could be updated to use Strategy
        return self.upload_video(file_path, caption, timeout) # Video uploader handles photos too on desktop

    def _navigate_to_post(self, post_url: str) -> bool:
        """Navigate to a specific Instagram post."""
        try:
            self._debug_log(f"Navigating to post: {post_url}")
            self.page.goto(post_url, wait_until="domcontentloaded", timeout=30000)
            self.page.wait_for_timeout(3000)  # Wait for post to load
            self.handle_popups()
            return True
        except Exception as e:
            self.last_error = f"Navigation failed: {e}"
            return False

    def _execute_engagement_action(self, action_type: EngagementActionType, target_identifier: str,
                                 metadata: dict = None) -> EngagementResult:
        """Execute an engagement action with proper tracking and error handling."""
        # Basic rate limiting to avoid bursty behavior (GramAddict-style soft cap)
        self._respect_rate_limits()

        action = EngagementAction(
            action_type=action_type,
            platform=EngagementPlatform.INSTAGRAM,
            target_identifier=target_identifier,
            metadata=metadata or {}
        )

        try:
            # Navigate to target if it's a URL
            if target_identifier.startswith(('http://', 'https://')):
                if not self._navigate_to_post(target_identifier):
                    return EngagementResult(
                        action=action,
                        success=False,
                        message=f"Failed to navigate to {target_identifier}: {self.last_error}"
                    )

            # Execute the specific action
            result = self._perform_action(action)
            return result

        except Exception as e:
            action.status = EngagementStatus.FAILED
            action.error_message = str(e)
            return EngagementResult(
                action=action,
                success=False,
                message=f"Engagement action failed: {e}"
            )

    def _perform_action(self, action: EngagementAction) -> EngagementResult:
        """Perform the specific engagement action."""
        strategy = SelectorStrategy(self.page)

        if action.action_type == EngagementActionType.LIKE:
            return self._perform_like(action, strategy)
        elif action.action_type == EngagementActionType.FOLLOW:
            return self._perform_follow(action, strategy)
        elif action.action_type == EngagementActionType.COMMENT:
            return self._perform_comment(action, strategy)
        elif action.action_type == EngagementActionType.SAVE:
            return self._perform_save(action, strategy)
        elif action.action_type == EngagementActionType.SHARE:
            return self._perform_share(action, strategy)
        else:
            return EngagementResult(
                action=action,
                success=False,
                message=f"Unsupported action type: {action.action_type}"
            )

    def _perform_like(self, action: EngagementAction, strategy: SelectorStrategy) -> EngagementResult:
        """Perform like action on a post with robust verification."""
        try:
            self._debug_log("Attempting to like post")

            # Check if already liked (multiple indicators)
            if self._is_already_liked(strategy):
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Post already liked"
                )

            # Try to find like button
            like_button = strategy.find(INSTAGRAM_SELECTORS["like_button"], timeout=5000)
            if not like_button:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Like button not found"
                )

            # Click like button with human-like behavior
            human_click(self.page, strategy.last_successful_selector)
            wait_human(self.page, 'click')

            # Robust verification
            if self._verify_like_success(strategy):
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Post liked successfully"
                )
            else:
                # Fallback: Assume success if click was successful
                self._debug_log("Primary verification failed, assuming success from successful click")
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Like action completed (verification uncertain)"
                )

        except Exception as e:
            return EngagementResult(
                action=action,
                success=False,
                message=f"Like failed: {e}"
            )

    def _is_already_liked(self, strategy: SelectorStrategy) -> bool:
        """Check multiple indicators if post is already liked."""
        liked_indicators = [
            INSTAGRAM_SELECTORS["unlike_button"],
            ["button[aria-label*='Unlike']", "[data-testid*='unlike']"],
            [".liked", "svg[fill*='red']", "span[color*='red']"]
        ]

        for indicator_set in liked_indicators:
            if strategy.find(indicator_set, timeout=1000):
                return True
        return False

    def _verify_like_success(self, strategy: SelectorStrategy) -> bool:
        """Robust verification of like action success."""
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                # Wait for UI updates
                wait_time = 1 + (attempt * 0.5)  # 1s, 1.5s, 2s
                self.page.wait_for_timeout(wait_time * 1000)

                # Method 1: Check for unlike button
                if strategy.find(INSTAGRAM_SELECTORS["unlike_button"], timeout=2000):
                    self._debug_log(f"Like verified via unlike button (attempt {attempt + 1})")
                    return True

                # Method 2: Check for visual indicators
                unlike_selectors = [
                    "button[aria-label*='Unlike']",
                    "[data-testid*='unlike']",
                    "svg[fill*='red']",
                    ".unlike-button"
                ]

                for selector in unlike_selectors:
                    if self.page.is_visible(selector, timeout=1000):
                        self._debug_log(f"Like verified via visual indicator: {selector}")
                        return True

                # Method 3: Check if like button changed/disappeared
                if not strategy.find(INSTAGRAM_SELECTORS["like_button"], timeout=1000):
                    self._debug_log(f"Like verified via like button disappearance (attempt {attempt + 1})")
                    return True

                self._debug_log(f"Like verification attempt {attempt + 1} failed, retrying...")

            except Exception as e:
                self._debug_log(f"Like verification error on attempt {attempt + 1}: {e}")

        self._debug_log("All like verification attempts failed")
        return False

    def _perform_follow(self, action: EngagementAction, strategy: SelectorStrategy) -> EngagementResult:
        """Perform follow action on a user with robust verification."""
        try:
            self._debug_log("Attempting to follow user")

            # Try to find follow button
            follow_button = strategy.find(INSTAGRAM_SELECTORS["follow_button"], timeout=5000)
            if not follow_button:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Follow button not found"
                )

            # Check if already following (multiple indicators)
            if self._is_already_following(strategy):
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Already following user"
                )

            # Click follow button with human-like behavior
            human_click(self.page, strategy.last_successful_selector)
            wait_human(self.page, 'click')

            # Robust verification with multiple methods
            if self._verify_follow_success(strategy):
                return EngagementResult(
                    action=action,
                    success=True,
                    message="User followed successfully"
                )
            else:
                # Fallback: Assume success if click was successful (common case)
                self._debug_log("Primary verification failed, assuming success from successful click")
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Follow action completed (verification uncertain)"
                )

        except Exception as e:
            return EngagementResult(
                action=action,
                success=False,
                message=f"Follow failed: {e}"
            )

    def _is_already_following(self, strategy: SelectorStrategy) -> bool:
        """Check multiple indicators if user is already following."""
        following_indicators = [
            INSTAGRAM_SELECTORS["unfollow_button"],
            ["button:has-text('Following')", "button:has-text('Requested')"],
            ["[aria-label*='Unfollow']", "[data-testid*='following']"],
            [".followed", "[role='button']:has-text('Following')"]
        ]

        for indicator_set in following_indicators:
            if strategy.find(indicator_set, timeout=1000):
                return True
        return False

    def _verify_follow_success(self, strategy: SelectorStrategy) -> bool:
        """Robust verification of follow action success."""
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                # Wait progressively longer for UI updates
                wait_time = 1 + (attempt * 1)  # 1s, 2s, 3s
                self.page.wait_for_timeout(wait_time * 1000)

                # Method 1: Check for unfollow button (primary method)
                if strategy.find(INSTAGRAM_SELECTORS["unfollow_button"], timeout=2000):
                    self._debug_log(f"Follow verified via unfollow button (attempt {attempt + 1})")
                    return True

                # Method 2: Check for "Following" text in various elements
                following_selectors = [
                    "button:has-text('Following')",
                    "div:has-text('Following')",
                    "[aria-label*='Following']",
                    "[data-testid*='following']"
                ]

                for selector in following_selectors:
                    if self.page.is_visible(selector, timeout=1000):
                        self._debug_log(f"Follow verified via following indicator: {selector}")
                        return True

                # Method 3: Check if follow button disappeared
                if not strategy.find(INSTAGRAM_SELECTORS["follow_button"], timeout=1000):
                    self._debug_log(f"Follow verified via follow button disappearance (attempt {attempt + 1})")
                    return True

                self._debug_log(f"Verification attempt {attempt + 1} failed, retrying...")

            except Exception as e:
                self._debug_log(f"Verification error on attempt {attempt + 1}: {e}")

        self._debug_log("All verification attempts failed")
        return False

    def _perform_comment(self, action: EngagementAction, strategy: SelectorStrategy) -> EngagementResult:
        """Perform comment action on a post."""
        try:
            self._debug_log("Attempting to comment on post")

            comment_text = action.metadata.get("comment_text", "")
            if not comment_text:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="No comment text provided"
                )

            # Find comment button
            comment_button = strategy.find(INSTAGRAM_SELECTORS["comment_button"], timeout=5000)
            if not comment_button:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Comment button not found"
                )

            # Click comment button
            human_click(self.page, strategy.last_successful_selector)
            wait_human(self.page, 'click')

            # Find comment input
            comment_input = strategy.find(INSTAGRAM_SELECTORS["comment_input"], timeout=5000)
            if not comment_input:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Comment input not found"
                )

            # Type comment with human-like behavior
            from radar.human_behavior import human_type
            human_type(self.page, strategy.last_successful_selector, comment_text)
            wait_human(self.page, 'type')

            # Find and click post button
            post_button = strategy.find(INSTAGRAM_SELECTORS["post_comment_button"], timeout=5000)
            if not post_button:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Post comment button not found"
                )

            human_click(self.page, strategy.last_successful_selector)
            wait_human(self.page, 'click')

            # Verify comment was posted
            # Look for the comment text in the comments section
            if strategy.is_any_visible([f'text="{comment_text}"'], timeout=5000):
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Comment posted successfully"
                )
            else:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Could not verify comment was posted"
                )

        except Exception as e:
            return EngagementResult(
                action=action,
                success=False,
                message=f"Comment failed: {e}"
            )

    def _perform_save(self, action: EngagementAction, strategy: SelectorStrategy) -> EngagementResult:
        """Perform save action on a post with robust verification."""
        try:
            self._debug_log("Attempting to save post")

            # Check if already saved (multiple indicators)
            if self._is_already_saved(strategy):
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Post already saved"
                )

            # Try to find save button
            save_button = strategy.find(INSTAGRAM_SELECTORS["save_button"], timeout=5000)
            if not save_button:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Save button not found"
                )

            # Click save button with human-like behavior
            human_click(self.page, strategy.last_successful_selector)
            wait_human(self.page, 'click')

            # Robust verification
            if self._verify_save_success(strategy):
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Post saved successfully"
                )
            else:
                # Fallback: Assume success if click was successful
                self._debug_log("Primary verification failed, assuming success from successful click")
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Save action completed (verification uncertain)"
                )

        except Exception as e:
            return EngagementResult(
                action=action,
                success=False,
                message=f"Save failed: {e}"
            )

    def _is_already_saved(self, strategy: SelectorStrategy) -> bool:
        """Check multiple indicators if post is already saved."""
        saved_indicators = [
            INSTAGRAM_SELECTORS["unsave_button"],
            ["button[aria-label*='Unsave']", "[data-testid*='unsave']"],
            [".saved", "svg[fill*='currentColor'][aria-label*='Saved']"]
        ]

        for indicator_set in saved_indicators:
            if strategy.find(indicator_set, timeout=1000):
                return True
        return False

    def _verify_save_success(self, strategy: SelectorStrategy) -> bool:
        """Robust verification of save action success."""
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                # Wait for UI updates
                wait_time = 1 + (attempt * 0.5)  # 1s, 1.5s, 2s
                self.page.wait_for_timeout(wait_time * 1000)

                # Method 1: Check for unsave button
                if strategy.find(INSTAGRAM_SELECTORS["unsave_button"], timeout=2000):
                    self._debug_log(f"Save verified via unsave button (attempt {attempt + 1})")
                    return True

                # Method 2: Check for visual indicators
                unsave_selectors = [
                    "button[aria-label*='Unsave']",
                    "[data-testid*='unsave']",
                    "svg[fill*='currentColor'][aria-label*='Saved']"
                ]

                for selector in unsave_selectors:
                    if self.page.is_visible(selector, timeout=1000):
                        self._debug_log(f"Save verified via visual indicator: {selector}")
                        return True

                # Method 3: Check if save button changed/disappeared
                if not strategy.find(INSTAGRAM_SELECTORS["save_button"], timeout=1000):
                    self._debug_log(f"Save verified via save button disappearance (attempt {attempt + 1})")
                    return True

                self._debug_log(f"Save verification attempt {attempt + 1} failed, retrying...")

            except Exception as e:
                self._debug_log(f"Save verification error on attempt {attempt + 1}: {e}")

        self._debug_log("All save verification attempts failed")
        return False

    def _perform_share(self, action: EngagementAction, strategy: SelectorStrategy) -> EngagementResult:
        """Perform share action on a post."""
        try:
            self._debug_log("Attempting to share post")

            share_method = action.metadata.get("method", "dm")

            # Find share button
            share_button = strategy.find(INSTAGRAM_SELECTORS["share_button_engage"], timeout=5000)
            if not share_button:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Share button not found"
                )

            # Click share button
            human_click(self.page, strategy.last_successful_selector)
            wait_human(self.page, 'click')

            if share_method == "dm":
                # Find DM option
                dm_button = strategy.find(INSTAGRAM_SELECTORS["dm_button"], timeout=5000)
                if not dm_button:
                    return EngagementResult(
                        action=action,
                        success=False,
                        message="DM button not found in share dialog"
                    )

                human_click(self.page, strategy.last_successful_selector)
                wait_human(self.page, 'click')

                # For now, just click the first user suggestion
                # In a real implementation, we'd need to select a specific user
                first_user = strategy.find(['div[role="button"]:has(img)'], timeout=5000)
                if first_user:
                    human_click(self.page, strategy.last_successful_selector)
                    wait_human(self.page, 'click')

                    # Click send button
                    send_button = strategy.find(['button:has-text("Send")', 'div:has-text("Senden")'], timeout=5000)
                    if send_button:
                        human_click(self.page, strategy.last_successful_selector)
                        wait_human(self.page, 'click')
                        return EngagementResult(
                            action=action,
                            success=True,
                            message="Post shared via DM successfully"
                        )

            return EngagementResult(
                action=action,
                success=False,
                message="Share method not implemented"
            )

        except Exception as e:
            return EngagementResult(
                action=action,
                success=False,
                message=f"Share failed: {e}"
            )

    # Public engagement methods
    def like_post(self, post_url: str) -> EngagementResult:
        """Like an Instagram post."""
        return self._execute_engagement_action(
            EngagementActionType.LIKE,
            post_url
        )

    def follow_user(self, username: str) -> EngagementResult:
        """Follow an Instagram user."""
        # Convert username to profile URL
        profile_url = f"https://www.instagram.com/{username}/"
        return self._execute_engagement_action(
            EngagementActionType.FOLLOW,
            profile_url
        )

    def comment_on_post(self, post_url: str, comment_text: str) -> EngagementResult:
        """Comment on an Instagram post."""
        return self._execute_engagement_action(
            EngagementActionType.COMMENT,
            post_url,
            {"comment_text": comment_text}
        )

    def save_post(self, post_url: str) -> EngagementResult:
        """Save an Instagram post."""
        return self._execute_engagement_action(
            EngagementActionType.SAVE,
            post_url
        )

    def share_post(self, post_url: str, method: str = "dm") -> EngagementResult:
        """Share an Instagram post."""
        return self._execute_engagement_action(
            EngagementActionType.SHARE,
            post_url,
            {"method": method}
        )

    def _respect_rate_limits(self, per_minute: int = 20, min_delay: float = 1.5, max_delay: float = 4.0) -> None:
        """
        Soft rate limiter to spread actions and reduce detection risk.
        """
        now = time.monotonic()
        # Ensure a small random pause between actions
        pause = random.uniform(min_delay, max_delay)
        time.sleep(pause)

        # Enforce per-minute window if close to limits
        recent = [t for t in self._action_timestamps if now - t < 60]
        if len(recent) >= per_minute:
            wait_for = 60 - (now - recent[0])
            if wait_for > 0:
                time.sleep(wait_for)

        self._action_timestamps.append(time.monotonic())
        # Trim old timestamps to keep memory small
        while self._action_timestamps and now - self._action_timestamps[0] > 60:
            self._action_timestamps.popleft()
