from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
from typing import Optional, Dict, Any

class BrowserManager:
    def __init__(self):
        self._playwright = None
        self._browser = None

    def __enter__(self):
        self._playwright = sync_playwright().start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def launch_browser(self, headless: bool = True, slow_mo: int = 0, **kwargs) -> Browser:
        if not self._playwright:
             raise RuntimeError("BrowserManager must be used as a context manager")
        # Default to chromium
        self._browser = self._playwright.chromium.launch(headless=headless, slow_mo=slow_mo, **kwargs)
        return self._browser

    def new_context(self, browser: Browser, **kwargs) -> BrowserContext:
        """
        Create a new browser context.
        Accepts standard Playwright context options like 'user_agent', 'viewport', etc.
        """
        return browser.new_context(**kwargs)

    def new_page(self, context: BrowserContext) -> Page:
        return context.new_page()
