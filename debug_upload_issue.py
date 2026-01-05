#!/usr/bin/env python3
"""
Instagram Upload Diagnostic Tool

This script helps identify the root cause of Instagram upload failures
by running systematic diagnostics and tests.
"""

import os
import sys
import time
from pathlib import Path

# Add the radar module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from radar.browser import BrowserManager
from radar.instagram_enhanced import EnhancedInstagramAutomator

def check_file_issues(file_path):
    """Check for common file-related issues."""
    print("=== File Validation ===")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    file_size = os.path.getsize(file_path)
    file_ext = Path(file_path).suffix.lower()
    
    print(f"✅ File exists: {file_path}")
    print(f"📁 File size: {file_size / 1024 / 1024:.1f}MB")
    print(f"📄 File extension: {file_ext}")
    
    # Check file size limits
    if file_ext in ['.mp4', '.mov', '.avi', '.mkv']:
        if file_size > 4 * 1024 * 1024 * 1024:
            print("❌ Video file too large (>4GB)")
            return False
        if file_size < 1024 * 1024:
            print("⚠️  Video file is very small (<1MB)")
    elif file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
        if file_size > 30 * 1024 * 1024:
            print("❌ Photo file too large (>30MB)")
            return False
    else:
        print(f"⚠️  Potentially unsupported format: {file_ext}")
    
    # Try to get file info
    try:
        import subprocess
        result = subprocess.run(['file', file_path], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"📋 File type: {result.stdout.strip()}")
    except:
        print("⚠️  Could not determine file type")
    
    return True

def test_browser_setup():
    """Test browser and context setup."""
    print("\n=== Browser Setup Test ===")
    
    try:
        with BrowserManager() as manager:
            print("✅ BrowserManager initialized")
            
            # Test context creation
            user_data_dir = os.path.join(os.getcwd(), "test_session")
            context = manager.launch_persistent_context(
                user_data_dir,
                headless=True,
                viewport={"width": 1280, "height": 800}
            )
            print("✅ Context created")
            
            # Test page creation
            page = manager.new_page(context, stealth=True)
            print("✅ Page created")
            
            # Test navigation
            page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=30000)
            print("✅ Navigation successful")
            
            # Take screenshot
            screenshot_path = "browser_test_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"✅ Screenshot saved: {screenshot_path}")
            
            context.close()
            return True
            
    except Exception as e:
        print(f"❌ Browser setup failed: {e}")
        return False

def test_instagram_automation(file_path):
    """Test Instagram automation with detailed diagnostics."""
    print("\n=== Instagram Automation Test ===")
    
    if not check_file_issues(file_path):
        return False
    
    try:
        with BrowserManager() as manager:
            user_data_dir = os.path.join(os.getcwd(), "ig_session")
            automator = EnhancedInstagramAutomator(manager, user_data_dir)
            
            # Enable debug mode
            os.environ["DEBUG"] = "1"
            automator.debug = True
            
            print("🚀 Starting Instagram automation test...")
            
            # Test context creation
            automator.context = manager.launch_persistent_context(
                user_data_dir,
                headless=False,  # Keep visible for debugging
                viewport={"width": 1280, "height": 800}
            )
            automator.context.on("page", automator._handle_new_page)
            
            automator.page = manager.new_page(automator.context, stealth=True)
            
            # Navigate to Instagram
            print("📱 Navigating to Instagram...")
            automator.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
            automator.page.wait_for_timeout(5000)
            
            # Check if logged in
            if "login" in automator.page.url:
                print("⚠️  Not logged in. Please log in manually in the browser.")
                print("Press ENTER when logged in and on Instagram home...")
                input()
            
            # Run diagnostics
            automator.diagnose_upload_issue()
            
            # Test just the upload flow (without actually uploading)
            print("\n🧪 Testing upload flow components...")
            
            # Test popup handling
            print("Testing popup handling...")
            popups_closed = automator.enhanced_popup_handler()
            print(f"Popups closed: {popups_closed}")
            
            # Test create button clicking
            print("Testing create button detection...")
            try:
                from radar.selectors import SelectorStrategy
                strategy = SelectorStrategy(automator.page)
                create_found = automator._click_create_button(strategy, timeout=10000)
                print(f"Create button found: {create_found}")
            except Exception as e:
                print(f"Create button test failed: {e}")
            
            print("\n✅ Instagram automation test completed")
            print("Check the debug_shots/ directory for screenshots and diagnostic information")
            
            # Keep browser open for manual inspection
            print("\n🔍 Browser will stay open for 30 seconds for manual inspection...")
            time.sleep(30)
            
            return True
            
    except Exception as e:
        print(f"❌ Instagram automation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_debug_logs():
    """Analyze debug logs and screenshots."""
    print("\n=== Debug Log Analysis ===")
    
    debug_dir = "debug_shots"
    if not os.path.exists(debug_dir):
        print("No debug_shots directory found")
        return
    
    files = os.listdir(debug_dir)
    if not files:
        print("No debug files found")
        return
    
    print(f"Found {len(files)} debug files:")
    
    # Categorize files
    screenshots = [f for f in files if f.endswith('.png')]
    html_dumps = [f for f in files if f.endswith('.html')]
    other_files = [f for f in files if f not in screenshots + html_dumps]
    
    if screenshots:
        print(f"📸 Screenshots ({len(screenshots)}):")
        for shot in sorted(screenshots):
            print(f"  - {shot}")
    
    if html_dumps:
        print(f"📄 HTML dumps ({len(html_dumps)}):")
        for dump in sorted(html_dumps):
            print(f"  - {dump}")
    
    if other_files:
        print(f"📋 Other files ({len(other_files)}):")
        for file in sorted(other_files):
            print(f"  - {file}")
    
    # Look for error patterns in filenames
    error_files = [f for f in files if any(word in f.lower() for word in ['error', 'fail', 'timeout'])]
    if error_files:
        print(f"\n⚠️  Files indicating potential issues:")
        for error_file in error_files:
            print(f"  - {error_file}")

def main():
    """Main diagnostic function."""
    print("🔧 Instagram Upload Diagnostic Tool")
    print("=" * 50)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python debug_upload_issue.py <path_to_media_file>")
        print("Example: python debug_upload_issue.py test_video.mp4")
        return
    
    file_path = sys.argv[1]
    
    print(f"Testing file: {file_path}")
    print()
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_browser_setup():
        tests_passed += 1
    
    if test_instagram_automation(file_path):
        tests_passed += 1
    
    # Analyze debug logs
    analyze_debug_logs()
    tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! Your setup appears to be working correctly.")
        print("If you're still experiencing upload issues, they may be related to:")
        print("  - Instagram's current state/UI changes")
        print("  - Network connectivity")
        print("  - Account-specific restrictions")
        print("  - Rate limiting")
    else:
        print("❌ Some tests failed. Check the output above for specific issues.")
        print("The enhanced automation code may help resolve these issues.")
    
    print("\n💡 Recommendations:")
    print("1. Try using the enhanced Instagram automator (radar/instagram_enhanced.py)")
    print("2. Check the troubleshooting guide (instagram_upload_troubleshooting.md)")
    print("3. Run with DEBUG=1 for detailed logging")
    print("4. Ensure your file meets Instagram's requirements")

if __name__ == "__main__":
    main()