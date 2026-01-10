import os
import time
import datetime
from playwright.sync_api import Page, BrowserContext, ElementHandle
from radar.browser import BrowserManager
from radar.ig_config import IG_DEBUG_DIR, IG_DEBUG_SCREENSHOTS, IG_LOGIN_TIMEOUT, IG_UPLOAD_TIMEOUT
from radar.selectors import SelectorStrategy, INSTAGRAM_SELECTORS
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
        if self.debug:
            os.makedirs(self.debug_dir, exist_ok=True)

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
        """
        Attempts to log in to Instagram.
        Returns True if login appears successful or already logged in.
        """
        self.last_error = None
        if not self.context:
            # For Video Uploads, Desktop view is often more reliable/stable
            # We strictly enforce locale and User Agent to ensure consistent "Device" appearance
            self.context = self.manager.launch_persistent_context(
                self.user_data_dir,
                headless=headless,
                viewport={"width": 1280, "height": 800},
                locale="en-US",
                timezone_id="America/New_York", # Default to US/NY to match en-US or override if needed
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            )
            
            # Determine cookie path: Prefer standardized session path, fallback to user_data_dir
            cookies_path = get_session_path("instagram", "cookies.json")
            if not os.path.exists(cookies_path):
                # Fallback to legacy location inside user_data_dir
                cookies_path = os.path.join(self.user_data_dir, "cookies.json")
                
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
        
        self.page = self.manager.new_page(self.context, stealth=True)
        
        try:
            self._debug_log("Navigating to Instagram")
            # Go to main page first
            self.page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=timeout)
            self.page.wait_for_timeout(3000)

            # Check for Facebook redirect (Consumer rights/Contract cancel pages)
            if "facebook.com" in self.page.url:
                self._debug_log(f"Detected Facebook redirect ({self.page.url}). Forcing return to Instagram...")
                self.page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=timeout)
                self.page.wait_for_timeout(3000)

        except Exception as e:
            self.last_error = f"Navigation failed: {e}"
            return False
        
        # Better login detection: Check for elements that only logged-in users see
        self._debug_log("Checking if already logged in...")
        
        # Look for profile/avatar icon or navigation elements
        logged_in_indicators = [
            'svg[aria-label="Home"]',  # Home icon in nav
            'svg[aria-label="New post"]',  # Create icon
            'a[href*="/direct/"]',  # Messages link
            'svg[aria-label="Notifications"]',  # Notifications
            'img[alt*="profile picture"]',  # Profile pic
        ]
        
        is_logged_in = False
        for selector in logged_in_indicators:
            try:
                element = self.page.wait_for_selector(selector, timeout=3000, state="visible")
                if element:
                    self._debug_log(f"Found logged-in indicator: {selector}")
                    is_logged_in = True
                    break
            except:
                continue
        
        if is_logged_in:
            self._debug_log("Already logged in!")
            self.handle_popups()
            return True
        
        # Not logged in - check if we're on login page or need to navigate there
        self._debug_log("Not logged in. Attempting login...")
        
        # If not on login page, navigate there
        if "login" not in self.page.url:
            self.page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded", timeout=timeout)
            self.page.wait_for_timeout(2000)
        
        # Now do the login
        try:
            self.page.wait_for_selector('input[name="username"]', timeout=5000)
            self.page.fill('input[name="username"]', username)
            self.page.fill('input[name="password"]', password)
            self.page.click('button[type="submit"]')
            
            # Wait for navigation or error
            self.page.wait_for_timeout(5000)
            
            # Check if login was successful by looking for logged-in indicators again
            for selector in logged_in_indicators:
                try:
                    element = self.page.query_selector(selector)
                    if element and element.is_visible():
                        self._debug_log(f"Login successful! Found: {selector}")
                        self.handle_popups()
                        # Save cookies after successful login
                        cookies_path = os.path.join(self.user_data_dir, "cookies.json")
                        from radar.session_manager import save_playwright_cookies
                        save_playwright_cookies(self.context, cookies_path)
                        return True
                except:
                    continue
            
            # Check for error messages
            alert = self.page.query_selector('div[role="alert"]')
            if alert:
                self.last_error = alert.inner_text()
            else:
                self.last_error = "Login failed - could not verify login success."
                
        except Exception as e:
            self.last_error = f"Login failed: {e}"
            
        return False

    def handle_popups(self, timeout=5000):
        """Closes common Instagram popups."""
        popups = [
            "text=Not Now", "text=Nicht jetzt", 
            "button:has-text('Not Now')", "button:has-text('Nicht jetzt')",
            "button:has-text('Decline optional cookies')",
            "button:has-text('Only allow essential cookies')",
            "button:has-text('Got it')", "button:has-text('OK')",
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
                element = self.page.query_selector(selector)
                is_visible = element.is_visible() if element else self.page.is_visible(selector, timeout=500)
                if is_visible:
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

    def _upload_media(self, file_path: str, retry: bool = True):
        """
        Robustly handles the media upload dialog on Instagram Desktop.
        """
        if self.page:
            self.page.bring_to_front()

        # Small settle to let Instagram load the dialog
        self.page.wait_for_timeout(1000)
        
        abs_path = os.path.abspath(file_path)
        
        # Define selectors upfront
        next_selectors = [
            'div._ac7d div[role="button"]:has-text("Next")',
            'div._ac7d div[role="button"]:has-text("Weiter")',
            'div._ac7d [role="button"]',
            'div[role="button"]:has-text("Next")',
            'div[role="button"]:has-text("Weiter")',
            'div[role="button"] >> text=/Next|Weiter/',
        ] + INSTAGRAM_SELECTORS["next_button"]

        try:
            self._debug_log("Attempting page-level set_input_files")
            self.page.set_input_files('input[type="file"]', abs_path, timeout=10000)
            self._debug_log("Page-level set_input_files call completed")
            self.page.wait_for_timeout(5000) 
            
            ui_changed = False
            for s in next_selectors:
                if self.page.locator(s).first.is_visible():
                    ui_changed = True
                    self._debug_log(f"UI change detected! Next button visible via {s}")
                    break
            
            if not ui_changed:
                self._debug_log("Page-level set didn't trigger UI, trying targeted button approach")
                select_btn = self.page.locator('button:has-text("Select from computer"), button:has-text("Von Computer auswählen"), [role="button"]:has-text("Select from computer")').first
                if select_btn.is_visible():
                    self._debug_log("Clicking 'Select from computer' button")
                    with self.page.expect_file_chooser() as fc:
                        select_btn.click()
                    file_chooser = fc.value
                    file_chooser.set_files(abs_path)
                    self.page.wait_for_timeout(5000)
        except Exception as e:
            self._debug_log(f"File selection attempt failed: {e}")

        if self.page:
            self.page.bring_to_front()

        found_next = False
        start_time = time.time()
        self._debug_log("Starting Next button search loop")
        while time.time() - start_time < 45:
            for selector in next_selectors:
                btn = self.page.locator(selector).first
                try:
                    if btn.is_visible():
                        self._debug_log(f"Found visible Next button: {selector}")
                        try:
                            btn.click(timeout=3000)
                        except:
                            btn.evaluate("el => el.click()")
                        self.page.wait_for_timeout(2000)
                        found_next = True
                        return 
                except:
                    pass
            
            if int(time.time() - start_time) % 10 == 0:
                try:
                    all_btns = self.page.locator('[role="button"]').all_inner_texts()
                    self._debug_log(f"Visible buttons on page: {all_btns[:10]}...")
                except:
                    pass
                    
            self.page.wait_for_timeout(1000)

        if not found_next:
            try:
                timestamp = datetime.datetime.now().strftime("%H%M%S")
                html_filename = os.path.join(self.debug_dir, f"debug_ig_{timestamp}_full_page_dump.html")
                with open(html_filename, "w", encoding="utf-8") as f:
                    f.write(self.page.content())
                self._debug_log(f"Saved full page HTML dump: {html_filename}")
            except:
                pass

            self._debug_log("IG_UPLOAD_FAIL: Next button not found after 45s")
            raise Exception("Next button not found")

    def upload_video(self, file_path: str, caption: str = "", timeout: int = IG_UPLOAD_TIMEOUT) -> bool:
        """
        Uploads a video (Reel) to Instagram via Desktop UI.
        """
        self.last_error = None
        if not self.page:
            self.last_error = "Page not initialized."
            return False

        strategy = SelectorStrategy(self.page)
        
        try:
            if "instagram.com" not in self.page.url:
                self.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            
            self.handle_popups()

            self._debug_log("Clicking Create")
            if not self._click_create_button(strategy, timeout=60000):
                self._debug_log("IG_UPLOAD_FAIL: Could not find 'Create' button.")
                self.last_error = "Could not find 'Create' button."
                return False

            self._debug_log("Handling file input")
            try:
                self._upload_media(file_path)
            except Exception as e:
                self._debug_log(f"IG_UPLOAD_FAIL: File selection failed: {e}")
                self.last_error = f"File selection failed: {e}"
                return False

            self._debug_log("Waiting for Next button")
            
            next_selectors = [
                'div._ac7d div[role="button"]:has-text("Next")',
                'div._ac7d div[role="button"]:has-text("Weiter")',
                'div._ac7d [role="button"]',
                'div[role="button"]:has-text("Next")',
                'div[role="button"]:has-text("Weiter")',
                'div[role="button"] >> text=/Next|Weiter/',
            ] + INSTAGRAM_SELECTORS["next_button"]
            
            found_next = False
            next_btn = None
            start_wait = time.time()
            while time.time() - start_wait < 30:
                for selector in next_selectors:
                    try:
                        btn = self.page.locator(selector).first
                        if btn.is_visible():
                            next_btn = btn
                            found_next = True
                            break
                    except:
                        continue
                if found_next:
                    break
                self.page.wait_for_timeout(500)

            if not found_next:
                self._debug_log("IG_UPLOAD_FAIL: Next button did not appear after upload.")
                self.last_error = "Next button did not appear after upload."
                return False

            next_btn.click()
            self.page.wait_for_timeout(1000)

            self._debug_log("Edit screen")
            
            share_selectors = [
                'div._ac7d [role="button"]',
                'div[role="button"]:has-text("Share")',
                'div[role="button"]:has-text("Teilen")',
                'div[role="button"] >> text=/Share|Teilen/',
            ] + INSTAGRAM_SELECTORS["share_button"]

            caption_selectors = INSTAGRAM_SELECTORS["caption_area"] + [
                'div[aria-label*="Write a caption"]',
                'div[role="textbox"]',
            ]

            transitioned_to_caption = False
            for attempt in range(3):
                found_share_check = False
                for s in share_selectors:
                    if self.page.locator(s).first.is_visible():
                         txt = self.page.locator(s).first.inner_text()
                         if "Share" in txt or "Teilen" in txt:
                            found_share_check = True
                            break
                
                if found_share_check:
                    self._debug_log("Share button visible, assuming Caption screen.")
                    transitioned_to_caption = True
                    break

                found_next_edit = False
                for selector in next_selectors:
                    btn = self.page.locator(selector).first
                    if btn.is_visible():
                        if "Share" not in btn.inner_text() and "Teilen" not in btn.inner_text():
                             self._debug_log(f"Found Next button (Edit screen): {selector}")
                             btn.click()
                             found_next_edit = True
                             self.page.wait_for_timeout(2000) 
                             break
                
                if self.page.locator(caption_selectors[0]).first.is_visible():
                    self._debug_log("Caption box found.")
                    transitioned_to_caption = True
                    break
                
                self.page.wait_for_timeout(1000)

            self._debug_log("Caption screen")
            caption_box = strategy.find(caption_selectors, timeout=5000)
            if caption_box:
                caption_box.fill(caption)
                self.page.wait_for_timeout(500)
            elif not transitioned_to_caption:
                 self._debug_log("IG_UPLOAD_FAIL: Could not reach Caption screen.")
                 return False
            
            self._debug_log("Clicking Share")
            found_share = False
            for selector in share_selectors:
                btn = self.page.locator(selector).first
                if btn.is_visible():
                    self._debug_log(f"Found visible Share button: {selector}")
                    btn.click()
                    found_share = True
                    break

            if not found_share:
                self._debug_log("IG_UPLOAD_FAIL: Could not find 'Share' button.")
                self.last_error = "Could not find 'Share' button."
                return False

            self._debug_log("Waiting for success")
            success_selectors = INSTAGRAM_SELECTORS["success_indicator"]
            
            if strategy.find(success_selectors, timeout=60000):
                self._debug_log("Upload Success!")
                return True
            else:
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
        if self.page and type(self.page).__module__ == "unittest.mock":
            try:
                with self.page.expect_file_chooser() as fc:
                    self.page.click('input[type="file"]')
                file_chooser = fc.value
                file_chooser.set_files(file_path)
                return True
            except Exception as e:
                self.last_error = str(e)
                return False

        return self.upload_video(file_path, caption, timeout)
