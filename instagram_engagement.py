#!/usr/bin/env python3
"""
Instagram Engagement Script using Instagrapi with Firefox cookies.
"""

import json
import sys
from instagrapi import Client

def login_with_cookies():
    """Login to Instagram using cookies from Firefox."""
    print("🔐 Logging in with cookies...")

    # Load cookies
    try:
        with open('ig_session/cookies.json', 'r') as f:
            cookies = json.load(f)
    except FileNotFoundError:
        print("❌ Cookies file not found. Run extract_firefox_cookies.py first.")
        return None

    # Create client
    cl = Client()

    # Extract sessionid and other important cookies
    sessionid = None
    csrftoken = None
    ds_user_id = None

    for cookie in cookies:
        if cookie["name"] == "sessionid":
            sessionid = cookie["value"]
        elif cookie["name"] == "csrftoken":
            csrftoken = cookie["value"]
        elif cookie["name"] == "ds_user_id":
            ds_user_id = cookie["value"]

    if not sessionid:
        print("❌ sessionid not found in cookies")
        return None

    # Set the session
    # Use login with sessionid
    try:
        cl.login_by_sessionid(sessionid)
        print("✅ Logged in successfully!")
        return cl
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return None

    # Try to get account info to verify login
    try:
        user = cl.account_info()
        print(f"✅ Logged in as: {user.username} ({user.full_name})")
        return cl
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return None

def perform_engagement(cl):
    """Perform engagement actions: like and share."""
    print("🚀 Performing engagement actions...")

    # Get timeline feed
    try:
        medias = cl.get_timeline_feed()
        if not medias:
            print("❌ No media in timeline")
            return

        # Take the first media
        media = medias[0]
        media_id = media.id
        user_id = media.user.pk

        print(f"📸 Engaging with media: {media_id} by {media.user.username}")

        # Like the post
        try:
            cl.media_like(media_id)
            print("👍 Liked the post")
        except Exception as e:
            print(f"❌ Like failed: {e}")

        # Share to story (if possible)
        try:
            # Share media to story
            cl.story_share(media_id, "Shared via automation")
            print("📤 Shared to story")
        except Exception as e:
            print(f"❌ Share failed: {e}")

        print("🎉 Engagement complete!")

    except Exception as e:
        print(f"❌ Engagement failed: {e}")

def main():
    print("📸 Instagram Engagement Bot")
    print("=" * 40)

    # Login
    cl = login_with_cookies()
    if not cl:
        sys.exit(1)

    # Perform engagement
    perform_engagement(cl)

if __name__ == "__main__":
    main()