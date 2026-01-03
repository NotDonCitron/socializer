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
            return True
            
        try:
            # Fill credentials
            self.page.fill('input[name="username"]', username, timeout=timeout//3)
            self.page.fill('input[name="password"]', password)
            self.page.click('button[type="submit"]')
            
            # Wait for navigation or indicator of success or error
            # We look for either navigation away from login OR an error message
            
            # Instagram often shows error in a div with role="alert"
            # We'll wait for either navigation or the alert to appear
            
            # This is a bit tricky with sync API without threading/wait_for_selector(timeout)
            # We'll try to wait for navigation with a shorter timeout and then check for alerts
            try:
                self.page.wait_for_navigation(wait_until="networkidle", timeout=timeout//2)
            except:
                pass # Timeout on navigation, maybe error appeared or it's just slow
            
            if "login" not in self.page.url:
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

