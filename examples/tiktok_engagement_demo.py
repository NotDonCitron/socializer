"""
TikTok Engagement Demo

Demonstrates how to use the engagement features for TikTok.
"""
import os
from radar.browser import BrowserManager
from radar.engagement import EngagementManager
from radar.models import EngagementAction, EngagementActionType, EngagementPlatform

def main():
    print("=== TikTok Engagement Demo ===")

    # Example video URLs (replace with real URLs)
    video_urls = [
        "https://www.tiktok.com/@example/video/1",
        "https://www.tiktok.com/@example/video/2",
        "https://www.tiktok.com/@example/video/3"
    ]

    # Example usernames
    usernames = ["example_creator1", "example_creator2"]

    with BrowserManager() as manager:
        # Initialize engagement manager
        engagement_manager = EngagementManager()
        if not engagement_manager.initialize_tiktok(manager, "tiktok_session"):
            print("Failed to initialize TikTok automator")
            return

        # Login
        print("Logging in to TikTok...")
        if not engagement_manager.tiktok_automator.login(headless=False):
            print(f"Login failed: {engagement_manager.tiktok_automator.last_error}")
            return

        print("\n=== Individual Engagement Actions ===")

        # Like a video
        print(f"1. Liking video: {video_urls[0]}")
        result = engagement_manager.tiktok_automator.like_video(video_urls[0])
        print(f"   Result: {'✓ Success' if result.success else '✗ Failed'} - {result.message}")

        # Follow a creator
        print(f"2. Following creator: {usernames[0]}")
        result = engagement_manager.tiktok_automator.follow_creator(usernames[0])
        print(f"   Result: {'✓ Success' if result.success else '✗ Failed'} - {result.message}")

        # Comment on a video
        print(f"3. Commenting on video: {video_urls[1]}")
        result = engagement_manager.tiktok_automator.comment_on_video(video_urls[1], "Awesome content! 🔥")
        print(f"   Result: {'✓ Success' if result.success else '✗ Failed'} - {result.message}")

        # Save a video
        print(f"4. Saving video: {video_urls[2]}")
        result = engagement_manager.tiktok_automator.save_video(video_urls[2])
        print(f"   Result: {'✓ Success' if result.success else '✗ Failed'} - {result.message}")

        print("\n=== Batch Engagement ===")

        # Create a batch of actions
        from radar.models import EngagementBatch

        actions = [
            EngagementAction(
                action_type=EngagementActionType.LIKE,
                platform=EngagementPlatform.TIKTOK,
                target_identifier=video_urls[0]
            ),
            EngagementAction(
                action_type=EngagementActionType.FOLLOW,
                platform=EngagementPlatform.TIKTOK,
                target_identifier=usernames[1]
            ),
            EngagementAction(
                action_type=EngagementActionType.COMMENT,
                platform=EngagementPlatform.TIKTOK,
                target_identifier=video_urls[1],
                metadata={"comment_text": "Great video! 👌"}
            ),
            EngagementAction(
                action_type=EngagementActionType.SAVE,
                platform=EngagementPlatform.TIKTOK,
                target_identifier=video_urls[2]
            )
        ]

        batch = EngagementBatch(
            actions=actions,
            platform=EngagementPlatform.TIKTOK,
            settings={
                "delay_between_actions": 25,
                "max_retries": 2,
                "randomize_order": True,
                "stop_on_failure": False
            }
        )

        print(f"Executing batch with {len(batch.actions)} actions...")
        results = engagement_manager.execute_batch(batch)

        # Print batch results
        successful = sum(1 for r in results if r.success)
        print(f"\nBatch Results: {successful}/{len(results)} successful")

        for i, result in enumerate(results, 1):
            status = "✓" if result.success else "✗"
            print(f"{status} Action {i}: {result.action.action_type.value} on {result.action.target_identifier}")
            if not result.success:
                print(f"   Error: {result.message}")

        print("\n=== Demo Complete ===")
        print("Check the engagement statistics:")
        stats = engagement_manager.get_engagement_stats()
        print(f"Actions performed: {stats['action_counts']}")

if __name__ == "__main__":
    main()