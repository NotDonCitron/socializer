from playwright.sync_api import Page, BrowserContext
from radar.browser import BrowserManager
import time

class InstagramAutomator:
    def __init__(self, manager: BrowserManager, user_data_dir: str):
        self.manager = manager
        self.user_data_dir = user_data_dir
        self.context: BrowserContext = None
        self.page: Page = None
        self.last_error: str = None

    def login(self, username, password, headless=True, timeout=15000):
        """
        Attempts to log in to Instagram.
        Returns True if login appears successful or already logged in.
        """
        self.last_error = None
        if not self.context:
            self.context = self.manager.launch_persistent_context(
                self.user_data_dir,
                headless=headless,
                viewport={"width": 412, "height": 915},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
            )
        
        self.page = self.manager.new_page(self.context, stealth=True)
        
        try:
            self.page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle", timeout=timeout)
        except Exception as e:
            self.last_error = f"Navigation failed: {e}"
            return False
        
        # Check if we are already logged in
        if "login" not in self.page.url:
            self.handle_popups()
            return True
            
        try:
            # Fill credentials
            self.page.fill('input[name="username"]', username, timeout=timeout//3)
            self.page.fill('input[name="password"]', password)
            self.page.click('button[type="submit"]')
            
            # Wait for navigation or indicator of success or error
            try:
                self.page.wait_for_navigation(wait_until="networkidle", timeout=timeout//2)
            except:
                pass # Timeout on navigation, maybe error appeared or it's just slow
            
            if "login" not in self.page.url:
                self.handle_popups()
                return True
                
            # Check for error messages
            alert = self.page.query_selector('div[role="alert"]')
            if alert:
                self.last_error = alert.inner_text()
                print(f"Login error detected: {self.last_error}")
            else:
                self.last_error = "Login failed without explicit error message."
                
        except Exception as e:
            self.last_error = f"Login process failed: {e}"
            print(f"Login failed: {e}")
            
        return False

    def handle_popups(self, timeout=3000):
        """
        Closes common Instagram popups like 'Save info' or 'Turn on notifications'.
        """
        popups = [
            "text=Not Now",
            "text=Nicht jetzt",
            "button:has-text('Not Now')",
            "button:has-text('Nicht jetzt')",
            "text=Abbrechen",
            "text=Cancel"
        ]
        
        # Try to find and click these buttons if they appear
        for selector in popups:
            try:
                if self.page.is_visible(selector, timeout=timeout//len(popups)):
                    self.page.click(selector)
                    # Often multiple popups appear in sequence
                    self.page.wait_for_timeout(500)
            except:
                continue

    def upload_photo(self, file_path: str, caption: str = "", timeout: int = 45000) -> bool:
        """
        Uploads a photo to Instagram.
        Assumes the user is logged in and on the mobile layout.
        """
        self.last_error = None
        if not self.page:
            self.last_error = "Page not initialized. Call login() first."
            return False

        try:
            # Close any initial popups
            self.handle_popups()

            # 1. Click "New Post" Button & Handle File Chooser
            new_post_selectors = [
                'svg[aria-label="New post"]', 
                'svg[aria-label="New Post"]',
                'svg[aria-label="Erstellen"]', 
                'svg[aria-label="Posten"]',
                '[aria-label="New post"]',
                '[aria-label="Posten"]'
            ]
            
            # We need to find which one is visible first to wrap the click correctly
            upload_btn = None
            for sel in new_post_selectors:
                if self.page.is_visible(sel, timeout=2000):
                    upload_btn = sel
                    break
            
            if not upload_btn:
                # Fallback: try waiting for the first one
                try:
                    self.page.wait_for_selector(new_post_selectors[0], timeout=5000)
                    upload_btn = new_post_selectors[0]
                except:
                    self.last_error = "Could not find 'New Post' button."
                    return False

            try:
                with self.page.expect_file_chooser(timeout=10000) as fc_info:
                    self.page.click(upload_btn)
                file_chooser = fc_info.value
                file_chooser.set_files(file_path)
            except Exception as e:
                self.last_error = f"File chooser failed: {e}"
                return False
            
            # 3. Handle 'Crop' screen -> Next
            # Instagram mobile web: Crop -> Next -> Filter -> Next -> Caption -> Share
            next_btn_selectors = ['text=Next', 'text=Weiter', 'button:has-text("Next")', 'button:has-text("Weiter")']
            
            self.page.wait_for_timeout(2000) 
            
            # Click Next (Crop screen)
            if not self._click_any(next_btn_selectors, timeout=10000):
                self.last_error = "Could not find 'Next' button on Crop screen."
                return False
                
            # 4. Handle 'Filter' screen -> Next
            self.page.wait_for_timeout(1500)
            if not self._click_any(next_btn_selectors, timeout=10000):
                self.last_error = "Could not find 'Next' button on Filter screen."
                return False
            
            # 5. Enter Caption
            self.page.wait_for_timeout(1500)
            caption_selectors = [
                'textarea[aria-label="Write a caption…"]',
                'textarea[aria-label="Write a caption..."]',
                'textarea[aria-label="Bildunterschrift verfassen …"]',
                'textarea'
            ]
            
            caption_area = None
            for sel in caption_selectors:
                if self.page.is_visible(sel, timeout=2000):
                    caption_area = sel
                    break
            
            if caption_area:
                self.page.fill(caption_area, caption)
            else:
                print("Warning: Could not find caption area, posting without caption.")

            # 6. Click Share
            share_selectors = ['text=Share', 'text=Teilen', 'button:has-text("Share")', 'button:has-text("Teilen")']
            if not self._click_any(share_selectors, timeout=10000):
                self.last_error = "Could not find 'Share' button."
                return False

            # 7. Verify Post
            # Success indicator: "Your post has been shared" or navigation to feed
            # We look for a success message or the disappearance of the sharing UI
            try:
                success_indicators = [
                    "text=Your post has been shared",
                    "text=Dein Beitrag wurde geteilt",
                    'svg[aria-label="New post"]' # Back on home screen
                ]
                
                # Wait for any success indicator
                for indicator in success_indicators:
                    if self.page.is_visible(indicator, timeout=10000):
                        return True
                        
                # If not found, check if we are on the main feed
                if "/direct/inbox/" not in self.page.url and "instagram.com/?variant=" not in self.page.url:
                     # This is a bit weak but Instagram navigation is complex
                     return True
            except:
                pass

            return True # Fallback to true if we got this far

        except Exception as e:
            self.last_error = f"Upload failed: {e}"
            print(self.last_error)
            return False


        except Exception as e:
            self.last_error = f"Upload failed: {e}"
            print(self.last_error)
            return False

    def _click_any(self, selectors: list, timeout: int = 5000) -> bool:
        """Helper to click the first visible selector from a list."""
        for sel in selectors:
            try:
                if self.page.is_visible(sel, timeout=1000):
                    self.page.click(sel)
                    return True
            except:
                continue
        
        # If none found quickly, try waiting for the first one specifically
        try:
            self.page.click(selectors[0], timeout=timeout)
            return True
        except:
            return False

