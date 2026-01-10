from playwright.sync_api import Browser, BrowserContext, Page
from radar.browser import BrowserManager

def test_browser_manager_initialization():
    with BrowserManager() as manager:
        assert manager is not None

def test_launch_browser():
    with BrowserManager() as manager:
        browser = manager.launch_browser()
        assert isinstance(browser, Browser)

def test_new_context():
    with BrowserManager() as manager:
        browser = manager.launch_browser()
        context = manager.new_context(browser)
        assert isinstance(context, BrowserContext)

def test_new_page():
    with BrowserManager() as manager:
        browser = manager.launch_browser()
        context = manager.new_context(browser)
        page = manager.new_page(context)
        assert isinstance(page, Page)

def test_context_with_options():
    with BrowserManager() as manager:
        browser = manager.launch_browser()
        user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
        context = manager.new_context(browser, user_agent=user_agent)
        page = manager.new_page(context)
        assert  page.evaluate("navigator.userAgent") == user_agent
