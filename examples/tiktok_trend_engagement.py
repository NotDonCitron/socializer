"""
Automated TikTok Trend Engagement Script.

Discovers trending videos and performs engagement actions (like, comment, follow, save).
Usage: python examples/tiktok_trend_engagement.py --actions like,comment --max-videos 10 --headless
"""
import os
import time
import random
import argparse
from typing import List
from radar.browser import BrowserManager
from radar.tiktok import TikTokAutomator


def discover_trending_videos(automator: TikTokAutomator, max_videos: int = 10) -> List[str]:
    """Discover trending videos by navigating to the trending page."""
    print("🔍 Discovering trending videos...")
    automator.page.goto("https://www.tiktok.com/trending", wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    automator._dismiss_overlays()
    for _ in range(3):
        automator.page.keyboard.press("PageDown")
        time.sleep(2)
    video_urls = []
    try:
        links = automator.page.query_selector_all('a[href*="/video/"]')
        for link in links[:max_videos]:
            href = link.get_attribute('href')
            if href and href not in video_urls:
                if href.startswith('/'):
                    href = f"https://www.tiktok.com{href}"
                video_urls.append(href)
    except Exception as e:
        print(f"⚠️ Error discovering videos: {e}")
    print(f"📹 Found {len(video_urls)} trending videos")
    return video_urls[:max_videos]


def get_random_comment() -> str:
    """Get a random positive comment."""
    comments = ["Awesome content! 🔥", "Love this! 👌", "So cool! 😎", "Great video! 👍",
                "Incredible! 🤩", "This is amazing! ✨", "Well done! 💯", "Fantastic! 🌟"]
    return random.choice(comments)


def perform_engagement(automator: TikTokAutomator, video_url: str, actions: List[str],
                      delay_range: tuple = (5, 15)) -> dict:
    """Perform engagement actions on a single video."""
    results = {"video": video_url, "actions": []}
    if not automator._navigate_to_video(video_url):
        results["error"] = f"Failed to navigate to {video_url}"
        return results
    time.sleep(random.uniform(*delay_range))
    for action in actions:
        try:
            if action == "like":
                result = automator.like_video(video_url)
                results["actions"].append({"type": "like", "success": result.success, "message": result.message})
            elif action == "comment":
                result = automator.comment_on_video(video_url, get_random_comment())
                results["actions"].append({"type": "comment", "success": result.success, "message": result.message})
            elif action == "save":
                result = automator.save_video(video_url)
                results["actions"].append({"type": "save", "success": result.success, "message": result.message})
            elif action == "follow":
                results["actions"].append({"type": "follow", "success": False, "message": "Not implemented"})
            time.sleep(random.uniform(2, 5))
        except Exception as e:
            results["actions"].append({"type": action, "success": False, "message": str(e)})
    return results


def main():
    parser = argparse.ArgumentParser(description="TikTok Trend Engagement Automator")
    parser.add_argument("--actions", default="like,comment", help="Actions: like,comment,save,follow")
    parser.add_argument("--max-videos", type=int, default=5, help="Max videos")
    parser.add_argument("--headless", action="store_true", help="Headless mode")
    parser.add_argument("--delay-min", type=int, default=5, help="Min delay")
    parser.add_argument("--delay-max", type=int, default=15, help="Max delay")
    args = parser.parse_args()

    actions = [a.strip().lower() for a in args.actions.split(",")]
    valid_actions = ["like", "comment", "save", "follow"]
    actions = [a for a in actions if a in valid_actions]

    if not actions:
        print("❌ No valid actions. Use: like,comment,save,follow")
        return

    print("=== TikTok Trend Engagement Automator ===")
    print(f"Actions: {', '.join(actions)}")
    print(f"Max videos: {args.max_videos}")

    with BrowserManager() as manager:
        automator = TikTokAutomator()
        automator.context = manager.launch_persistent_context(
            automator.user_data_dir, headless=args.headless, randomize=True
        )
        automator.page = manager.new_page(automator.context, stealth=True)

        print("\n🔐 Logging in to TikTok...")
        if not automator.login(headless=args.headless):
            print(f"❌ Login failed: {automator.last_error}")
            return

        video_urls = discover_trending_videos(automator, args.max_videos)
        if not video_urls:
            print("❌ No trending videos found")
            return

        print(f"\n🚀 Starting engagement on {len(video_urls)} videos...")
        engagement_results = []
        for i, video_url in enumerate(video_urls, 1):
            print(f"\n[{i}/{len(video_urls)}] Engaging with: {video_url}")
            result = perform_engagement(automator, video_url, actions,
                                       delay_range=(args.delay_min, args.delay_max))
            engagement_results.append(result)
            successful = sum(1 for a in result["actions"] if a["success"])
            print(f"   ✓ {successful}/{len(result['actions'])} actions successful")

        print("\n=== Engagement Summary ===")
        total = sum(len(r["actions"]) for r in engagement_results)
        successful = sum(sum(1 for a in r["actions"] if a["success"]) for r in engagement_results)
        print(f"Total: {total}, Successful: {successful}")
        print(f"Success rate: {successful/total*100:.1f}%" if total > 0 else "N/A")
        print("\n✅ Trend engagement complete!")


if __name__ == "__main__":
    main()
