from radar.browser import BrowserManager
import pytest

def test_stealth_mode_enabled():
    """
    Test that stealth mode hides webdriver property.
    """
    with BrowserManager() as manager:
        browser = manager.launch_browser(headless=True)
        context = manager.new_context(browser)
        
        # Enable stealth
        page = manager.new_page(context, stealth=True)
        
        # Navigate to ensure init scripts run (though they should run on about:blank too, but safer)
        page.goto("data:text/html,<html><body></body></html>")

        # Check if navigator.webdriver is false/undefined
        is_webdriver = page.evaluate("navigator.webdriver")
        assert not is_webdriver, "navigator.webdriver should be false/undefined in stealth mode"

def test_user_agent_rotation():
    """
    Test that we can rotate user agents.
    """
    ua1 = "Mozilla/5.0 (Test UA 1)"
    ua2 = "Mozilla/5.0 (Test UA 2)"
    
    with BrowserManager() as manager:
        browser = manager.launch_browser(headless=True)
        
        # Context 1
        context1 = manager.new_context(browser, user_agent=ua1)
        page1 = manager.new_page(context1)
        assert page1.evaluate("navigator.userAgent") == ua1
        
        # Context 2
        context2 = manager.new_context(browser, user_agent=ua2)
        page2 = manager.new_page(context2)
        assert page2.evaluate("navigator.userAgent") == ua2
