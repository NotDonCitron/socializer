import os
import re
import time
import datetime
from urllib.parse import quote
from playwright.sync_api import Page, BrowserContext, ElementHandle
from radar.browser import BrowserManager
from radar.human_behavior import human_delay, typing_delay, thinking_pause_chance
from radar.ig_config import (
    IG_DEBUG_DIR,
    IG_DEBUG_SCREENSHOTS,
    IG_LOGIN_TIMEOUT,
    IG_UPLOAD_TIMEOUT,
    IG_MIN_ACTION_DELAY,
    IG_MAX_ACTION_DELAY,
    IG_SEARCH_MAX_RESULTS,
    IG_SEARCH_MAX_SCROLLS,
    IG_MAX_SEARCHES_PER_HOUR,
    IG_MAX_FOLLOWS_PER_HOUR,
    IG_MAX_LIKES_PER_HOUR,
    IG_MAX_COMMENTS_PER_HOUR,
    IG_SKIP_PRIVATE,
    IG_ALLOWED_USERNAME_PREFIXES,
)
from radar.ig_selectors import SelectorStrategy, INSTAGRAM_SELECTORS
from radar.session_manager import load_playwright_cookies, get_session_path

class InstagramAutomator:
    def __init__(self, manager: BrowserManager, user_data_dir: str):
        self.manager = manager
        self.user_data_dir = user_data_dir
        self.context: BrowserContext = None
        self.page: Page = None
        self.last_error: str = None
        self.debug = IG_DEBUG_SCREENSHOTS
        self.debug_dir = IG_DEBUG_DIR
        self.action_counts = {}
        self.action_window_start = time.time()
        if self.debug:
            os.makedirs(self.debug_dir, exist_ok=True)

    def _launch_context(self, headless: bool):
        self.context = self.manager.launch_persistent_context(
            self.user_data_dir,
            headless=headless,
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            timezone_id="America/New_York",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )

        cookies_path = get_session_path("instagram", "cookies.json")
        if not os.path.exists(cookies_path):
            cookies_path = os.path.join(self.user_data_dir, "cookies.json")
        load_playwright_cookies(self.context, path=cookies_path)

        def abort_and_log(route):
            if self.debug:
                print(f"[DEBUG] Aborted request: {route.request.url}")
            route.abort()

        self.context.route("**/facebook.com/help/cancelcontracts**", abort_and_log)
        self.context.route("**/help/cancelcontracts?source=instagram.com**", abort_and_log)
        self.context.route("**/help.instagram.com/**", abort_and_log)
        self.context.route("**/transparency.fb.com/**", abort_and_log)
        self.context.on("page", self._handle_new_page)

    def _ensure_page(self):
        # Simplified check to avoid AttributeError on is_closed
        if not self.context:
            self._launch_context(headless=False)
        
        # Verify context is alive by accessing pages property
        try:
            _ = self.context.pages
        except Exception:
            self.context = None
            self._launch_context(headless=False)

        # Handle page
        if self.page:
            try:
                if self.page.is_closed():
                    self.page = None
            except Exception:
                self.page = None
                
        if not self.page:
            self.page = self.manager.new_page(self.context, stealth=True)

    def _debug_log(self, message: str):
        if self.debug:
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            print(f"[DEBUG] {message}")
            if self.page:
                # Sanitize message for filename: strip newlines, remove bad chars
                clean_msg = message.split('\n')[0] # Only take first line
                safe_msg = "".join([c if c.isalnum() or c in " _-" else "_" for c in clean_msg])
                safe_msg = safe_msg.replace(' ', '_').lower()[:30]
                
                filename = os.path.join(self.debug_dir, f"debug_ig_{timestamp}_{safe_msg}.png")
                try:
                    self.page.screenshot(path=filename)
                    print(f"[DEBUG] Saved screenshot: {filename}")
                except Exception as e:
                    print(f"[DEBUG] Failed to save screenshot: {e}")
                    pass

    def _rate_limit(self, action: str, max_per_hour: int) -> bool:
        if max_per_hour <= 0:
            return True

        now = time.time()
        if now - self.action_window_start >= 3600:
            self.action_window_start = now
            self.action_counts = {}

        count = self.action_counts.get(action, 0)
        if count >= max_per_hour:
            self.last_error = f"Rate limit reached for {action} ({max_per_hour}/hour)"
            return False

        self.action_counts[action] = count + 1
        return True

    def _sleep_action(self):
        delay_ms = int(human_delay(IG_MIN_ACTION_DELAY, IG_MAX_ACTION_DELAY))
        if self.page:
            self.page.wait_for_timeout(delay_ms)

    def _parse_prefixes(self, prefixes: list[str] | None) -> list[str]:
        if prefixes is not None:
            raw = prefixes
        else:
            raw = [p for p in IG_ALLOWED_USERNAME_PREFIXES.split(",") if p.strip()]

        return [p.strip().lower() for p in raw if p.strip()]

    def _matches_prefix(self, username: str, prefixes: list[str]) -> bool:
        if not prefixes:
            return True
        uname = username.lower()
        return any(uname.startswith(p) for p in prefixes)

    def _extract_username(self, href: str) -> str | None:
        if not href:
            return None

        match = re.match(r"^/([A-Za-z0-9._]+)/$", href)
        if not match:
            return None

        username = match.group(1)
        reserved = {
            "explore", "reels", "reel", "p", "accounts", "tags", "direct",
            "about", "help", "privacy", "terms", "challenge", "graphql",
        }
        if username.lower() in reserved:
            return None

        return username

    def _collect_search_results(self, container_selector: str) -> list[dict]:
        data = self.page.evaluate(
            """
            (selector) => {
                const root = document.querySelector(selector);
                if (!root) return [];
                const anchors = Array.from(root.querySelectorAll('a[href]'));
                return anchors.map(a => ({
                    href: a.getAttribute('href'),
                    text: (a.innerText || '').trim()
                }));
            }
            """,
            container_selector,
        )

        results = []
        seen = set()
        for item in data:
            href = item.get("href") or ""
            username = self._extract_username(href)
            if not username or username in seen:
                continue

            display_name = None
            text = item.get("text") or ""
            if text:
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                if lines:
                    if lines[0].lower() != username.lower():
                        display_name = lines[0]
                    elif len(lines) > 1:
                        display_name = lines[1]

            results.append(
                {
                    "username": username,
                    "display_name": display_name,
                    "profile_url": f"https://www.instagram.com/{username}/",
                }
            )
            seen.add(username)

        return results

    def _open_search_ui(self, strategy: SelectorStrategy) -> bool:
        if strategy.click_first_visible(INSTAGRAM_SELECTORS["search_button"]):
            self._sleep_action()
            return True
        return False

    def _open_profile(self, username: str) -> bool:
        if not username:
            self.last_error = "Username is empty."
            return False

        self._ensure_page()
        if not self.page:
            self.last_error = "Page not initialized."
            return False

        profile_url = f"https://www.instagram.com/{username}/"
        self.page.goto(profile_url, wait_until="domcontentloaded")
        self.page.wait_for_timeout(1500)
        return True

    def _is_private_account(self, strategy: SelectorStrategy) -> bool:
        return strategy.is_any_visible(INSTAGRAM_SELECTORS["private_account"])

    def _open_first_post(self, strategy: SelectorStrategy) -> bool:
        post_link = strategy.find_any_visible(INSTAGRAM_SELECTORS["profile_post_link"])
        if not post_link:
            self.last_error = "No posts found on profile."
            return False

        try:
            post_link.click()
            self.page.wait_for_timeout(1500)
            return True
        except Exception as e:
            self.last_error = f"Failed to open post: {e}"
            return False

    def search_accounts(
        self,
        query: str,
        max_results: int = IG_SEARCH_MAX_RESULTS,
        max_scrolls: int = IG_SEARCH_MAX_SCROLLS,
    ) -> list[dict]:
        """
        Search Instagram accounts by keyword using the UI.

        Returns a list of dicts: {username, display_name, profile_url}.
        """
        self.last_error = None
        if not query or not query.strip():
            self.last_error = "Search query is empty."
            return []

        if not self._rate_limit("search", IG_MAX_SEARCHES_PER_HOUR):
            return []

        self._ensure_page()
        if not self.page:
            self.last_error = "Page not initialized."
            return []

        if "instagram.com" not in self.page.url:
            self.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")

        self.handle_popups()
        strategy = SelectorStrategy(self.page)

        input_el = None
        if self._open_search_ui(strategy):
            input_el = strategy.find(INSTAGRAM_SELECTORS["search_input"], timeout=5000)

        if not input_el:
            search_url = f"https://www.instagram.com/explore/search/keyword/?q={quote(query)}"
            self.page.goto(search_url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(1500)
            input_el = strategy.find(INSTAGRAM_SELECTORS["search_input"], timeout=5000)

        if not input_el:
            self.last_error = "Search input not found."
            return []

        input_el.click()
        self.page.wait_for_timeout(150)
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")

        for char in query.strip():
            self.page.keyboard.type(char)
            self.page.wait_for_timeout(int(typing_delay()))
            if thinking_pause_chance():
                self.page.wait_for_timeout(300)

        self.page.wait_for_timeout(800)

        container_selector = None
        for selector in INSTAGRAM_SELECTORS["search_results_container"]:
            try:
                if self.page.is_visible(selector):
                    container_selector = selector
                    break
            except Exception:
                continue

        if not container_selector:
            container_selector = "body"

        results = []
        seen = set()
        for _ in range(max_scrolls + 1):
            chunk = self._collect_search_results(container_selector)
            for item in chunk:
                if len(results) >= max_results:
                    break
                username = item["username"]
                if username not in seen:
                    results.append(item)
                    seen.add(username)

            if len(results) >= max_results:
                break

            try:
                self.page.evaluate(
                    "(selector) => { const el = document.querySelector(selector); if (el) el.scrollBy(0, el.scrollHeight); }",
                    container_selector,
                )
            except Exception:
                self.page.mouse.wheel(0, 800)

            self._sleep_action()

        return results[:max_results]

    def follow_user(
        self,
        username: str,
        prefixes: list[str] | None = None,
        skip_private: bool = IG_SKIP_PRIVATE,
    ) -> bool:
        self.last_error = None
        allowed = self._parse_prefixes(prefixes)
        if not self._matches_prefix(username, allowed):
            self.last_error = "Username does not match allowed prefixes."
            return False

        if not self._open_profile(username):
            return False

        self.handle_popups()
        strategy = SelectorStrategy(self.page)

        if skip_private and self._is_private_account(strategy):
            self.last_error = "Skipped private account."
            return False

        if strategy.is_any_visible(INSTAGRAM_SELECTORS["following_button"]):
            return True

        if not self._rate_limit("follow", IG_MAX_FOLLOWS_PER_HOUR):
            return False

        if strategy.click_first_visible(INSTAGRAM_SELECTORS["follow_button"]):
            self._sleep_action()
            return True

        self.last_error = "Follow button not found."
        return False

    def like_recent_post(
        self,
        username: str,
        prefixes: list[str] | None = None,
        skip_private: bool = IG_SKIP_PRIVATE,
    ) -> bool:
        self.last_error = None
        allowed = self._parse_prefixes(prefixes)
        if not self._matches_prefix(username, allowed):
            self.last_error = "Username does not match allowed prefixes."
            return False

        if not self._open_profile(username):
            return False

        self.handle_popups()
        strategy = SelectorStrategy(self.page)

        if skip_private and self._is_private_account(strategy):
            self.last_error = "Skipped private account."
            return False

        if not self._open_first_post(strategy):
            return False

        if strategy.is_any_visible(INSTAGRAM_SELECTORS["liked_button"]):
            return True

        if not self._rate_limit("like", IG_MAX_LIKES_PER_HOUR):
            return False

        if strategy.click_first_visible(INSTAGRAM_SELECTORS["like_button"]):
            self._sleep_action()
            return True

        self.last_error = "Like button not found."
        return False

    def comment_recent_post(
        self,
        username: str,
        comment_text: str,
        prefixes: list[str] | None = None,
        skip_private: bool = IG_SKIP_PRIVATE,
    ) -> bool:
        self.last_error = None
        allowed = self._parse_prefixes(prefixes)
        if not self._matches_prefix(username, allowed):
            self.last_error = "Username does not match allowed prefixes."
            return False

        if not comment_text or not comment_text.strip():
            self.last_error = "Comment text is empty."
            return False

        if not self._open_profile(username):
            return False

        self.handle_popups()
        strategy = SelectorStrategy(self.page)

        if skip_private and self._is_private_account(strategy):
            self.last_error = "Skipped private account."
            return False

        if not self._open_first_post(strategy):
            return False

        comment_box = strategy.find(INSTAGRAM_SELECTORS["comment_box"], timeout=5000)
        if not comment_box:
            self.last_error = "Comment box not found."
            return False

        if not self._rate_limit("comment", IG_MAX_COMMENTS_PER_HOUR):
            return False

        comment_box.click()
        self.page.wait_for_timeout(150)
        for char in comment_text.strip():
            self.page.keyboard.type(char)
            self.page.wait_for_timeout(int(typing_delay()))
            if thinking_pause_chance():
                self.page.wait_for_timeout(300)

        if strategy.click_first_visible(INSTAGRAM_SELECTORS["comment_post_button"]):
            self._sleep_action()
            return True

        self.page.keyboard.press("Enter")
        self._sleep_action()
        return True

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

    def login(self, username, password, headless=True, timeout=IG_LOGIN_TIMEOUT):
        """Unified login method using SeleniumBase for bridge if needed."""
        if not self.context:
            self._launch_context(headless)
        
        if not self.page:
            self.page = self.manager.new_page(self.context, stealth=True)

        self.last_error = None
        
        # 1. Quick check if already logged in via stored cookies
        try:
            self._debug_log("Checking if already logged in via Playwright...")
            self.page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=timeout)
            self.handle_popups()
            
            from radar.session_manager import validate_instagram_session
            check = validate_instagram_session(self.page)
            
            if check['valid']:
                self._debug_log(f"Session verified (Playwright): {check['reason']}")
                return True
        except Exception as e:
            self._debug_log(f"Initial session check failed: {e}")

        self._debug_log(f"Session invalid/missing. Launching SeleniumBase Stealth Bridge...")
        
        # 2. Use SeleniumBase to refresh cookies
        from radar.auth_bridge_ig import sb_login
        # Ensure we run in the same headless mode
        success = sb_login(username=username, password=password, headless=headless)
        
        if success:
            self._debug_log("SeleniumBase Bridge login succeeded. Reloading Playwright context...")
            # Close existing context and page to reload with new cookies
            self.context.close()
            # Launch again - it will pick up the new cookies in _launch_context
            self._launch_context(headless)
            self.page = self.manager.new_page(self.context, stealth=True)
            
            self.page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=timeout)
            self.handle_popups()
            
            from radar.session_manager import validate_instagram_session
            check = validate_instagram_session(self.page)
            if check['valid']:
                 self._debug_log("Session bridged successfully to Playwright!")
                 return True
            else:
                 self.last_error = f"Session still invalid after bridge: {check['reason']}"
                 self._debug_log(self.last_error)
                 return False
        else:
            self.last_error = "SeleniumBase Bridge login failed."
            self._debug_log(self.last_error)
            return False

    def handle_popups(self, timeout=5000):
        """Closes common Instagram/Facebook popups, including those in frames."""
        popups = INSTAGRAM_SELECTORS.get("popups", []) # Fallback if list not updated
        # [I will keep the inline list for now to be sure]
        popups = [
            "text=Not Now", "text=Nicht jetzt", 
            "button:has-text('Not Now')", "button:has-text('Nicht jetzt')",
            "button[data-cookiebanner='accept_button']",
            "button[data-testid='cookie-policy-manage-dialog-accept-button']",
            "button:has-text('Allow all cookies')",
            "button:has-text('Alle Cookies erlauben')",
            "button:has-text('Alles akzeptieren')",
            "button:has-text('Allow Essential and Optional Cookies')",
            "button:has-text('Decline optional cookies')",
            "button:has-text('Only allow essential cookies')",
            "button:has-text('Nur essenzielle Cookies erlauben')",
            "button:has-text('Optionalen Cookies widersprechen')",
            "button:has-text('Got it')", "button:has-text('OK')",
            "button:has-text('Verstanden')",
            "[aria-label='Close']", "[aria-label='Schließen']",
            "button[aria-label='Close']", 
            "div[role='button']:has-text('Not Now')",
            "div[role='button']:has-text('Nicht jetzt')",
            "div[role='dialog'] button:has-text('OK')", # Generic dialog OK
            "div[role='dialog'] button:has-text('Done')",
            "text=New! separate tabs", # Feature discovery
            "text=Neu! separate Tabs"
        ]
        
        for selector in popups:
            try:
                # Check main page
                element = self.page.query_selector(selector)
                if element and element.is_visible():
                    self._debug_log(f"Closing popup: {selector}")
                    element.click(timeout=2000)
                    self.page.wait_for_timeout(500)
                
                # Check all frames
                for frame in self.page.frames:
                    if frame == self.page.main_frame:
                        continue
                    element = frame.query_selector(selector)
                    if element and element.is_visible():
                        self._debug_log(f"Closing popup in frame: {selector}")
                        element.click(timeout=2000)
                        self.page.wait_for_timeout(500)
            except Exception as e:
                continue

    def _click_create_button(self, strategy: SelectorStrategy, timeout: int = 15000) -> bool:
        """
        Waits for the Create/New Post button to be clickable with multiple fallbacks.
        Retries while clearing popups that can obscure the sidebar.
        """
        create_selectors = INSTAGRAM_SELECTORS["new_post_button"] + [
            'div[role="button"][aria-label*="Create" i]',
            'button[aria-label*="Create" i]',
            'button:has-text("Create")',
            'button:has-text("Erstellen")',
        ]
        create_selectors = list(dict.fromkeys(create_selectors))

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

    def _find_clickable(self, selectors: list[str]) -> ElementHandle | None:
        """Helper to find the first visible, clickable element from a list."""
        for s in selectors:
            try:
                 el = self.page.locator(s).first
                 if el.is_visible():
                     return el
            except:
                continue
        return None

    def _upload_media(self, file_path: str, caption: str):
        """
        State-driven upload handler.
        Navigates: File Selection -> Next/Filter -> Next/Edit -> Share -> Success
        """
        self._ensure_page()
        if self.page:
            self.page.bring_to_front()
        
        abs_path = os.path.abspath(file_path)
        
        # 1. File Selection Phase
        print(f"[TRACE] Attempting file selection for {abs_path}")
        try:
            # Try to find a file input that belongs to the modal
            file_input = self.page.locator('div[role="dialog"] input[type="file"]').first
            if not file_input.count():
                file_input = self.page.locator('input[type="file"]').first
                
            if file_input:
                file_input.set_input_files(abs_path)
            else:
                self.page.set_input_files('input[type="file"]', abs_path, timeout=5000)
            print("[TRACE] File selection called.")
            self.page.wait_for_timeout(3000)
        except Exception as e:
            print(f"[TRACE] File selection error: {e}")

        # If file selection didn't trigger (we are still on "Select from computer" or similar)
        select_btns = [
             'button:has-text("Select from computer")',
             'button:has-text("Von Computer auswählen")',
             '[role="button"]:has-text("Select from computer")',
             'div[role="button"] >> text=/Select.*computer/i'
        ]
        
        # Check if we are still on the "Select" screen
        if self._find_clickable(select_btns) or self.page.is_visible('text="Drag photos and videos here"'):
             self._debug_log("Still on Select screen, attempting fallback click...")
             btn = self._find_clickable(select_btns)
             if btn:
                 try:
                     with self.page.expect_file_chooser(timeout=5000) as fc:
                         btn.click(force=True)
                     fc.value.set_files(abs_path)
                     print("[TRACE] File chooser fallback success")
                     self.page.wait_for_timeout(3000)
                 except Exception as e:
                     print(f"[TRACE] File chooser fallback failed: {e}")

        # 2. Infinite State Loop (Next -> Share)
        # We loop until we see "Success" or timeout
        start_time = time.time()
        max_duration = 120 # 2 minutes total for upload flow
        caption_filled = False
        
        next_selectors = [
            'button:has-text("Next")',
            'button:has-text("Weiter")',
            'button:has-text("OK")',
            'button:has-text("Alle akzeptieren")',
            'div._ac7d div[role="button"]:has-text("Next")',
            'div[role="button"]:has-text("Next")',
            'div[role="button"]:has-text("Weiter")',
            'div[role="button"]:has-text("OK")',
        ]
        
        share_selectors = [
            'button:has-text("Share")',
            'button:has-text("Teilen")',
            'div[role="button"]:has-text("Share")',
            'div[role="button"]:has-text("Teilen")',
        ]
        
        # Expanders for accessibility/advanced settings that might block visibility
        expander_selectors = [
             'button:has-text("Accessibility")',
             'div[role="button"]:has-text("Accessibility")',
             'div[role="button"]:has-text("Barrierefreiheit")',
             'div[role="button"]:has-text("Advanced settings")',
             'div[role="button"]:has-text("Erweiterte Einstellungen")',
        ]
        
        caption_selectors = [
            'div[aria-label="Write a caption..."]',
            'div[aria-label="Verfasse eine Bildunterschrift ..."]',
            'div[role="textbox"][contenteditable="true"]',
            'textarea[aria-label="Write a caption..."]',
             'textarea[aria-label*="caption"]'
        ]

        success_indicators = [
             'text="Post shared"', 'text="Beitrag geteilt"',
             'text="Your post has been shared"',
             'img[alt="Animated checkmark"]',
             'svg[aria-label="Success"]'
        ]

        self._debug_log("Starting State-Driven Upload Loop")
        
        while time.time() - start_time < max_duration:
            # A. Check Success
            if self._find_clickable(success_indicators) or self.page.is_visible('text="Reel shared"'):
                self._debug_log("Upload Success Detected!")
                return True

            # B. Check Share Button (Final Step)
            share_btn = self._find_clickable(share_selectors)
            if share_btn:
                # If we see Share, we are on the final screen. Fill caption if needed.
                if not caption_filled and caption:
                    self._debug_log("On Share screen, filling caption...")
                    cb = self._find_clickable(caption_selectors)
                    if cb:
                        try:
                            cb.click()
                            cb.fill(caption)
                            caption_filled = True
                            self.page.wait_for_timeout(500)
                        except:
                            pass
                
                self._debug_log("Clicking Share button...")
                try:
                    share_btn.click()
                    self.page.wait_for_timeout(3000) # Wait for network
                    continue # Loop back to check success
                except Exception as e:
                    self._debug_log(f"Share click failed: {e}")

            # C. Check Next Buttons (Intermediate Steps)
            # Only click next if Share is NOT visible (handled above)
            next_btn = self._find_clickable(next_selectors)
            if next_btn:
                 self._debug_log("Found Next button, advancing...")
                 try:
                     next_btn.click()
                     self.page.wait_for_timeout(1000)
                     continue
                 except:
                     pass

            # D. Handle Blocking Expanders or Errors
            if self.page.is_visible('text="Only images can be posted"') or self.page.is_visible('text="Nur Bilder können gepostet werden"'):
                 self._debug_log("Critical Error: Only images can be posted for this account.")
                 self.last_error = "Platform restriction: Only images can be posted."
                 return False
            
            # E. Check for "Success" close button (if missed main text)
            close_btn = self._find_clickable(['button:has-text("Close")', 'button:has-text("Schließen")'])
            if close_btn and (self.page.is_visible('text="shared"') or self.page.is_visible('text="geteilt"')):
                 self._debug_log("Found Close button on success text.")
                 return True

            # Periodic Trace (every 5 seconds)
            if time.time() - start_time > 5 and int(time.time() - start_time) % 5 == 0:
                 try:
                     bts = self.page.locator('button, [role="button"]').all_inner_texts()
                     print(f"[TRACE] Visible buttons: {bts}")
                     self._debug_log(f"Stuck? Visible buttons: {bts}")
                     
                     timestamp = datetime.datetime.now().strftime("%H%M%S")
                     with open(os.path.join(self.debug_dir, f"debug_ig_{timestamp}_stuck_dump.html"), "w", encoding="utf-8") as f:
                         f.write(self.page.content())
                 except: pass

            self.page.wait_for_timeout(1000)
            
        self.last_error = "Upload timed out (State Loop exhausted)"
        return False

    def upload_video(self, file_path: str, caption: str = "", timeout: int = IG_UPLOAD_TIMEOUT) -> bool:
        """
        Uploads a video (Reel) to Instagram or Photo.
        """
        self.last_error = None
        self._ensure_page()
        if not self.page:
            self.last_error = "Page not initialized."
            return False

        strategy = SelectorStrategy(self.page)
        
        try:
            if "instagram.com" not in self.page.url:
                self.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            
            self.handle_popups()

            self._debug_log("Opening create flow via UI button")
            # Ensure we are on home or a page with the sidebar
            if not self._click_create_button(strategy):
                # Fallback to direct URL if button click fails, but log it
                self._debug_log("Create button click failed, falling back to direct URL (risky)")
                self.page.goto("https://www.instagram.com/create/select/", wait_until="domcontentloaded")
            
            self.page.wait_for_timeout(2000)
            
            # Use state machine for the rest
            return self._upload_media(file_path, caption)

        except Exception as e:
            self.last_error = str(e)
            return False

    def upload_photo(self, file_path: str, caption: str = "", timeout: int = 45000) -> bool:
         return self.upload_video(file_path, caption, timeout)
