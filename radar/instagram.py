from playwright.sync_api import Page, BrowserContext
from radar.browser import BrowserManager
import time

class InstagramAutomator:
    def __init__(self, manager: BrowserManager, user_data_dir: str):
        self.manager = manager
        self.user_data_dir = user_data_dir
        self.context: BrowserContext = None
        self.page: Page = None

    def login(self, username, password, headless=True):
        """
        Attempts to log in to Instagram.
        Returns True if login appears successful or already logged in.
        """
        if not self.context:
            self.context = self.manager.launch_persistent_context(
                self.user_data_dir,
                headless=headless,
                viewport={"width": 412, "height": 915},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
            )
        
        self.page = self.manager.new_page(self.context, stealth=True)
        
        self.page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle")
        
        # Check if we are already logged in
        if "login" not in self.page.url:
            return True
            
        try:
            # Fill credentials
            self.page.fill('input[name="username"]', username, timeout=5000)
            self.page.fill('input[name="password"]', password)
            self.page.click('button[type="submit"]')
            
            # Wait for navigation or indicator of success
            # Instagram often has a "Save Your Login Info?" prompt
            self.page.wait_for_navigation(wait_until="networkidle", timeout=15000)
            
            if "login" not in self.page.url:
                return True
        except Exception as e:
            print(f"Login failed: {e}")
            
        return False
