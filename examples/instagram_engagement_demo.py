"""
Instagram Engagement Demo

Demonstrates how to use the engagement features for Instagram.
"""
import os
from radar.browser import BrowserManager
from radar.engagement import EngagementManager
from radar.models import EngagementAction, EngagementActionType, EngagementPlatform

def main():
    print("=== Instagram Engagement Demo ===")

    # Example post URLs (replace with real URLs)
    post_urls = [
        "https://www.instagram.com/p/EXAMPLE1/",
        "https://www.instagram.com/p/EXAMPLE2/",
        "https://www.instagram.com/p/EXAMPLE3/"
    ]

    # Example usernames
    usernames = ["example_user1", "example_user2"]

    with BrowserManager() as manager:
        # Initialize engagement manager
        engagement_manager = EngagementManager()
        if not engagement_manager.initialize_instagram(manager, "ig_session"):
            print("Failed to initialize Instagram automator")
            return

        # Login
        print("Logging in to Instagram...")
        if not engagement_manager.instagram_automator.login("your_username", "your_password", headless=False):
            print(f"Login failed: {engagement_manager.instagram_automator.last_error}")
            return

        print("\n=== Individual Engagement Actions ===")

        # Like a post
        print(f"1. Liking post: {post_urls[0]}")
        result = engagement_manager.instagram_automator.like_post(post_urls[0])
        print(f"   Result: {'✓ Success' if result.success else '✗ Failed'} - {result.message}")

        # Follow a user
        print(f"2. Following user: {usernames[0]}")
        result = engagement_manager.instagram_automator.follow_user(usernames[0])
        print(f"   Result: {'✓ Success' if result.success else '✗ Failed'} - {result.message}")

        # Comment on a post
        print(f"3. Commenting on post: {post_urls[1]}")
        result = engagement_manager.instagram_automator.comment_on_post(post_urls[1], "Great content! 👍")
        print(f"   Result: {'✓ Success' if result.success else '✗ Failed'} - {result.message}")

        # Save a post
        print(f"4. Saving post: {post_urls[2]}")
        result = engagement_manager.instagram_automator.save_post(post_urls[2])
        print(f"   Result: {'✓ Success' if result.success else '✗ Failed'} - {result.message}")

        print("\n=== Batch Engagement ===")

        # Create a batch of actions
        from radar.models import EngagementBatch

        actions = [
            EngagementAction(
                action_type=EngagementActionType.LIKE,
                platform=EngagementPlatform.INSTAGRAM,
                target_identifier=post_urls[0]
            ),
            EngagementAction(
                action_type=EngagementActionType.FOLLOW,
                platform=EngagementPlatform.INSTAGRAM,
                target_identifier=usernames[1]
            ),
            EngagementAction(
                action_type=EngagementActionType.COMMENT,
                platform=EngagementPlatform.INSTAGRAM,
                target_identifier=post_urls[1],
                metadata={"comment_text": "Nice post! 😊"}
            ),
            EngagementAction(
                action_type=EngagementActionType.SAVE,
                platform=EngagementPlatform.INSTAGRAM,
                target_identifier=post_urls[2]
            )
        ]

        batch = EngagementBatch(
            actions=actions,
            platform=EngagementPlatform.INSTAGRAM,
            settings={
                "delay_between_actions": 30,
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