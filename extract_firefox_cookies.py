#!/usr/bin/env python3
"""
Extract cookies from Firefox browser for use with social media automation.

This script extracts cookies from Firefox's cookie database and converts them
to the format expected by Playwright for Instagram and TikTok automation.
"""

import sqlite3
import json
import os
import sys
import platform
from pathlib import Path
from datetime import datetime, timezone

def get_firefox_profile_path():
    """Get the default Firefox profile path for the current OS."""
    system = platform.system()

    if system == "Linux":
        # Linux: ~/.mozilla/firefox/*.default-release
        home = Path.home()
        firefox_dir = home / ".mozilla" / "firefox"
        if firefox_dir.exists():
            # Find the default profile
            for profile_dir in firefox_dir.iterdir():
                if profile_dir.is_dir() and (profile_dir.name.endswith(".default") or
                                           profile_dir.name.endswith(".default-release")):
                    return profile_dir
    elif system == "Darwin":  # macOS
        home = Path.home()
        firefox_dir = home / "Library" / "Application Support" / "Firefox" / "Profiles"
        if firefox_dir.exists():
            for profile_dir in firefox_dir.iterdir():
                if profile_dir.is_dir() and (profile_dir.name.endswith(".default") or
                                           profile_dir.name.endswith(".default-release")):
                    return profile_dir
    elif system == "Windows":
        # Windows: %APPDATA%\Mozilla\Firefox\Profiles
        appdata = os.environ.get("APPDATA")
        if appdata:
            firefox_dir = Path(appdata) / "Mozilla" / "Firefox" / "Profiles"
            if firefox_dir.exists():
                for profile_dir in firefox_dir.iterdir():
                    if profile_dir.is_dir() and (profile_dir.name.endswith(".default") or
                                               profile_dir.name.endswith(".default-release")):
                        return profile_dir

    return None

def extract_instagram_cookies(firefox_profile_path):
    """Extract Instagram cookies from Firefox profile."""
    cookies_db = firefox_profile_path / "cookies.sqlite"

    if not cookies_db.exists():
        print(f"❌ Firefox cookies database not found at: {cookies_db}")
        return []

    # Connect to Firefox's cookies database
    # Firefox locks the database while running, so we need to copy it
    import tempfile
    import shutil

    with tempfile.NamedTemporaryFile(delete=False) as temp_db:
        temp_db_path = temp_db.name

    try:
        shutil.copy2(cookies_db, temp_db_path)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Query for Instagram cookies
        # Convert Firefox timestamp (microseconds since epoch) to Unix timestamp
        cursor.execute("""
            SELECT host, name, value, path, expiry, isSecure, isHttpOnly
            FROM moz_cookies
            WHERE host LIKE '%instagram.com%'
            ORDER BY host, name
        """)

        cookies = []
        for row in cursor.fetchall():
            host, name, value, path, expiry, is_secure, is_http_only = row

            # Convert Firefox timestamp to Unix timestamp
            # Firefox uses microseconds since epoch, we need seconds
            if expiry and expiry > 0:
                # Firefox expiry is in microseconds, convert to seconds
                expiry_seconds = expiry / 1000000
            else:
                # Session cookie
                expiry_seconds = None

            cookie = {
                "name": name,
                "value": value,
                "domain": host,
                "path": path,
                "secure": bool(is_secure),
                "httpOnly": bool(is_http_only)
            }

            if expiry_seconds:
                cookie["expires"] = expiry_seconds

            cookies.append(cookie)

        conn.close()

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_db_path)
        except:
            pass

    return cookies

def extract_tiktok_cookies(firefox_profile_path):
    """Extract TikTok cookies from Firefox profile."""
    cookies_db = firefox_profile_path / "cookies.sqlite"

    if not cookies_db.exists():
        print(f"❌ Firefox cookies database not found at: {cookies_db}")
        return []

    import tempfile
    import shutil

    with tempfile.NamedTemporaryFile(delete=False) as temp_db:
        temp_db_path = temp_db.name

    try:
        shutil.copy2(cookies_db, temp_db_path)

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Query for TikTok cookies
        cursor.execute("""
            SELECT host, name, value, path, expiry, isSecure, isHttpOnly
            FROM moz_cookies
            WHERE host LIKE '%tiktok.com%'
            ORDER BY host, name
        """)

        cookies = []
        for row in cursor.fetchall():
            host, name, value, path, expiry, is_secure, is_http_only = row

            if expiry and expiry > 0:
                expiry_seconds = expiry / 1000000
            else:
                expiry_seconds = None

            cookie = {
                "name": name,
                "value": value,
                "domain": host,
                "path": path,
                "secure": bool(is_secure),
                "httpOnly": bool(is_http_only)
            }

            if expiry_seconds:
                cookie["expires"] = expiry_seconds

            cookies.append(cookie)

        conn.close()

    finally:
        try:
            os.unlink(temp_db_path)
        except:
            pass

    return cookies

def save_cookies_for_platform(cookies, platform_name, session_dir):
    """Save cookies for a specific platform."""
    if not cookies:
        print(f"⚠️ No {platform_name} cookies found")
        return

    # Create session directory
    session_path = Path(session_dir)
    session_path.mkdir(exist_ok=True)

    cookies_file = session_path / "cookies.json"

    # Save cookies in Playwright format
    with open(cookies_file, 'w') as f:
        json.dump(cookies, f, indent=2)

    print(f"✅ Saved {len(cookies)} {platform_name} cookies to {cookies_file}")

def main():
    print("🔍 Finding Firefox profile...")

    firefox_profile = get_firefox_profile_path()
    if not firefox_profile:
        print("❌ Could not find Firefox profile. Please make sure Firefox is installed and has been run at least once.")
        print("\nManual steps:")
        print("1. Open Firefox")
        print("2. Go to about:profiles")
        print("3. Find your default profile path")
        print("4. Run this script with the profile path as an argument")
        sys.exit(1)

    print(f"📁 Found Firefox profile: {firefox_profile}")

    # Extract Instagram cookies
    print("\n📸 Extracting Instagram cookies...")
    ig_cookies = extract_instagram_cookies(firefox_profile)
    save_cookies_for_platform(ig_cookies, "Instagram", "ig_session")

    # Extract TikTok cookies
    print("\n🎵 Extracting TikTok cookies...")
    tt_cookies = extract_tiktok_cookies(firefox_profile)
    save_cookies_for_platform(tt_cookies, "TikTok", "tiktok_session")

    print("\n🎉 Cookie extraction complete!")
    print("\n📋 Next steps:")
    print("1. Make sure you're logged into Instagram/TikTok in Firefox")
    print("2. Run your engagement scripts - they will use these cookies automatically")
    print("3. Test with single actions first before batch operations")

    if not ig_cookies and not tt_cookies:
        print("\n⚠️ No social media cookies found. Make sure you're logged into Instagram and/or TikTok in Firefox.")

if __name__ == "__main__":
    main()