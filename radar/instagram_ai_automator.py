"""
AI-powered Instagram Automator for autonomous content posting.
Combines vision analysis, caption generation, and decision making.
"""
import asyncio
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from radar.instagram_enhanced import EnhancedInstagramAutomator
from radar.browser import BrowserManager
from radar.session_manager import load_playwright_cookies
from radar.llm.vision import VisionAnalyzer
from radar.llm.base import LLMClient
from radar.ai_decision_maker import AIDecisionMaker, AccountStrategy, ContentEvaluation, PostingDecision

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramAIAutomator:
    """Autonomous Instagram posting with AI analysis and decision making."""

    def __init__(self,
                 browser_manager: BrowserManager,
                 user_data_dir: str,
                 vision_analyzer: VisionAnalyzer,
                 llm_client: LLMClient,
                 decision_maker: AIDecisionMaker,
                 content_directory: str = "content_to_post"):
        """
        Initialize the AI automator.

        Args:
            browser_manager: Playwright browser manager
            user_data_dir: Directory for browser user data
            vision_analyzer: Vision API analyzer
            llm_client: LLM client for caption generation
            decision_maker: AI decision maker for posting strategy
            content_directory: Directory to monitor for new content
        """
        self.instagram = EnhancedInstagramAutomator(browser_manager, user_data_dir)
        self.vision_analyzer = vision_analyzer
        self.llm_client = llm_client
        self.decision_maker = decision_maker
        self.content_directory = Path(content_directory)
        self.processed_files: set = set()

        # Create content directory if it doesn't exist
        self.content_directory.mkdir(exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def process_image(self, image_path: str) -> Optional[Dict]:
        """
        Process a single image through the AI pipeline.

        Returns:
            Post data dict if should post, None if skipped
        """
        self.logger.info(f"Processing image: {image_path}")

        try:
            # Step 1: Vision analysis
            self.logger.info("Analyzing image with vision AI...")
            vision_analysis = await self.vision_analyzer.analyze_image(image_path)
            self.logger.info(f"Vision analysis complete: {vision_analysis.get('scene', 'unknown')} scene, {vision_analysis.get('mood', 'unknown')} mood")

            # Step 2: Generate caption and hashtags
            self.logger.info("Generating caption with LLM...")
            caption_data = await self.llm_client.generate_instagram_caption(
                vision_analysis=vision_analysis,
                custom_instructions=self._get_custom_instructions(),
                lang="en"
            )
            self.logger.info(f"Caption generated: '{caption_data.get('caption', '')[:50]}...'")

            # Step 3: Evaluate content
            evaluation = self.decision_maker.evaluate_content(
                image_path, vision_analysis, caption_data
            )
            self.logger.info(f"Content evaluation: quality={evaluation.quality_score:.2f}, relevance={evaluation.relevance_score:.2f}")

            # Step 4: Make posting decision
            decision, scheduled_time = self.decision_maker.decide_posting_action(evaluation)

            self.logger.info(f"Decision: {decision.value}" + (f" at {scheduled_time}" if scheduled_time else ""))

            if decision == PostingDecision.SKIP:
                self.logger.info("Skipping content - doesn't meet quality/relevance thresholds")
                return None

            # Prepare post data
            post_data = {
                "image_path": image_path,
                "caption": caption_data.get("caption", ""),
                "hashtags": caption_data.get("hashtags", ""),
                "vision_analysis": vision_analysis,
                "evaluation": {
                    "quality_score": evaluation.quality_score,
                    "relevance_score": evaluation.relevance_score,
                    "engagement_potential": evaluation.engagement_potential,
                    "mood_match": evaluation.mood_match
                },
                "decision": decision.value,
                "scheduled_time": scheduled_time.isoformat() if scheduled_time else None
            }

            return post_data

        except Exception as e:
            self.logger.error(f"Error processing image {image_path}: {e}")
            return None

    def _get_custom_instructions(self) -> str:
        """Get custom instructions for caption generation based on account strategy."""
        strategy = self.decision_maker.strategy

        instructions = []

        # Audience-specific instructions
        if strategy.target_audience == "lifestyle":
            instructions.append("Focus on authentic, relatable moments that inspire daily life.")
        elif strategy.target_audience == "business":
            instructions.append("Emphasize professionalism and industry insights.")
        elif strategy.target_audience == "creative":
            instructions.append("Highlight artistic elements and creative expression.")

        # Theme instructions
        if strategy.content_themes and strategy.content_themes != ["general"]:
            instructions.append(f"Emphasize themes: {', '.join(strategy.content_themes)}")

        # Hashtag restrictions
        if strategy.avoid_hashtags:
            instructions.append(f"Avoid these hashtags: {', '.join(strategy.avoid_hashtags)}")

        return " ".join(instructions)

    async def post_content(self, post_data: Dict) -> bool:
        """Post content to Instagram."""
        try:
            image_path = post_data["image_path"]
            caption = post_data["caption"]
            hashtags = post_data["hashtags"]

            # Combine caption and hashtags
            full_caption = f"{caption}\n\n#{hashtags.replace(' ', ' #')}"

            self.logger.info(f"Posting to Instagram: {image_path}")
            self.logger.info(f"Caption: {full_caption[:100]}...")

            # Use the enhanced Instagram automator to post
            success = self.instagram.upload_photo(image_path, full_caption)

            if success:
                self.logger.info("Post successful!")
                # Record the post for decision making
                self.decision_maker.record_post(datetime.now())
                return True
            else:
                self.logger.error("Post failed!")
                return False

        except Exception as e:
            self.logger.error(f"Error posting content: {e}")
            return False

    async def scan_and_process_content(self) -> List[Dict]:
        """Scan content directory for new images and process them."""
        self.logger.info(f"Scanning directory: {self.content_directory}")

        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        new_images = []

        for file_path in self.content_directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                if str(file_path) not in self.processed_files:
                    new_images.append(str(file_path))
                    self.processed_files.add(str(file_path))

        self.logger.info(f"Found {len(new_images)} new images to process")

        processed_content = []
        for image_path in new_images:
            post_data = await self.process_image(image_path)
            if post_data:
                processed_content.append(post_data)

        return processed_content

    async def run_autonomous_cycle(self, cycle_interval: int = 300) -> None:
        """
        Run continuous autonomous posting cycle.

        Args:
            cycle_interval: Seconds between scanning for new content
        """
        self.logger.info("Starting autonomous Instagram AI posting cycle")
        self.logger.info(f"Monitoring directory: {self.content_directory}")
        self.logger.info(f"Scan interval: {cycle_interval} seconds")

        while True:
            try:
                # Scan for new content
                content_to_post = await self.scan_and_process_content()

                # Process each piece of content
                for post_data in content_to_post:
                    decision = post_data.get("decision")

                    if decision == PostingDecision.POST_NOW.value:
                        # Post immediately
                        success = await self.post_content(post_data)
                        if success:
                            self.logger.info("Posted immediately")
                        else:
                            self.logger.warning("Failed to post immediately")

                    elif decision == PostingDecision.POST_LATER.value:
                        # Schedule for later (simplified - just wait)
                        scheduled_time = datetime.fromisoformat(post_data["scheduled_time"])
                        delay = (scheduled_time - datetime.now()).total_seconds()

                        if delay > 0:
                            self.logger.info(f"Scheduling post in {delay:.0f} seconds")
                            await asyncio.sleep(delay)
                            await self.post_content(post_data)
                        else:
                            # Time already passed, post now
                            await self.post_content(post_data)

                    elif decision == PostingDecision.QUEUE.value:
                        # Queue for tomorrow - for now, just log
                        self.logger.info("Content queued for optimal timing tomorrow")

                    # Small delay between posts to avoid rate limiting
                    await asyncio.sleep(10)

                # Wait for next scan
                await asyncio.sleep(cycle_interval)

            except KeyboardInterrupt:
                self.logger.info("Autonomous cycle interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Error in autonomous cycle: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def manual_post_image(self, image_path: str) -> bool:
        """Manually post a single image with AI-generated content."""
        self.logger.info(f"Manual post request for: {image_path}")

        post_data = await self.process_image(image_path)
        if not post_data:
            self.logger.warning("Content was skipped by AI evaluation")
            return False

        # Override decision for manual posts
        success = await self.post_content(post_data)
        return success

    def get_status(self) -> Dict:
        """Get current status of the automator."""
        return {
            "content_directory": str(self.content_directory),
            "processed_files_count": len(self.processed_files),
            "daily_post_count": self.decision_maker.daily_post_count,
            "last_post_time": self.decision_maker.last_post_time.isoformat() if self.decision_maker.last_post_time else None,
            "account_strategy": {
                "target_audience": self.decision_maker.strategy.target_audience,
                "posting_frequency": self.decision_maker.strategy.posting_frequency,
                "preferred_times": self.decision_maker.strategy.preferred_times,
                "content_themes": self.decision_maker.strategy.content_themes
            }
        }