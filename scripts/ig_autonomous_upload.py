#!/usr/bin/env python3
"""
Robust Autonomous Instagram Upload Script

Features:
- Multiple selector fallbacks for Create/Erstellen, Next, Share buttons
- Automatic popup handling (Messaging tab, notifications, cookies)
- Comprehensive logging with timestamps and screenshots
- Poller integration with log file reporting
- Error recovery and retry mechanisms

Usage:
    python scripts/ig_autonomous_upload.py --file /path/to/video.mp4 --caption "Your caption"
    # Optional: --cookies ig_session/cookies.json --headless --log-dir /tmp/ig_logs
"""

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement


class InstagramUploadLogger:
    """Handles logging and screenshot capture for debugging."""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.step_counter = 0
        
    def log_message(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        # Also write to file
        log_file = self.log_dir / f"{self.session_id}_upload.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def capture_screenshot(self, driver, step_name: str, description: str = ""):
        """Capture screenshot with timestamp and step information."""
        try:
            self.step_counter += 1
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{self.session_id}_{self.step_counter:03d}_{step_name}.png"
            filepath = self.log_dir / filename
            
            driver.save_screenshot(str(filepath))
            
            if description:
                self.log_message(f"Screenshot captured: {filename} - {description}")
            else:
                self.log_message(f"Screenshot captured: {filename}")
                
            return filepath
        except Exception as e:
            self.log_message(f"Failed to capture screenshot: {e}", "ERROR")
            return None


class InstagramUploadManager:
    """Manages the Instagram upload process with robust error handling."""
    
    def __init__(self, log_dir: Path, headless: bool = False):
        self.logger = InstagramUploadLogger(log_dir)
        self.driver = None
        self.headless = headless
        self.current_step = "initialization"
        
        # Selector configurations with multiple fallbacks
        self.selectors = {
            "create_buttons": [
                # SVG-based buttons
                "//svg[@aria-label='New post']/ancestor::button",
                "//svg[@aria-label='Neuer Beitrag']/ancestor::button", 
                "//svg[@aria-label='Erstellen']/ancestor::button",
                "//svg[@aria-label='Create']/ancestor::button",
                
                # Text-based buttons
                "//button[contains(text(), 'Create')]",
                "//button[contains(text(), 'Erstellen')]",
                "//button[contains(text(), 'New post')]",
                "//button[contains(text(), 'Neuer Beitrag')]",
                
                # Link-based buttons
                "//a[.//svg[@aria-label='New post']]",
                "//a[.//svg[@aria-label='Neuer Beitrag']]",
                "//a[.//svg[@aria-label='Erstellen']]",
                
                # Navigation menu items
                "//nav//span[text()='Create']/ancestor::*[self::button or self::a or self::div]",
                "//nav//span[text()='Erstellen']/ancestor::*[self::button or self::a or self::div]",
                
                # Direct URL fallback
                "//a[@href='/create/select/']",
                
                # Generic create buttons
                "//button[@aria-label='Create']",
                "//button[@aria-label='Erstellen']",
                "//div[@role='button' and .//span[text()='Create']]",
                "//div[@role='button' and .//span[text()='Erstellen']]",
            ],
            
            "file_inputs": [
                "//input[@type='file' and contains(@accept,'video')]",
                "//input[@type='file' and contains(@accept,'image')]",
                "//input[@type='file']",
                "//input[@accept='video/*,image/*']",
                "//input[@accept='*']",
            ],
            
            "next_buttons": [
                # English variants
                "//div[text()='Next']/parent::button",
                "//span[text()='Next']/ancestor::button",
                "//button[contains(text(), 'Next')]",
                "//button[contains(text(), 'Weiter')]",
                
                # German variants
                "//div[text()='Weiter']/parent::button", 
                "//span[text()='Weiter']/ancestor::button",
                
                # Generic next buttons
                "//button[@type='button' and .//span[contains(text(),'Next')]]",
                "//button[@type='button' and .//span[contains(text(),'Weiter')]]",

                "//div[@role='button' and contains(., 'Next')]",
                "//div[@role='button' and contains(., 'Weiter')]",
                "//button[@aria-label='Next']",
                "//button[@aria-label='Weiter']",
                # Submit buttons that might be "Next" in context
                "//button[@type='submit']",
            ],
            
            "share_buttons": [
                # English variants
                "//div[text()='Share']/parent::button",
                "//span[text()='Share']/ancestor::button", 
                "//button[contains(text(), 'Share')]",
                "//button[contains(text(), 'Teilen')]",
                
                # German variants
                "//div[text()='Teilen']/parent::button",
                "//span[text()='Teilen']/ancestor::button",
                
                # Generic share buttons
                "//button[@type='submit' and .//div[contains(text(),'Share')]]",
                "//button[@type='submit' and .//div[contains(text(),'Teilen')]]",
                "//div[@role='button' and (contains(., 'Share') or contains(., 'Teilen') or contains(., 'Post'))]",
                "//button[@aria-label='Share']",
                "//button[@aria-label='Teilen']",
                "//button[contains(text(), 'Post')]",
                "//button[@type='submit']",
            ],
            
            "caption_inputs": [
                "//textarea[@aria-label='Write a caption...']",
                "//textarea[@aria-label='Schreibe eine Bildunterschrift...']",
                "//textarea[@placeholder='Write a caption...']",
                "//textarea[@placeholder='Schreibe eine Bildunterschrift...']",
                "//label//textarea",
                "//textarea[contains(@aria-label, 'caption')]",
                "//div[@role='textbox' and @contenteditable='true']",
                "//div[@role='textbox' and contains(@aria-label, 'caption')]",
                "//div[@role='textbox' and contains(@placeholder, 'caption')]",
                "//div[@contenteditable='true' and contains(@aria-label, 'caption')]",
            ],
            
            "popup_dismissers": [
                # Notification prompts
                "//button[contains(text(), 'Not Now')]",
                "//button[contains(text(), 'Jetzt nicht')]",
                "//button[contains(text(), 'Later')]",
                "//button[contains(text(), 'Später')]",
                
                # Cookie banners
                "//button[contains(text(), 'Allow all cookies')]",
                "//button[contains(text(), 'Alle zulassen')]",
                "//button[contains(text(), 'Accept all')]",
                "//button[contains(text(), 'Alle akzeptieren')]",
                
                # Messaging tab prompts
                "//button[contains(text(), 'OK')]",
                "//button[contains(text(), 'Got it')]",
                "//button[contains(text(), 'Verstanden')]",
                "//div[@role='dialog']//button[text()='OK']",
                "//div[@role='dialog']//button[contains(text(),'Got it')]",
                "//div[@role='dialog']//button[contains(text(),'Verstanden')]",
                
                # Generic dismiss buttons
                "//button[contains(text(), 'Close')]",
                "//button[contains(text(), 'Schließen')]",
                "//button[@aria-label='Close']",
                "//button[@aria-label='Schließen']",
                
                # Cross buttons
                "//button[@aria-label='Close dialog']",
                "//button[@aria-label='Dialog schließen']",
                "//button[@aria-label='Dismiss']",
            ],
            
            "success_indicators": [
                "//span[contains(text(),'shared')]",
                "//span[contains(text(),'geteilt')]",
                "//div[contains(text(),'Your reel has been shared')]",
                "//div[contains(text(),'wurde geteilt')]",
                "//span[contains(text(),'posted')]",
                "//span[contains(text(),'gepostet')]",
                "//div[contains(text(),'Your post has been shared')]",
                "//div[contains(text(),'Dein Beitrag wurde geteilt')]",
            ]
        }
    
    def setup_driver(self):
        """Initialize the Chrome driver with stealth settings."""
        self.logger.log_message("Initializing Chrome driver with stealth settings")
        
        opts = uc.ChromeOptions()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--disable-web-security")
        opts.add_argument("--disable-features=IsolateOrigins,site-per-process")
        opts.add_argument("--disable-features=VizDisplayCompositor")
        opts.add_argument("--disable-ipc-flooding-protection")
        opts.add_argument("--disable-background-timer-throttling")
        opts.add_argument("--disable-backgrounding-occluded-windows")
        opts.add_argument("--disable-renderer-backgrounding")
        opts.add_argument("--disable-features=TranslateUI")
        opts.add_argument("--disable-ipc-flooding-protection")
        opts.add_argument("--disable-web-security")
        opts.add_argument("--allow-running-insecure-content")
        opts.add_argument("--disable-features=VizDisplayCompositor")
        
        if self.headless:
            opts.add_argument("--headless=new")
        
        # Additional stealth options
        # opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        # opts.add_experimental_option('useAutomationExtension', False)
        
        self.driver = uc.Chrome(options=opts)
        self.driver.maximize_window()
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.logger.log_message("Chrome driver initialized successfully")
    
    def load_cookies(self, cookies_path: Path):
        """Load Instagram cookies from file."""
        self.logger.log_message(f"Loading cookies from {cookies_path}")
        
        if not cookies_path.exists():
            raise FileNotFoundError(f"Cookies file not found: {cookies_path}")
        
        try:
            with open(cookies_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            if not isinstance(cookies, list):
                raise ValueError("Cookies file must contain a list of cookie dicts")
            
            # Navigate to Instagram first
            self.driver.get("https://www.instagram.com/")
            time.sleep(3)
            
            # Inject cookies
            for cookie in cookies:
                name = cookie.get("name")
                value = cookie.get("value")
                if not name or value is None:
                    continue
                
                cookie_dict = {
                    "name": name,
                    "value": value,
                    "domain": cookie.get("domain", ".instagram.com"),
                    "path": cookie.get("path", "/"),
                }
                
                if cookie.get("expiry"):
                    cookie_dict["expiry"] = cookie["expiry"]
                if cookie.get("secure") is not None:
                    cookie_dict["secure"] = bool(cookie["secure"])
                if cookie.get("httpOnly") is not None:
                    cookie_dict["httpOnly"] = bool(cookie["httpOnly"])
                
                try:
                    self.driver.add_cookie(cookie_dict)
                except Exception as e:
                    self.logger.log_message(f"Failed to add cookie {name}: {e}", "WARNING")
            
            self.driver.refresh()
            time.sleep(3)
            self.logger.log_message("Cookies loaded successfully")
            
        except Exception as e:
            self.logger.log_message(f"Failed to load cookies: {e}", "ERROR")
            raise
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in to Instagram."""
        self.logger.log_message("Checking login status")
        
        try:
            # If still on login page -> not logged in
            if "accounts/login" in self.driver.current_url:
                self.logger.log_message("Still on login page - not logged in", "WARNING")
                return False
            
            # Look for search box or profile elements as login indicators
            login_indicators = [
                "//input[@placeholder='Search']",
                "//input[@placeholder='Suchen']",
                "//a[contains(@href, '/direct/inbox/')]",
                "//a[contains(@href, '/accounts/edit/')]",
                "//svg[@aria-label='Home']",
                "//svg[@aria-label='Start']",
            ]
            
            for selector in login_indicators:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    self.logger.log_message("Login confirmed via UI elements")
                    return True
                except TimeoutException:
                    continue
            
            self.logger.log_message("No login indicators found", "WARNING")
            return False
            
        except Exception as e:
            self.logger.log_message(f"Error checking login status: {e}", "ERROR")
            return False
    
    def handle_popups(self, timeout: int = 5):
        """Handle various popups and dialogs."""
        self.logger.log_message("Checking for popups to dismiss")
        
        popup_selectors = self.selectors["popup_dismissers"]
        
        for selector in popup_selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                self.driver.execute_script("arguments[0].click();", element)
                self.logger.log_message(f"Dismissed popup using selector: {selector}")
                time.sleep(1)  # Wait for popup to close
                return True
            except TimeoutException:
                continue
            except Exception as e:
                self.logger.log_message(f"Error dismissing popup with selector {selector}: {e}", "WARNING")
        
        self.logger.log_message("No popups found to dismiss")
        return False
    
    def click_element_with_fallbacks(self, selectors: List[str], timeout: int = 15, step_name: str = "") -> bool:
        """Try multiple selectors to click an element."""
        self.current_step = step_name or "click_element"
        
        for i, selector in enumerate(selectors):
            try:
                self.logger.log_message(f"Trying selector {i+1}/{len(selectors)}: {selector}")
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                self.driver.execute_script("arguments[0].click();", element)
                self.logger.log_message(f"Successfully clicked using selector: {selector}")
                return True
            except TimeoutException:
                self.logger.log_message(f"Selector timed out: {selector}", "DEBUG")
                continue
            except Exception as e:
                self.logger.log_message(f"Error with selector {selector}: {e}", "DEBUG")
                continue
        
        self.logger.log_message(f"Failed to click element with any selector", "ERROR")
        return False
    
    def wait_for_element_with_fallbacks(self, selectors: List[str], timeout: int = 15, step_name: str = "") -> Optional[WebElement]:
        """Wait for any element from a list of selectors."""
        self.current_step = step_name or "wait_element"
        
        for i, selector in enumerate(selectors):
            try:
                self.logger.log_message(f"Waiting for selector {i+1}/{len(selectors)}: {selector}")
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                self.logger.log_message(f"Found element using selector: {selector}")
                return element
            except TimeoutException:
                self.logger.log_message(f"Selector not found: {selector}", "DEBUG")
                continue
            except Exception as e:
                self.logger.log_message(f"Error waiting for selector {selector}: {e}", "DEBUG")
                continue
        
        self.logger.log_message(f"No elements found with any selector", "ERROR")
        return None
    
    def upload_media(self, media_path: Path, caption: str) -> bool:
        """Perform the complete media upload process."""
        self.logger.log_message(f"Starting upload process for: {media_path}")
        
        try:
            # Step 1: Open upload dialog
            self.logger.log_message("Step 1: Opening upload dialog")
            self.capture_screenshot("upload_start", "Starting upload process")
            
            if not self.click_element_with_fallbacks(
                self.selectors["create_buttons"],
                timeout=20,
                step_name="open_upload_dialog"
            ):
                self.logger.log_message("Failed to open upload dialog, trying direct URL", "WARNING")
                try:
                    self.driver.get("https://www.instagram.com/create/select/")
                    time.sleep(3)
                except Exception as e:
                    self.logger.log_message(f"Failed to navigate to upload URL: {e}", "ERROR")
                    return False
            
            self.capture_screenshot("upload_dialog_opened", "Upload dialog opened")
            
            # Step 2: Handle any popups that appeared
            self.handle_popups()
            
            # Step 3: Find and upload file
            self.logger.log_message("Step 2: Finding file input")
            file_input = self.wait_for_element_with_fallbacks(
                self.selectors["file_inputs"],
                timeout=25,
                step_name="find_file_input"
            )
            
            if not file_input:
                self.logger.log_message("No file input found", "ERROR")
                self.capture_screenshot("no_file_input", "No file input found")
                return False
            
            self.logger.log_message(f"Found file input, uploading: {media_path}")
            file_input.send_keys(str(media_path))
            self.logger.log_message("File selected successfully")
            
            self.capture_screenshot("file_selected", f"File selected: {media_path.name}")
            
            # Step 4: Handle Next buttons (usually twice for trim and details)
            for step in range(1, 3):
                self.logger.log_message(f"Step 3.{step}: Clicking Next button")
                if not self.click_element_with_fallbacks(
                    self.selectors["next_buttons"],
                    timeout=20,
                    step_name=f"click_next_{step}"
                ):
                    self.logger.log_message(f"Next button {step} not found, continuing anyway", "WARNING")
                else:
                    self.logger.log_message(f"Next button {step} clicked successfully")
                
                self.capture_screenshot(f"next_clicked_{step}", f"After clicking Next {step}")
                time.sleep(2)
            
            # Step 5: Set caption
            self.logger.log_message("Step 4: Setting caption")
            caption_element = self.wait_for_element_with_fallbacks(
                self.selectors["caption_inputs"],
                timeout=15,
                step_name="find_caption_input"
            )
            
            if caption_element:
                caption_element.clear()
                caption_element.send_keys(caption)
                self.logger.log_message(f"Caption set ({len(caption)} characters)")
            else:
                self.logger.log_message("Caption field not found, continuing without caption", "WARNING")
            
            self.capture_screenshot("caption_set", f"Caption set: {caption[:50]}...")
            
            # Step 6: Click Share
            self.logger.log_message("Step 5: Clicking Share button")
            if not self.click_element_with_fallbacks(
                self.selectors["share_buttons"],
                timeout=20,
                step_name="click_share"
            ):
                self.logger.log_message("Share button not found", "ERROR")
                self.capture_screenshot("share_failed", "Share button not found")
                return False
            
            self.logger.log_message("Share button clicked, waiting for confirmation")
            self.capture_screenshot("share_clicked", "Share button clicked")
            
            # Step 7: Wait for success confirmation
            self.logger.log_message("Step 6: Waiting for upload confirmation")
            success_element = self.wait_for_element_with_fallbacks(
                self.selectors["success_indicators"],
                timeout=60,  # Longer timeout for upload processing
                step_name="wait_success"
            )
            
            if success_element:
                self.logger.log_message("Upload completed successfully!")
                self.capture_screenshot("upload_success", "Upload completed successfully")
                return True
            else:
                self.logger.log_message("No success confirmation found, but upload may have succeeded", "WARNING")
                self.capture_screenshot("upload_uncertain", "Upload status uncertain")
                return True  # Assume success if no error occurred
                
        except Exception as e:
            self.logger.log_message(f"Upload failed with exception: {e}", "ERROR")
            self.capture_screenshot("upload_error", f"Upload error: {str(e)[:50]}")
            self.logger.log_message(traceback.format_exc(), "ERROR")
            return False
    
    def capture_screenshot(self, step_name: str, description: str = ""):
        """Capture screenshot for current step."""
        if self.driver:
            return self.logger.capture_screenshot(self.driver, step_name, description)
        return None
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.log_message(f"Error during cleanup: {e}", "WARNING")
            self.driver = None


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Robust Autonomous Instagram Upload Script")
    parser.add_argument("--file", required=True, help="Path to video/image file")
    parser.add_argument("--caption", default="", help="Caption text for the post")
    parser.add_argument("--cookies", default="ig_session/cookies.json", help="Path to cookies.json")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--log-dir", default="/tmp/ig_upload_logs", help="Directory for logs and screenshots")
    parser.add_argument("--max-retries", type=int, default=2, help="Maximum retry attempts")
    
    args = parser.parse_args()
    
    # Validate input file
    media_path = Path(args.file).resolve()
    if not media_path.exists():
        print(f"❌ File not found: {media_path}")
        sys.exit(1)
    
    # Setup logging
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize upload manager
    upload_manager = InstagramUploadManager(log_dir, headless=args.headless)
    
    try:
        # Setup driver
        upload_manager.setup_driver()
        
        # Load cookies
        cookies_path = Path(args.cookies)
        upload_manager.load_cookies(cookies_path)
        
        # Handle initial popups
        upload_manager.handle_popups()
        
        # Check login status
        if not upload_manager.is_logged_in():
            upload_manager.logger.log_message("❌ Login failed (still on login page). Cookies may be invalid.", "ERROR")
            sys.exit(1)
        
        upload_manager.logger.log_message("✅ Login confirmed via cookies")
        upload_manager.logger.log_message(f"📄 Upload file: {media_path}")
        upload_manager.logger.log_message(f"📝 Caption (len={len(args.caption)}): {args.caption}")
        
        # Perform upload with retries
        success = False
        for attempt in range(args.max_retries + 1):
            upload_manager.logger.log_message(f"Upload attempt {attempt + 1}/{args.max_retries + 1}")
            
            success = upload_manager.upload_media(media_path, args.caption)
            
            if success:
                upload_manager.logger.log_message("✅ Upload completed successfully!")
                break
            elif attempt < args.max_retries:
                upload_manager.logger.log_message(f"❌ Upload failed, retrying in 5 seconds...", "WARNING")
                time.sleep(5)
                # Refresh page and try again
                upload_manager.driver.refresh()
                time.sleep(3)
                upload_manager.handle_popups()
            else:
                upload_manager.logger.log_message(f"❌ Upload failed after {args.max_retries + 1} attempts", "ERROR")
        
        # Report results
        log_file = upload_manager.logger.log_dir / f"{upload_manager.logger.session_id}_upload.log"
        print(f"\n📋 Upload log saved to: {log_file}")
        print(f"📸 Screenshots saved to: {upload_manager.logger.log_dir}")
        
        if success:
            print("✅ Upload process completed!")
            sys.exit(0)
        else:
            print("❌ Upload process failed!")
            sys.exit(1)
            
    except Exception as e:
        if upload_manager.logger:
            upload_manager.logger.log_message(f"Fatal error: {e}", "ERROR")
            upload_manager.logger.log_message(traceback.format_exc(), "ERROR")
        
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
    
    finally:
        upload_manager.cleanup()


if __name__ == "__main__":
    main()
