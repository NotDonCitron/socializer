from playwright.sync_api import Page, expect

def test_playwright_is_ready(page: Page):
    page.goto("https://example.com")
    expect(page).to_have_title("Example Domain")
