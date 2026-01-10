"""
Multi-strategy selector system for robust element finding.

Provides fallback chains to handle TikTok/Instagram UI changes gracefully.
Priority: data-e2e → aria-label → CSS partial → text content → XPath
"""
from typing import List, Optional, Callable
from playwright.sync_api import Page, ElementHandle


# TikTok Upload Page Selectors
TIKTOK_SELECTORS = {
    "file_input": [
        'input[type="file"]',
        'input[accept*="video"]',
        'input[name*="upload"]',
    ],
    "caption_area": [
        'div[contenteditable="true"][data-e2e*="caption"]',
        'div[contenteditable="true"]',
        'textarea[placeholder*="caption" i]',
        'textarea[placeholder*="describe" i]',
        'textarea',
    ],
    "post_button": [
        # TikTok Studio specific
        'button[data-e2e="post_video_button"]',
        'button[data-e2e="post-button"]',
        'button[data-e2e="submit-button"]',
        'div[data-e2e="post_video_button"]',
        # Primary/Submit buttons (TikTok Studio often uses these)
        'button[class*="TUXButton--primary"]:has-text("Post")',
        'button[class*="TUXButton--primary"]:has-text("Submit")',
        'button[class*="primary"]:has-text("Post")',
        'button[class*="submit"]',
        # Text-based selectors
        'button:has-text("Post")',
        'button:has-text("Submit")',
        'button:has-text("Publish")',
        'button:has-text("Veröffentlichen")',  # German
        'button:has-text("Posten")',  # German
        'button:has-text("Absenden")',  # German for Submit
        # Aria labels
        'button[aria-label*="Post" i]',
        'button[aria-label*="Submit" i]',
        # Class-based fallbacks
        'button[class*="post-btn"]',
        'button[class*="post_btn"]',
        'button[class*="PostButton"]',
        # Last resort: any visible primary button at bottom
        'div[class*="footer"] button[class*="primary"]',
    ],
    "confirmation_button": [
        'button:has-text("TikTok.com")',  # Red button in dialog "Continue to post?"
        'button:has-text("Continue")',
        'button:has-text("Weiter")',
        'button[class*="confirm"]',
        'div[class*="modal"] button[class*="primary"]',
        'div[class*="dialog"] button[class*="primary"]',
    ],
    "upload_complete": [
        '[data-e2e="upload-complete"]',
        '[class*="upload-success"]',
        '[class*="preview-ready"]',
        'div[class*="thumbnail"]:not([class*="loading"])',
    ],
    "loading_indicator": [
        '[class*="loading"]',
        '[class*="spinner"]',
        '[class*="progress"]',
        'svg[class*="loading"]',
        'div:has-text("Uploading")',
        'div:has-text("Processing")',
    ],
    "processing_complete": [
        'div:has-text("Copyright check complete")',
        'div:has-text("Run a copyright check")', # Means it's ready to run, so upload is done
        'div[class*="success"]',
        'div[class*="progress"] [style*="width: 100%"]',
    ],
    "tour_overlay": [
        'div[id="react-joyride-portal"]',
        '[class*="joyride"]',
        '[class*="tour"]',
        '[class*="onboarding"]',
    ],
    "post_success_dialog": [
        '[class*="SuccessModal"]',
        '[class*="SuccessContainer"]',
        'div:has-text("Your video has been uploaded")',
        'div:has-text("Video wurde hochgeladen")', # German
        'div:has-text("Manage your video")',
        'div:has-text("Manage your videos")',
        'div:has-text("Videos verwalten")', # German
    ],
    "dismiss_button": [
        'button[class*="dismiss"]',
        'button[class*="close"]',
        'button[aria-label="Close"]',
        'svg[class*="close"]',
    ],
    "cookie_banner": [
        'tiktok-cookie-banner',
        'button:has-text("Allow all")',
        'button:has-text("Accept all")',
        'button:has-text("Alle akzeptieren")',
        'button:has-text("Decline all")', # Sometimes safer to decline if 'Allow' fails
        'button:has-text("Alle ablehnen")',
        'div[class*="cookie-banner"] button[class*="primary"]',
    ],
}

# Instagram Selectors
INSTAGRAM_SELECTORS = {
    "file_input": [
        'input[type="file"]',
        'input[accept*="image"]',
    ],
    "new_post_button": [
        'svg[aria-label="New reel"]',
        'svg[aria-label="Neuer Reel"]',
        'svg[aria-label*="reel" i]',
        'svg[aria-label="New post"]',
        'svg[aria-label="Create"]',
        'svg[aria-label="Neuer Beitrag"]',  # German
        'svg[aria-label="Erstellen"]',  # German
        'svg[aria-label*="post" i]',
        'svg[aria-label*="create" i]',
        '[data-testid="new-post-button"]',
        'div[role="button"]:has-text("Create")',
        'div[role="button"]:has-text("New post")',
        'div[role="button"]:has-text("Erstellen")',
        'div[role="button"]:has-text("Neuer Beitrag")',
        'div[role="link"]:has-text("Create")',
        'div[role="link"]:has-text("New post")',
        'div[role="link"]:has-text("Erstellen")',
        'div[role="link"]:has-text("Neuer Beitrag")',
        'a[role="link"]:has-text("Create")',
        'a[role="link"]:has-text("Erstellen")',
        'div[role="button"]:has-text("Reel")',
        'div[role="button"]:has-text("Neuer Reel")',
        'span:has-text("Create")',
        'span:has-text("New post")',
        'span:has-text("Erstellen")',
        'span:has-text("Neuer Beitrag")',
    ],
        'span:has-text("Reel")',
    "next_button": [
        'button[data-testid="next-button"]',
        '[data-testid="next-button"]',
        '[role="button"]:has-text("Next")',
        '[role="button"]:has-text("Weiter")',
        'div:has-text("Next")[role="button"]',
        'div:has-text("Weiter")[role="button"]',
        'button:has-text("Next")',
        'button:has-text("Weiter")',
        '[aria-label="Next"]',
    ],
    "caption_area": [
        'textarea[aria-label="Write a caption..."]',
        'textarea[aria-label*="caption" i]',
        'textarea[placeholder*="caption" i]',
        'div[contenteditable="true"]',
        'textarea',
    ],
    "share_button": [
        'button[data-testid="share-button"]',
        '[data-testid="share-button"]',
        'button:has-text("Share")',
        'button:has-text("Post")',
        'button:has-text("Teilen")',
    ],
    "success_indicator": [
        'text="Your reel has been shared"',
        'text="Dein Reel wurde geteilt"',
        'text="Your post has been shared"',
        'text="Dein Beitrag wurde geteilt"',
        'h2:has-text("shared")',
        'svg[aria-label="Animated checkmark"]'
    ],
    "search_button": [
        'svg[aria-label="Search"]',
        'svg[aria-label="Suche"]',
        'a[href="/explore/search/"]',
        'div[role="link"]:has-text("Search")',
        'div[role="link"]:has-text("Suche")',
        'span:has-text("Search")',
        'span:has-text("Suche")',
    ],
    "search_input": [
        'input[placeholder="Search"]',
        'input[placeholder="Suche"]',
        'input[aria-label="Search input"]',
        'input[aria-label*="Search" i]',
        'input[aria-label*="Suche" i]',
    ],
    "search_results_container": [
        'div[role="dialog"]',
        'div[role="menu"]',
        'div[aria-label*="Results" i]',
        'div[aria-label*="Ergebnisse" i]',
    ],
    "follow_button": [
        'button:has-text("Follow")',
        'button:has-text("Follow Back")',
        'button:has-text("Folgen")',
        'button:has-text("Zurückfolgen")',
        'div[role="button"]:has-text("Follow")',
        'div[role="button"]:has-text("Folgen")',
    ],
    "following_button": [
        'button:has-text("Following")',
        'button:has-text("Requested")',
        'button:has-text("Abonniert")',
        'button:has-text("Angefragt")',
        'div[role="button"]:has-text("Following")',
        'div[role="button"]:has-text("Requested")',
    ],
    "like_button": [
        'svg[aria-label="Like"]',
        'span[aria-label="Like"]',
        'button[aria-label="Like"]',
        'svg[aria-label="Gefällt mir"]',
        'svg[aria-label="Gefallt mir"]',
        'button[aria-label*="Like" i]',
    ],
    "liked_button": [
        'svg[aria-label="Unlike"]',
        'span[aria-label="Unlike"]',
        'button[aria-label="Unlike"]',
        'svg[aria-label="Gefällt mir nicht mehr"]',
        'svg[aria-label="Gefallt mir nicht mehr"]',
    ],
    "comment_box": [
        'textarea[aria-label*="Add a comment" i]',
        'textarea[placeholder*="Add a comment" i]',
        'textarea[aria-label*="Kommentar" i]',
    ],
    "comment_post_button": [
        'button:has-text("Post")',
        'button:has-text("Publish")',
        'button:has-text("Posten")',
        'button:has-text("Veröffentlichen")',
    ],
    "private_account": [
        'h2:has-text("This account is private")',
        'h2:has-text("This Account is Private")',
        'span:has-text("This account is private")',
        'h2:has-text("Dieses Konto ist privat")',
        'span:has-text("Dieses Konto ist privat")',
    ],
    "profile_post_link": [
        'article a[href*="/p/"]',
        'article a[href*="/reel/"]',
    ],
}


class SelectorStrategy:
    """
    Finds elements using a prioritized list of selectors with fallbacks.
    """
    
    def __init__(self, page: Page, timeout: int = 5000):
        """
        Initialize with a Playwright page.
        
        Args:
            page: Playwright Page object
            timeout: Default timeout for selector waits in ms
        """
        self.page = page
        self.timeout = timeout
        self.last_successful_selector: Optional[str] = None
    
    def find(
        self, 
        selectors: List[str], 
        state: str = "visible",
        timeout: Optional[int] = None
    ) -> Optional[ElementHandle]:
        """
        Try each selector in order until one finds an element.
        
        Args:
            selectors: List of CSS/XPath selectors to try
            state: Element state to wait for ('visible', 'attached', 'hidden')
            timeout: Override default timeout
            
        Returns:
            ElementHandle if found, None otherwise
        """
        timeout = timeout or self.timeout
        per_selector_timeout = max(500, timeout // len(selectors))
        
        for selector in selectors:
            try:
                element = self.page.wait_for_selector(
                    selector, 
                    state=state, 
                    timeout=per_selector_timeout
                )
                if element:
                    self.last_successful_selector = selector
                    return element
            except Exception:
                continue
        
        return None
    
    def find_any_visible(self, selectors: List[str]) -> Optional[ElementHandle]:
        """
        Find the first visible element from the selector list.
        
        Unlike find(), this doesn't wait - checks current state immediately.
        
        Args:
            selectors: List of selectors to check
            
        Returns:
            First visible ElementHandle, or None
        """
        for selector in selectors:
            try:
                if self.page.is_visible(selector):
                    element = self.page.query_selector(selector)
                    if element:
                        self.last_successful_selector = selector
                        return element
            except Exception:
                continue
        
        return None
    
    def wait_for_any(
        self, 
        selectors: List[str], 
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        Wait for any of the selectors to match, return the first one that does.
        
        Args:
            selectors: List of selectors to wait for
            timeout: Maximum wait time
            
        Returns:
            The selector that matched, or None if timeout
        """
        timeout = timeout or self.timeout
        
        # Create a race condition - first selector to match wins
        js_check = """
        (selectors) => {
            for (const sel of selectors) {
                try {
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent !== null) return sel;
                } catch (e) {}
            }
            return null;
        }
        """
        
        import time
        start = time.time()
        while (time.time() - start) * 1000 < timeout:
            result = self.page.evaluate(js_check, selectors)
            if result:
                self.last_successful_selector = result
                return result
            self.page.wait_for_timeout(100)
        
        return None
    
    def is_any_visible(self, selectors: List[str]) -> bool:
        """
        Check if any of the selectors are visible.
        
        Args:
            selectors: List of selectors to check
            
        Returns:
            True if any selector matches a visible element
        """
        for selector in selectors:
            try:
                if self.page.is_visible(selector):
                    return True
            except Exception:
                continue
        return False
    
    def click_first_visible(
        self, 
        selectors: List[str], 
        force: bool = False
    ) -> bool:
        """
        Click the first visible element from the selector list.
        
        Args:
            selectors: List of selectors to try
            force: Force click even if element is obscured
            
        Returns:
            True if clicked successfully, False otherwise
        """
        element = self.find_any_visible(selectors)
        if element:
            try:
                element.click(force=force)
                return True
            except Exception:
                pass
        return False


def find_tiktok_element(page: Page, element_type: str, **kwargs) -> Optional[ElementHandle]:
    """
    Convenience function to find TikTok elements.
    
    Args:
        page: Playwright Page object
        element_type: Key from TIKTOK_SELECTORS dict
        **kwargs: Additional args for SelectorStrategy.find()
        
    Returns:
        ElementHandle if found
    """
    selectors = TIKTOK_SELECTORS.get(element_type, [])
    if not selectors:
        raise ValueError(f"Unknown TikTok element type: {element_type}")
    
    strategy = SelectorStrategy(page)
    return strategy.find(selectors, **kwargs)


def find_instagram_element(page: Page, element_type: str, **kwargs) -> Optional[ElementHandle]:
    """
    Convenience function to find Instagram elements.
    
    Args:
        page: Playwright Page object
        element_type: Key from INSTAGRAM_SELECTORS dict
        **kwargs: Additional args for SelectorStrategy.find()
        
    Returns:
        ElementHandle if found
    """
    selectors = INSTAGRAM_SELECTORS.get(element_type, [])
    if not selectors:
        raise ValueError(f"Unknown Instagram element type: {element_type}")
    
    strategy = SelectorStrategy(page)
    return strategy.find(selectors, **kwargs)
