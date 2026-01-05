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
    # Engagement selectors
    "like_button": [
        'svg[data-e2e="like-icon"]',
        'button[data-e2e="like-button"]',
        'svg[aria-label*="Like" i]',
        'div[data-e2e*="like"]',
        'button:has(svg[data-e2e="like-icon"])',
    ],
    "unlike_button": [
        'svg[data-e2e="liked-icon"]',
        'button[data-e2e="like-button"][data-e2e*="liked"]',
        'div[data-e2e*="liked"]',
    ],
    "comment_button": [
        'svg[data-e2e="comment-icon"]',
        'button[data-e2e="comment-button"]',
        'svg[aria-label*="Comment" i]',
        'div[data-e2e*="comment"]',
    ],
    "share_button_engage": [
        'svg[data-e2e="share-icon"]',
        'button[data-e2e="share-button"]',
        'svg[aria-label*="Share" i]',
        'div[data-e2e*="share"]',
    ],
    "save_button": [
        'svg[data-e2e="collect-icon"]',
        'button[data-e2e="collect-button"]',
        'svg[aria-label*="Save" i]',
        'div[data-e2e*="collect"]',
    ],
    "unsave_button": [
        'svg[data-e2e="collected-icon"]',
        'button[data-e2e="collect-button"][data-e2e*="collected"]',
        'div[data-e2e*="collected"]',
    ],
    "follow_button": [
        'button[data-e2e="follow-button"]',
        'button:has-text("Follow")',
        'button:has-text("Folgen")',  # German
        'div[data-e2e*="follow"]',
    ],
    "unfollow_button": [
        'button[data-e2e="following-button"]',
        'button:has-text("Following")',
        'button:has-text("Abonniert")',  # German
        'div[data-e2e*="following"]',
    ],
    "comment_input": [
        'textarea[data-e2e="comment-input"]',
        'div[contenteditable="true"][data-e2e*="comment"]',
        'textarea[placeholder*="Add comment" i]',
        'textarea[placeholder*="Kommentar hinzufügen" i]',  # German
    ],
    "post_comment_button": [
        'button[data-e2e="comment-post"]',
        'button:has-text("Post")',
        'button:has-text("Kommentieren")',  # German
    ],
    "duet_button": [
        'button[data-e2e="duet-button"]',
        'svg[data-e2e="duet-icon"]',
        'div[data-e2e*="duet"]',
    ],
    "stitch_button": [
        'button[data-e2e="stitch-button"]',
        'svg[data-e2e="stitch-icon"]',
        'div[data-e2e*="stitch"]',
    ],
    "live_comment_input": [
        'input[data-e2e="live-comment-input"]',
        'textarea[data-e2e="live-comment-input"]',
        'div[contenteditable="true"][data-e2e*="live-comment"]',
    ],
}

# Instagram Selectors
INSTAGRAM_SELECTORS = {
    "file_input": [
        'input[type="file"]',
        'input[accept*="image"]',
    ],
    "new_post_button": [
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
        'span:has-text("Create")',
        'span:has-text("New post")',
        'span:has-text("Erstellen")',
        'span:has-text("Neuer Beitrag")',
    ],
    "next_button": [
        'button:has-text("Next")',
        'button:has-text("Weiter")',
        '[aria-label="Next"]',
    ],
    "caption_area": [
        'textarea[aria-label*="caption" i]',
        'textarea[placeholder*="caption" i]',
        'div[contenteditable="true"]',
        'textarea',
    ],
    "share_button": [
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
    # Engagement selectors
    "like_button": [
        'svg[aria-label="Like"]',
        'svg[aria-label="Gefällt mir"]',  # German
        'button[aria-label*="Like" i]',
        'button[aria-label*="Gefällt" i]',
        'span[data-visualcompletion="ignore-dynamic"]:has(svg[aria-label="Like"])',
        'div[role="button"]:has(svg[aria-label="Like"])',
    ],
    "unlike_button": [
        'svg[aria-label="Unlike"]',
        'svg[aria-label="Gefällt mir nicht mehr"]',  # German
        'button[aria-label*="Unlike" i]',
        'span[data-visualcompletion="ignore-dynamic"]:has(svg[aria-label="Unlike"])',
    ],
    "comment_button": [
        'svg[aria-label="Comment"]',
        'svg[aria-label="Kommentieren"]',  # German
        'button[aria-label*="Comment" i]',
        'div[role="button"]:has(svg[aria-label="Comment"])',
    ],
    "share_button_engage": [
        'svg[aria-label="Share"]',
        'svg[aria-label="Teilen"]',  # German
        'button[aria-label*="Share" i]',
        'div[role="button"]:has(svg[aria-label="Share"])',
    ],
    "save_button": [
        'svg[aria-label="Save"]',
        'svg[aria-label="Speichern"]',  # German
        'button[aria-label*="Save" i]',
        'div[role="button"]:has(svg[aria-label="Save"])',
    ],
    "unsave_button": [
        'svg[aria-label="Remove"]',
        'svg[aria-label="Entfernen"]',  # German
        'button[aria-label*="Remove" i]',
        'div[role="button"]:has(svg[aria-label="Remove"])',
    ],
    "follow_button": [
        'button:has-text("Follow")',
        'button:has-text("Folgen")',  # German
        'div[role="button"]:has-text("Follow")',
        'div[role="button"]:has-text("Folgen")',
    ],
    "unfollow_button": [
        'button:has-text("Following")',
        'button:has-text("Abonniert")',  # German
        'div[role="button"]:has-text("Following")',
        'button:has-text("Unfollow")',
        'button:has-text("Entfolgen")',  # German
    ],
    "comment_input": [
        'textarea[aria-label*="Add a comment"]',
        'textarea[placeholder*="Add a comment" i]',
        'textarea[placeholder*="Kommentar hinzufügen" i]',  # German
        'div[contenteditable="true"][aria-label*="comment" i]',
    ],
    "post_comment_button": [
        'button:has-text("Post")',
        'button:has-text("Kommentieren")',  # German
        'div[role="button"]:has-text("Post")',
    ],
    "story_ring": [
        'div[role="button"]:has(img)',
        'canvas',  # Story ring canvas
        'div[class*="story-ring"]',
    ],
    "dm_button": [
        'svg[aria-label="Direct message"]',
        'svg[aria-label="Direktnachricht"]',  # German
        'button[aria-label*="Direct" i]',
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