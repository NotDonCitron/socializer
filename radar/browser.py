from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
from typing import Optional, Dict, Any, List
from playwright_stealth import Stealth
import random
from radar.fingerprint_generator import FingerprintGenerator, BrowserFingerprint


# Anti-detection browser arguments
ANTI_DETECTION_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--disable-infobars',
    '--disable-extensions',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-web-security',
    '--disable-features=VizDisplayCompositor',
]

# Common desktop user agents (2025)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# Mobile user agents (for Instagram)
MOBILE_USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
]


class BrowserManager:
    """
    Enhanced browser manager with anti-detection measures.
    
    Features:
    - Anti-detection browser flags
    - Stealth mode with playwright-stealth
    - Proxy support per context
    - Randomized viewport and user agent
    """
    
    def __init__(self):
        self._playwright = None
        self._browser = None
        self._stealth_engine = Stealth()

    def __enter__(self):
        self._playwright = sync_playwright().start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def _get_browser_args(self, extra_args: Optional[List[str]] = None) -> List[str]:
        """Get combined anti-detection and custom browser args."""
        args = ANTI_DETECTION_ARGS.copy()
        if extra_args:
            args.extend(extra_args)
        return args

    def _randomize_viewport(self) -> Dict[str, int]:
        """Generate a randomized but realistic viewport size."""
        widths = [1366, 1440, 1536, 1600, 1920]
        heights = [768, 900, 864, 900, 1080]
        idx = random.randint(0, len(widths) - 1)
        return {'width': widths[idx], 'height': heights[idx]}

    def get_random_user_agent(self, mobile: bool = False) -> str:
        """Get a random user agent string."""
        agents = MOBILE_USER_AGENTS if mobile else USER_AGENTS
        return random.choice(agents)

    def launch_browser(
        self, 
        headless: bool = True, 
        slow_mo: int = 0,
        proxy: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Browser:
        """
        Launch browser with anti-detection measures.
        
        Args:
            headless: Run in headless mode (False recommended for social media)
            slow_mo: Slow down operations by this many ms
            proxy: Proxy config dict with 'server', optional 'username', 'password'
            **kwargs: Additional Playwright launch options
        """
        if not self._playwright:
            raise RuntimeError("BrowserManager must be used as a context manager")
        
        args = self._get_browser_args(kwargs.pop('args', None))
        
        launch_options = {
            'headless': headless,
            'slow_mo': slow_mo,
            'args': args,
            **kwargs
        }
        
        if proxy:
            launch_options['proxy'] = proxy
        
        self._browser = self._playwright.chromium.launch(**launch_options)
        return self._browser

    def new_context(
        self, 
        browser: Browser,
        randomize: bool = True,
        mobile: bool = False,
        **kwargs
    ) -> BrowserContext:
        """
        Create a new browser context with optional randomization.
        
        Args:
            browser: Browser instance
            randomize: Use randomized viewport and user agent
            mobile: Use mobile user agent and viewport
            **kwargs: Standard Playwright context options
        """
        if randomize and 'viewport' not in kwargs:
            if mobile:
                kwargs['viewport'] = {'width': 412, 'height': 915}
            else:
                kwargs['viewport'] = self._randomize_viewport()
        
        if randomize and 'user_agent' not in kwargs:
            kwargs['user_agent'] = self.get_random_user_agent(mobile=mobile)
        
        return browser.new_context(**kwargs)

    def launch_persistent_context(
        self,
        user_data_dir: str,
        headless: bool = True,
        slow_mo: int = 0,
        proxy: Optional[Dict[str, str]] = None,
        randomize: bool = True,
        mobile: bool = False,
        fingerprint: Optional[BrowserFingerprint] = None,
        **kwargs
    ) -> BrowserContext:
        """
        Launch a persistent browser context with session storage.

        Args:
            user_data_dir: Directory to store session data
            headless: Run headless (False recommended)
            slow_mo: Slow down operations
            proxy: Proxy configuration
            randomize: Use random viewport/user agent
            mobile: Use mobile configuration
            fingerprint: BrowserFingerprint to apply (overrides randomize)
            **kwargs: Additional context options
        """
        if not self._playwright:
            raise RuntimeError("BrowserManager must be used as a context manager")

        args = self._get_browser_args(kwargs.pop('args', None))

        # Apply fingerprint settings if provided
        if fingerprint:
            # Use fingerprint's context options
            fingerprint_options = fingerprint.to_playwright_context_options()
            kwargs.update(fingerprint_options)
        elif randomize:
            # Set defaults if not provided and not using fingerprint
            if 'viewport' not in kwargs:
                if mobile:
                    kwargs['viewport'] = {'width': 412, 'height': 915}
                else:
                    kwargs['viewport'] = self._randomize_viewport()

            if 'user_agent' not in kwargs:
                kwargs['user_agent'] = self.get_random_user_agent(mobile=mobile)

        context_options = {
            'user_data_dir': user_data_dir,
            'headless': headless,
            'slow_mo': slow_mo,
            'args': args,
            **kwargs
        }

        if proxy:
            context_options['proxy'] = proxy

        context = self._playwright.chromium.launch_persistent_context(**context_options)

        # Apply fingerprint JavaScript spoofing if fingerprint provided
        if fingerprint:
            # Create a page to apply fingerprint scripts
            page = context.new_page()
            try:
                FingerprintGenerator().apply_fingerprint_to_page(page, fingerprint)
            finally:
                # Close the temporary page
                page.close()

        return context

    def new_page(self, context: BrowserContext, stealth: bool = False) -> Page:
        """
        Create a new page, optionally with stealth mode.
        
        Args:
            context: Browser context
            stealth: Apply stealth measures to hide automation
        """
        page = context.new_page()
        if stealth:
            self._stealth_engine.apply_stealth_sync(page)
            # Additional stealth: inject scripts to mask automation
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                window.chrome = { runtime: {} };
            """)
        return page