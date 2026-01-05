# Instagram Upload Troubleshooting Guide

Based on your error image and the automation code analysis, here are the most common causes and solutions for Instagram upload failures:

## 1. File Format and Size Issues

### Common Causes

- Unsupported file format
- File too large (>4GB for videos, >30MB for photos)
- Corrupted media files
- Incorrect aspect ratio for videos

### Solutions

```python
# Check file before upload
import os
from pathlib import Path

def validate_media_file(file_path):
    """Validate media file before upload."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_size = os.path.getsize(file_path)
    file_ext = Path(file_path).suffix.lower()
    
    # Instagram video limits
    if file_ext in ['.mp4', '.mov', '.avi']:
        if file_size > 4 * 1024 * 1024 * 1024:  # 4GB
            raise ValueError("Video file too large (>4GB)")
    
    # Instagram photo limits  
    elif file_ext in ['.jpg', '.jpeg', '.png']:
        if file_size > 30 * 1024 * 1024:  # 30MB
            raise ValueError("Photo file too large (>30MB)")
    
    print(f"✓ File validation passed: {file_path} ({file_size / 1024 / 1024:.1f}MB)")
    return True

# Use before upload
validate_media_file("your_video.mp4")
```

## 2. Upload Dialog Issues

### Problem: "Upload stalled. Dialog visible" or Next button not found

### Solutions

The code already has good retry logic, but you can enhance it:

```python
# Enhanced upload media function
def enhanced_upload_media(automator, file_path):
    """Enhanced upload with better error handling."""
    try:
        # Wait for dialog
        dialog = automator.page.locator('div[role="dialog"]').first
        dialog.wait_for(state="visible", timeout=10000)
        
        # Multiple file input strategies
        input_strategies = [
            'input[type="file"]',
            'div[role="dialog"] input[type="file"]',
            'button:has-text("Select from computer") + input[type="file"]'
        ]
        
        file_input = None
        for selector in input_strategies:
            try:
                file_input = automator.page.wait_for_selector(selector, timeout=2000)
                if file_input:
                    break
            except:
                continue
        
        if not file_input:
            # Fallback: click select button and handle file chooser
            select_btn = automator.page.locator('button:has-text("Select from computer")').first
            if select_btn.is_visible():
                with automator.page.expect_file_chooser() as fc:
                    select_btn.click()
                fc.value.set_input_files(file_path)
            else:
                raise Exception("Could not find file input or select button")
        else:
            file_input.set_input_files(file_path)
        
        # Enhanced error detection
        error_selectors = [
            'h2:has-text("Couldn\'t select file")',
            'div[role="alert"]',
            'text=This file isn\'t supported',
            'text=File too large',
            'text=Video too short',
            'text=Video too long'
        ]
        
        for error_sel in error_selectors:
            error_elem = automator.page.locator(error_sel).first
            if error_elem.is_visible(timeout=2000):
                error_text = error_elem.inner_text()
                raise Exception(f"Upload error: {error_text}")
        
        print("✓ File uploaded successfully")
        return True
        
    except Exception as e:
        print(f"✗ Upload failed: {e}")
        # Take screenshot for debugging
        automator.page.screenshot(path=f"upload_error_{int(time.time())}.png")
        return False
```

## 3. Popup and Dialog Interference

### Problem: Popups blocking the upload process

### Enhanced popup handling

```python
def enhanced_popup_handler(automator):
    """Enhanced popup detection and handling."""
    popup_selectors = [
        # Cookie banners
        "button:has-text('Accept')",
        "button:has-text('Decline')", 
        "button:has-text('Only essential')",
        "button:has-text('Got it')",
        
        # Feature discovery
        "text=Not Now",
        "text=Nicht jetzt",
        "div[role='button']:has-text('Not Now')",
        
        # Error dialogs
        "button:has-text('OK')",
        "button:has-text('Cancel')",
        "button:has-text('Close')",
        
        # Navigation prompts
        "button:has-text('Next')",
        "button:has-text('Weiter')"
    ]
    
    closed_popups = []
    for selector in popup_selectors:
        try:
            if automator.page.is_visible(selector, timeout=500):
                # Be careful not to close upload-related buttons
                if "Next" in selector and "Weiter" in selector:
                    continue  # Skip Next buttons to avoid interfering with upload flow
                    
                automator.page.click(selector, timeout=1000)
                closed_popups.append(selector)
                automator.page.wait_for_timeout(300)
        except:
            continue
    
    if closed_popups:
        print(f"Closed {len(closed_popups)} popups: {closed_popups}")
    
    return len(closed_popups) > 0
```

## 4. Network and Timing Issues

### Problem: Network timeouts or slow processing

### Solutions

```python
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeout

def robust_upload_flow(automator, file_path, caption, max_retries=3):
    """Robust upload flow with comprehensive retry logic."""
    
    for attempt in range(max_retries):
        try:
            print(f"Upload attempt {attempt + 1}/{max_retries}")
            
            # Clear any existing popups
            automator.handle_popups()
            
            # Step 1: Click Create
            if not automator._click_create_button(SelectorStrategy(automator.page)):
                raise Exception("Could not find Create button")
            
            # Step 2: Upload file with retry
            upload_success = False
            for upload_attempt in range(3):
                try:
                    automator._upload_media(file_path, retry=False)
                    upload_success = True
                    break
                except Exception as e:
                    print(f"Upload attempt {upload_attempt + 1} failed: {e}")
                    if upload_attempt < 2:
                        automator.page.wait_for_timeout(2000)  # Wait before retry
                        automator.handle_popups()
                    else:
                        raise e
            
            if not upload_success:
                raise Exception("File upload failed after all retries")
            
            # Step 3: Handle Next buttons with longer timeouts
            dialog = automator.page.locator('div[role="dialog"]').first
            
            # Wait for Next button (longer timeout for video processing)
            next_btn = dialog.locator('div._ac7d [role="button"]').first
            next_btn.wait_for(state="visible", timeout=45000)  # Increased from 30s
            
            next_btn.click()
            automator.page.wait_for_timeout(2000)
            
            # Step 4: Caption (if provided)
            if caption:
                caption_selectors = [
                    'div[aria-label*="Write a caption"]',
                    'div[role="textbox"]',
                    'textarea[aria-label*="caption"]'
                ]
                
                for sel in caption_selectors:
                    try:
                        caption_box = automator.page.locator(sel).first
                        if caption_box.is_visible(timeout=2000):
                            caption_box.fill(caption)
                            break
                    except:
                        continue
            
            # Step 5: Share
            share_btn = dialog.locator('div._ac7d [role="button"]').first
            share_btn.wait_for(state="visible", timeout=30000)
            share_btn.click()
            
            # Step 6: Verify success
            success_selectors = [
                'text="Your reel has been shared"',
                'text="Your post has been shared"',
                'svg[aria-label="Animated checkmark"]'
            ]
            
            for sel in success_selectors:
                try:
                    if automator.page.locator(sel).first.is_visible(timeout=30000):
                        print("✓ Upload successful!")
                        return True
                except:
                    continue
            
            # If no success message but no "Sharing" indicator, assume success
            if not automator.page.is_visible('text="Sharing"'):
                print("✓ Upload completed (success indicator not found)")
                return True
                
        except PlaywrightTimeout:
            print(f"Timeout on attempt {attempt + 1}")
            automator.page.screenshot(path=f"timeout_attempt_{attempt + 1}.png")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            automator.page.screenshot(path=f"error_attempt_{attempt + 1}.png")
        
        # Wait before next retry
        if attempt < max_retries - 1:
            automator.page.wait_for_timeout(5000)
    
    print("✗ All upload attempts failed")
    return False
```

## 5. Session and Authentication Issues

### Problem: Session expired or authentication problems

### Solutions

```python
def check_session_validity(automator):
    """Check if Instagram session is still valid."""
    try:
        # Navigate to a protected page
        automator.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        automator.page.wait_for_timeout(3000)
        
        # Check for login indicators
        login_indicators = [
            'input[name="username"]',
            'text=Log in',
            'text=Anmelden'
        ]
        
        for indicator in login_indicators:
            if automator.page.is_visible(indicator, timeout=2000):
                print("⚠️ Session appears to be expired - login required")
                return False
        
        print("✓ Session appears valid")
        return True
        
    except Exception as e:
        print(f"Session check failed: {e}")
        return False

def refresh_session(automator):
    """Attempt to refresh the session."""
    try:
        # Clear cookies and reload
        automator.context.clear_cookies()
        automator.page.reload()
        automator.page.wait_for_timeout(3000)
        
        # Check if we're logged in
        if check_session_validity(automator):
            return True
            
        print("Session refresh failed - manual login may be required")
        return False
        
    except Exception as e:
        print(f"Session refresh failed: {e}")
        return False
```

## 6. Debugging Steps

### Enable Debug Mode

```bash
DEBUG=1 python3 examples/instagram_interactive.py
```

### Debug Information to Collect

1. **Screenshots**: Check `debug_shots/` directory for failure points
2. **HTML Dumps**: Look for `*_dialog_dump.html` files
3. **Console Logs**: Check for JavaScript errors
4. **Network Logs**: Monitor failed requests

### Quick Diagnostics

```python
def diagnose_upload_issue(automator):
    """Quick diagnostic function."""
    print("=== Upload Issue Diagnosis ===")
    
    # Check current URL
    print(f"Current URL: {automator.page.url}")
    
    # Check for visible dialogs
    dialogs = automator.page.locator('div[role="dialog"]').count()
    print(f"Visible dialogs: {dialogs}")
    
    # Check for file inputs
    file_inputs = automator.page.locator('input[type="file"]').count()
    print(f"File inputs found: {file_inputs}")
    
    # Check for error messages
    error_selectors = [
        'h2:has-text("Couldn\'t")',
        'div[role="alert"]',
        'text=Error'
    ]
    
    for selector in error_selectors:
        if automator.page.is_visible(selector, timeout=1000):
            error_text = automator.page.locator(selector).first.inner_text()
            print(f"Error found: {error_text}")
    
    # Take diagnostic screenshot
    automator.page.screenshot(path=f"diagnosis_{int(time.time())}.png")
    print("Diagnostic screenshot saved")

# Run diagnostics before upload
diagnose_upload_issue(automator)
```

## Summary of Most Likely Causes

1. **File format/size issues** - Check file validation
2. **Popup interference** - Enhanced popup handling
3. **Slow video processing** - Increase timeouts
4. **Session expiration** - Check authentication
5. **UI changes** - Monitor selector updates

Start with file validation and enhanced popup handling, as these are the most common issues.
