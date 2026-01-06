"""
 TikTok automation module with advanced anti-detection and retry logic.
"""
from typing import Optional
import random
import time
import os
import datetime
from collections import deque
from playwright.sync_api import Page, BrowserContext
from radar.browser import BrowserManager
from radar.element_selectors import SelectorStrategy, TIKTOK_SELECTORS
from radar.human_behavior import human_delay, human_type, human_click, wait_human
from radar.session_manager import validate_tiktok_session, load_playwright_cookies
from radar.engagement_models import EngagementAction, EngagementResult, EngagementActionType, EngagementPlatform, EngagementStatus
from radar.session_orchestrator import SessionOrchestrator, SessionContext, EngagementPlatform as OrchestratorPlatform

class TikTokAutomator:
    """
    TikTok upload automation with anti-detection measures.

    Features:
    - Human-like interaction patterns
    - Multi-strategy selectors with fallbacks
    - Retry logic with exponential backoff
    - Session validation and shadowban detection
    - Integration with SessionOrchestrator for multi-account support
    """

    def __init__(self, session_context: Optional[SessionContext] = None, account_id: Optional[str] = None):
        """
        Initialize TikTok automator.

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
            self.user_data_dir = f"data/sessions/tiktok/{account_id}" if account_id else "data/tiktok_session"
            os.makedirs(self.user_data_dir, exist_ok=True)

    def login(self, username=None, password=None, headless=False, timeout=30000):
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
                randomize=True,  # Use randomized viewport/UA
            )
            # Try to load SeleniumBase cookies if available
            load_playwright_cookies(self.context)

        # Create page if not exists
        if not self.page:
            self.page = self.manager.new_page(self.context, stealth=True)

        try:
            print("Browser context launched. Navigating to TikTok...")
            self.page.goto("https://www.tiktok.com/upload", wait_until="domcontentloaded", timeout=timeout)
            wait_human(self.page, 'navigate')

            validation = validate_tiktok_session(self.page)
            if validation['valid']:
                print(f"Session valid: {validation['reason']}")
                # Update session persistence if using orchestrator
                if self.session_context and self.session_context.session_data:
                    from radar.session_persistence import SessionPersistence
                    persistence = SessionPersistence()
                    persistence.update_login_status(self.account_id, True, True)
                return True

            print(f"Session invalid: {validation['reason']}")
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

    def _navigate_to_video(self, video_url: str) -> bool:
        """Navigate to a specific TikTok video."""
        try:
            print(f"Navigating to video: {video_url}")
            self.page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
            self.page.wait_for_timeout(3000)  # Wait for video to load
            self._dismiss_overlays()
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
            platform=EngagementPlatform.TIKTOK,
            target_identifier=target_identifier,
            metadata=metadata or {}
        )

        try:
            # Navigate to target if it's a URL
            if target_identifier.startswith(('http://', 'https://')):
                if not self._navigate_to_video(target_identifier):
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
        """Perform like action on a TikTok video."""
        try:
            print("Attempting to like video")

            # Try to find like button
            like_button = strategy.find(TIKTOK_SELECTORS["like_button"], timeout=5000)
            if not like_button:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Like button not found"
                )

            # Check if already liked
            unlike_button = strategy.find(TIKTOK_SELECTORS["unlike_button"], timeout=1000)
            if unlike_button:
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Video already liked"
                )

            # Click like button with human-like behavior
            human_click(self.page, strategy.last_successful_selector)
            wait_human(self.page, 'click')

            # Verify like was successful
            unlike_button = strategy.find(TIKTOK_SELECTORS["unlike_button"], timeout=3000)
            if unlike_button:
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Video liked successfully"
                )
            else:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Could not verify like action"
                )

        except Exception as e:
            return EngagementResult(
                action=action,
                success=False,
                message=f"Like failed: {e}"
            )

    def _perform_follow(self, action: EngagementAction, strategy: SelectorStrategy) -> EngagementResult:
        """Perform follow action on a TikTok creator."""
        try:
            print("Attempting to follow creator")

            # Try to find follow button
            follow_button = strategy.find(TIKTOK_SELECTORS["follow_button"], timeout=5000)
            if not follow_button:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Follow button not found"
                )

            # Check if already following
            unfollow_button = strategy.find(TIKTOK_SELECTORS["unfollow_button"], timeout=1000)
            if unfollow_button:
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Already following creator"
                )

            # Click follow button with human-like behavior
            human_click(self.page, strategy.last_successful_selector)
            wait_human(self.page, 'click')

            # Verify follow was successful
            unfollow_button = strategy.find(TIKTOK_SELECTORS["unfollow_button"], timeout=3000)
            if unfollow_button:
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Creator followed successfully"
                )
            else:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Could not verify follow action"
                )

        except Exception as e:
            return EngagementResult(
                action=action,
                success=False,
                message=f"Follow failed: {e}"
            )

    def _perform_comment(self, action: EngagementAction, strategy: SelectorStrategy) -> EngagementResult:
        """Perform comment action on a TikTok video."""
        try:
            print("Attempting to comment on video")

            comment_text = action.metadata.get("comment_text", "")
            if not comment_text:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="No comment text provided"
                )

            # Find comment button
            comment_button = strategy.find(TIKTOK_SELECTORS["comment_button"], timeout=5000)
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
            comment_input = strategy.find(TIKTOK_SELECTORS["comment_input"], timeout=5000)
            if not comment_input:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Comment input not found"
                )

            # Type comment with human-like behavior
            human_type(self.page, strategy.last_successful_selector, comment_text)
            wait_human(self.page, 'type')

            # Find and click post button
            post_button = strategy.find(TIKTOK_SELECTORS["post_comment_button"], timeout=5000)
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
        """Perform save action on a TikTok video."""
        try:
            print("Attempting to save video")

            # Try to find save button
            save_button = strategy.find(TIKTOK_SELECTORS["save_button"], timeout=5000)
            if not save_button:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Save button not found"
                )

            # Check if already saved
            unsave_button = strategy.find(TIKTOK_SELECTORS["unsave_button"], timeout=1000)
            if unsave_button:
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Video already saved"
                )

            # Click save button with human-like behavior
            human_click(self.page, strategy.last_successful_selector)
            wait_human(self.page, 'click')

            # Verify save was successful
            unsave_button = strategy.find(TIKTOK_SELECTORS["unsave_button"], timeout=3000)
            if unsave_button:
                return EngagementResult(
                    action=action,
                    success=True,
                    message="Video saved successfully"
                )
            else:
                return EngagementResult(
                    action=action,
                    success=False,
                    message="Could not verify save action"
                )

        except Exception as e:
            return EngagementResult(
                action=action,
                success=False,
                message=f"Save failed: {e}"
            )

    def _perform_share(self, action: EngagementAction, strategy: SelectorStrategy) -> EngagementResult:
        """Perform share action on a TikTok video."""
        try:
            print("Attempting to share video")

            share_method = action.metadata.get("method", "dm")

            # Find share button
            share_button = strategy.find(TIKTOK_SELECTORS["share_button_engage"], timeout=5000)
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
                dm_button = strategy.find(['button:has-text("Message")', 'button:has-text("Nachricht")'], timeout=5000)
                if not dm_button:
                    return EngagementResult(
                        action=action,
                        success=False,
                        message="DM button not found in share dialog"
                    )

                human_click(self.page, strategy.last_successful_selector)
                wait_human(self.page, 'click')

                # For now, just click the first user suggestion
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
                            message="Video shared via DM successfully"
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
    def like_video(self, video_url: str) -> EngagementResult:
        """Like a TikTok video."""
        return self._execute_engagement_action(
            EngagementActionType.LIKE,
            video_url
        )

    def follow_creator(self, username: str) -> EngagementResult:
        """Follow a TikTok creator."""
        # Convert username to profile URL
        profile_url = f"https://www.tiktok.com/@{username}"
        return self._execute_engagement_action(
            EngagementActionType.FOLLOW,
            profile_url
        )

    def comment_on_video(self, video_url: str, comment_text: str) -> EngagementResult:
        """Comment on a TikTok video."""
        return self._execute_engagement_action(
            EngagementActionType.COMMENT,
            video_url,
            {"comment_text": comment_text}
        )

    def save_video(self, video_url: str) -> EngagementResult:
        """Save a TikTok video."""
        return self._execute_engagement_action(
            EngagementActionType.SAVE,
            video_url
        )

    def share_video(self, video_url: str, method: str = "dm") -> EngagementResult:
        """Share a TikTok video."""
        return self._execute_engagement_action(
            EngagementActionType.SHARE,
            video_url,
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
