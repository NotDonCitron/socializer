"""
Batch Engagement Example

Demonstrates how to create and execute batch engagement workflows.
"""
import os
import json
from radar.browser import BrowserManager
from radar.engagement import EngagementManager
from radar.models import EngagementAction, EngagementActionType, EngagementPlatform, EngagementBatch

def create_sample_batch_config():
    """Create a sample batch configuration file."""
    config = {
        "platform": "instagram",
        "settings": {
            "delay_between_actions": 30,
            "max_retries": 2,
            "randomize_order": True,
            "stop_on_failure": False
        },
        "actions": [
            {
                "type": "like",
                "target": "https://www.instagram.com/p/EXAMPLE1/",
                "metadata": {}
            },
            {
                "type": "follow",
                "target": "example_user1",
                "metadata": {}
            },
            {
                "type": "comment",
                "target": "https://www.instagram.com/p/EXAMPLE2/",
                "metadata": {
                    "comment_text": "Great content! 👍"
                }
            },
            {
                "type": "save",
                "target": "https://www.instagram.com/p/EXAMPLE3/",
                "metadata": {}
            },
            {
                "type": "like",
                "target": "https://www.instagram.com/p/EXAMPLE4/",
                "metadata": {}
            }
        ]
    }

    # Save to file
    with open("engagement_batch_example.json", "w") as f:
        json.dump(config, f, indent=2)

    print("Created sample batch configuration: engagement_batch_example.json")
    return config

def main():
    print("=== Batch Engagement Example ===")

    # Create sample configuration
    config = create_sample_batch_config()

    with BrowserManager() as manager:
        # Initialize engagement manager
        engagement_manager = EngagementManager()

        # Initialize appropriate platform
        platform = config["platform"]
        if platform == "instagram":
            if not engagement_manager.initialize_instagram(manager, "ig_session"):
                print("Failed to initialize Instagram automator")
                return
            # Login
            print("Logging in to Instagram...")
            if not engagement_manager.instagram_automator.login("your_username", "your_password", headless=False):
                print(f"Login failed: {engagement_manager.instagram_automator.last_error}")
                return
        elif platform == "tiktok":
            if not engagement_manager.initialize_tiktok(manager, "tiktok_session"):
                print("Failed to initialize TikTok automator")
                return
            # Login
            print("Logging in to TikTok...")
            if not engagement_manager.tiktok_automator.login(headless=False):
                print(f"Login failed: {engagement_manager.tiktok_automator.last_error}")
                return

        # Create batch from configuration
        actions = []
        for action_config in config["actions"]:
            action_type = EngagementActionType[action_config["type"].upper()]
            platform_enum = EngagementPlatform[platform.upper()]

            action = EngagementAction(
                action_type=action_type,
                platform=platform_enum,
                target_identifier=action_config["target"],
                metadata=action_config.get("metadata", {})
            )
            actions.append(action)

        batch = EngagementBatch(
            actions=actions,
            platform=platform_enum,
            settings=config["settings"]
        )

        print(f"\n=== Batch Configuration ===")
        print(f"Platform: {batch.platform.value}")
        print(f"Actions: {len(batch.actions)}")
        print(f"Settings: {batch.settings}")

        print(f"\n=== Executing Batch ===")
        print(f"Starting batch with {len(batch.actions)} actions...")

        # Execute batch
        results = engagement_manager.execute_batch(batch)

        # Print detailed results
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        print(f"\n=== Batch Results ===")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(successful/len(results)*100):.1f}%")

        print(f"\n=== Detailed Results ===")
        for i, result in enumerate(results, 1):
            status = "[✓ SUCCESS]" if result.success else "[✗ FAILED]"
            action_type = result.action.action_type.value
            target = result.action.target_identifier
            print(f"{i}. {status} {action_type}: {target}")

            if not result.success:
                print(f"   Error: {result.message}")

        # Show statistics
        print(f"\n=== Engagement Statistics ===")
        stats = engagement_manager.get_engagement_stats()
        print(f"Actions performed: {stats['action_counts']}")
        print(f"Last action times: {stats['last_action_times']}")

        # Show rate limiting info
        platform_stats = stats['rate_limits'][batch.platform]
        print(f"\nRate Limiting for {batch.platform.value}:")
        print(f"  Min delay: {platform_stats['min_delay']}s")
        print(f"  Max delay: {platform_stats['max_delay']}s")
        print(f"  Max actions/hour: {platform_stats['max_actions_per_hour']}")

        print(f"\n=== Example Complete ===")
        print("You can now:")
        print("1. Modify engagement_batch_example.json and run again")
        print("2. Use the CLI: radar engage batch engagement_batch_example.json")
        print("3. Create your own batch configurations for different workflows")

if __name__ == "__main__":
    main()