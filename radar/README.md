# Radar - Core Modules

This package contains the core logic for the AI Agent Radar, including browser automation and social media interaction.

## Browser Management (`radar/browser.py`)

The `BrowserManager` class provides a unified interface for launching Playwright browsers with stealth support and persistent context.

### Usage

```python
from radar.browser import BrowserManager

with BrowserManager() as manager:
    # Standard context
    browser = manager.launch_browser(headless=True)
    context = manager.new_context(browser, user_agent="Custom UA")
    page = manager.new_page(context, stealth=True)
    
    # Persistent context (for saving logins)
    persistent_context = manager.launch_persistent_context(
        user_data_dir="./sessions/my_user",
        headless=False
    )
    page = manager.new_page(persistent_context, stealth=True)
```

## Instagram Automation (`radar/instagram.py`)

The `InstagramAutomator` handles specific workflows for Instagram. 

**Note:** For details on how we handle popups, blocking tabs, and robust upload flows, see [INSTAGRAM_HARDENING.md](INSTAGRAM_HARDENING.md).

### Usage

```python
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator

with BrowserManager() as manager:
    automator = InstagramAutomator(manager, user_data_dir="./ig_session")
    success = automator.login("username", "password", headless=False)
    
    if success:
        print("Logged in!")
    else:
        print(f"Error: {automator.last_error}")
```

## Testing

Run tests from the root directory:

```bash
PYTHONPATH=. pytest tests/
```
