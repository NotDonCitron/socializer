#!/usr/bin/env python3
"""
Example: Autonomous Instagram AI Posting
Demonstrates the complete AI-powered Instagram automation flow from Phase 3.

This script shows how to:
1. Set up vision analysis for image understanding
2. Generate captions and hashtags with AI
3. Make autonomous posting decisions
4. Run continuous monitoring and posting

Usage:
    python examples/instagram_ai_autonomous.py

Environment variables needed:
    OPENAI_API_KEY or GEMINI_API_KEY
    INSTAGRAM_USERNAME
    INSTAGRAM_PASSWORD
"""
import asyncio
import os
import sys
from pathlib import Path

# Add radar to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from radar.browser import BrowserManager
from radar.llm.vision import VisionAnalyzer
from radar.llm.gemini import GeminiLLM
from radar.ai_decision_maker import AIDecisionMaker, AccountStrategy
from radar.instagram_ai_automator import InstagramAIAutomator

async def setup_ai_automator() -> InstagramAIAutomator:
    """Set up the AI-powered Instagram automator with all components."""

    # 1. Set up browser manager
    browser_manager = BrowserManager()

    # 2. Choose vision provider (OpenAI GPT-4V or Gemini)
    # Default to Gemini if API key is available, otherwise OpenAI
    vision_provider = os.getenv("VISION_PROVIDER")
    if not vision_provider:
        if os.getenv("GEMINI_API_KEY"):
            vision_provider = "gemini"
        else:
            vision_provider = "openai"

    vision_analyzer = VisionAnalyzer(provider=vision_provider)

    # 3. Set up LLM client for caption generation
    llm_client = GeminiLLM()

    # 4. Define account strategy for autonomous decision making
    strategy = AccountStrategy(
        target_audience="lifestyle",  # or "business", "creative", "general"
        posting_frequency="moderate",  # "low", "moderate", "high"
        preferred_times=["08:00", "12:00", "18:00", "20:00"],
        content_themes=["nature", "urban", "people", "food"],
        avoid_hashtags=["spam", "bot", "fake"]
    )

    decision_maker = AIDecisionMaker(strategy)

    # 5. Create the AI automator
    automator = InstagramAIAutomator(
        browser_manager=browser_manager,
        user_data_dir="ig_session",
        vision_analyzer=vision_analyzer,
        llm_client=llm_client,
        decision_maker=decision_maker,
        content_directory="content_to_post"
    )

    return automator

async def demo_manual_post(automator: InstagramAIAutomator):
    """Demonstrate manual posting of a single image."""
    print("\n=== Manual Post Demo ===")

    # Check if we have a test image
    test_images = [
        "test_image.jpg",
        "examples/test_image.jpg",
        "content_to_post/test_image.jpg"
    ]

    image_path = None
    for path in test_images:
        if os.path.exists(path):
            image_path = path
            break

    if not image_path:
        print("No test image found. Please place an image in content_to_post/ directory")
        return

    print(f"Posting image: {image_path}")

    try:
        success = await automator.manual_post_image(image_path)
        if success:
            print("✓ Manual post successful!")
        else:
            print("✗ Manual post failed or was skipped by AI")
    except Exception as e:
        print(f"✗ Error during manual post: {e}")

async def demo_autonomous_cycle(automator: InstagramAIAutomator):
    """Demonstrate autonomous posting cycle."""
    print("\n=== Autonomous Cycle Demo ===")
    print("This will run for 2 minutes, monitoring for new content every 30 seconds")
    print("Place images in the 'content_to_post' directory to see them processed")
    print("Press Ctrl+C to stop")

    try:
        # Run for 2 minutes as demo
        await asyncio.wait_for(
            automator.run_autonomous_cycle(cycle_interval=30),
            timeout=120
        )
    except asyncio.TimeoutError:
        print("Demo completed (2 minute timeout)")
    except KeyboardInterrupt:
        print("Demo interrupted by user")

async def show_status(automator: InstagramAIAutomator):
    """Show current automator status."""
    print("\n=== Automator Status ===")
    status = automator.get_status()

    print(f"Content Directory: {status['content_directory']}")
    print(f"Processed Files: {status['processed_files_count']}")
    print(f"Daily Posts: {status['daily_post_count']}")
    print(f"Last Post: {status['last_post_time'] or 'None'}")

    strategy = status['account_strategy']
    print(f"\nAccount Strategy:")
    print(f"  Audience: {strategy['target_audience']}")
    print(f"  Frequency: {strategy['posting_frequency']}")
    print(f"  Preferred Times: {', '.join(strategy['preferred_times'])}")
    print(f"  Themes: {', '.join(strategy['content_themes'])}")

async def demo_image_processing(automator: InstagramAIAutomator):
    """Demonstrate just the AI processing without posting."""
    print("\n=== AI Processing Demo (No Posting) ===")

    # Find available images
    content_dir = Path("content_to_post")
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    images = []

    for file_path in content_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            images.append(str(file_path))

    if not images:
        print("No images found in content_to_post/ directory")
        print("Creating directory and providing instructions...")
        content_dir.mkdir(exist_ok=True)
        print("Place some images in the content_to_post/ directory and run again")
        return

    print(f"Found {len(images)} images. Processing first one...")

    # Process first image
    image_path = images[0]
    print(f"Processing: {image_path}")

    try:
        post_data = await automator.process_image(image_path)

        if post_data:
            print("✓ AI Processing Successful!")
            print(f"Decision: {post_data['decision']}")
            print(f"Caption: {post_data['caption'][:100]}...")
            print(f"Hashtags: {post_data['hashtags']}")

            evaluation = post_data['evaluation']
            print(f"Quality Score: {evaluation['quality_score']:.2f}")
            print(f"Relevance Score: {evaluation['relevance_score']:.2f}")
            print(f"Engagement Potential: {evaluation['engagement_potential']}")

            vision = post_data['vision_analysis']
            print(f"Scene: {vision.get('scene', 'unknown')}")
            print(f"Mood: {vision.get('mood', 'unknown')}")
            print(f"Objects: {', '.join(vision.get('objects', []))}")
        else:
            print("✗ Image was skipped by AI evaluation")

    except Exception as e:
        print(f"✗ Error during processing: {e}")

async def main():
    """Main demo function."""
    print("🤖 Instagram AI Autonomous Posting Demo")
    print("=" * 50)

    # Check environment
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")):
        print("❌ Error: Need OPENAI_API_KEY or GEMINI_API_KEY environment variable")
        return

    if not (os.getenv("INSTAGRAM_USERNAME") and os.getenv("INSTAGRAM_PASSWORD")):
        print("⚠️  Warning: Instagram credentials not set (INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)")
        print("   Manual posting will be skipped, but AI processing will work")

    try:
        # Setup automator
        print("Setting up AI components...")
        automator = await setup_ai_automator()
        print("✓ AI Automator ready")

        # Show status
        await show_status(automator)

        # Demo AI processing (safe, no posting)
        await demo_image_processing(automator)

        # For automated testing, exit after processing
        print("\n" + "=" * 50)
        print("AI Processing Demo completed successfully!")
        print("Phase 3: Kern-AI-Integration is working!")
        return

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nDemo completed.")

if __name__ == "__main__":
    asyncio.run(main())