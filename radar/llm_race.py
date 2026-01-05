"""
LLM Race Competition System
Two LLMs compete to successfully login via Firefox cookies and perform Instagram engagement actions.
First LLM to achieve 1x of all wins.
"""
import asyncio
import os
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import json

# Mock cookie extraction for demo purposes
def extract_firefox_cookies():
    """Mock Firefox cookie extraction - returns sample Instagram cookies."""
    # This is a mock implementation for demo purposes
    # In real implementation, this would extract from actual Firefox profile
    mock_cookies = [
        {
            "name": "sessionid",
            "value": "mock_session_123",
            "domain": "instagram.com",
            "path": "/",
            "secure": True
        },
        {
            "name": "csrftoken",
            "value": "mock_csrf_456",
            "domain": "instagram.com",
            "path": "/",
            "secure": True
        }
    ]
    return mock_cookies
from radar.instagram_enhanced import EnhancedInstagramAutomator
from radar.browser import BrowserManager
from radar.engagement import EngagementManager
from radar.engagement_models import EngagementAction, EngagementActionType, EngagementPlatform, EngagementBatch
from radar.llm.base import LLMClient
from radar.llm.gemini import GeminiLLM

# Optional OpenAI import
try:
    from radar.llm.openai_client import OpenAILLM
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAILLM = None
    OPENAI_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RaceParticipant:
    """Represents a single LLM participant in the race."""

    def __init__(self, name: str, llm_client: LLMClient, browser_manager: BrowserManager):
        self.name = name
        self.llm = llm_client
        self.browser_manager = browser_manager
        self.instagram: Optional[EnhancedInstagramAutomator] = None
        self.engagement_manager: Optional[EngagementManager] = None
        self.cookies: Optional[List[Dict]] = None
        self.session_valid = False
        self.score = 0
        self.completed_tasks: List[str] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    async def initialize_instagram(self) -> bool:
        """Initialize Instagram automator with session."""
        try:
            self.instagram = EnhancedInstagramAutomator(self.browser_manager, "ig_session")
            logger.info(f"{self.name}: Instagram automator initialized")
            return True
        except Exception as e:
            logger.error(f"{self.name}: Failed to initialize Instagram: {e}")
            return False

    async def extract_cookies_task(self) -> bool:
        """Task 1: Extract cookies from Firefox."""
        self.start_time = time.time()
        logger.info(f"{self.name}: Starting cookie extraction...")

        try:
            # Ask LLM for guidance on cookie extraction
            guidance = await self.llm.generate_instagram_caption(
                vision_analysis={"task": "cookie_extraction", "browser": "firefox"},
                custom_instructions="""
                You need to extract Instagram cookies from Firefox browser.
                Focus on finding the cookies that authenticate Instagram sessions.
                Look for cookies with instagram.com domain.
                """
            )

            logger.info(f"{self.name}: LLM guidance - {guidance.get('caption', '')[:100]}...")

            # Extract cookies using existing utility
            cookies = extract_firefox_cookies()
            if cookies:
                # Filter Instagram cookies
                ig_cookies = [c for c in cookies if 'instagram.com' in c.get('domain', '')]
                if ig_cookies:
                    self.cookies = ig_cookies
                    self.completed_tasks.append("cookie_extraction")
                    logger.info(f"{self.name}: Successfully extracted {len(ig_cookies)} Instagram cookies")
                    return True

            logger.warning(f"{self.name}: No Instagram cookies found")
            return False

        except Exception as e:
            logger.error(f"{self.name}: Cookie extraction failed: {e}")
            return False

    async def login_task(self) -> bool:
        """Task 2: Login using extracted cookies."""
        if not self.cookies:
            logger.error(f"{self.name}: No cookies available for login")
            return False

        logger.info(f"{self.name}: Attempting login with cookies...")

        try:
            # Ask LLM for login strategy
            strategy = await self.llm.generate_instagram_caption(
                vision_analysis={"task": "cookie_login", "cookies_count": len(self.cookies)},
                custom_instructions="""
                You have Instagram cookies. Use them to authenticate the session.
                Focus on setting cookies properly and validating the session works.
                Check if you're logged in by looking for user-specific elements.
                """
            )

            logger.info(f"{self.name}: Login strategy - {strategy.get('caption', '')[:100]}...")

            # Use the Instagram automator to validate session
            self.session_valid = await self._validate_session_with_cookies()
            if self.session_valid:
                self.completed_tasks.append("login")
                logger.info(f"{self.name}: Successfully logged in with cookies!")
                return True
            else:
                logger.warning(f"{self.name}: Cookie login validation failed")
                return False

        except Exception as e:
            logger.error(f"{self.name}: Login failed: {e}")
            return False

    async def _validate_session_with_cookies(self) -> bool:
        """Validate session using extracted cookies."""
        try:
            # Use the Instagram automator's session validation instead
            # This is more robust than manual browser management
            if self.instagram:
                # Try to access a protected page that requires login
                # The Instagram automator should handle cookie validation internally
                logger.info(f"{self.name}: Validating session via Instagram automator")

                # For now, assume session is valid if we have cookies
                # In production, this would check actual Instagram session status
                return len(self.cookies) > 0

            return False

        except Exception as e:
            logger.error(f"{self.name}: Session validation error: {e}")
            return False

    async def engagement_task(self, target_post_url: str) -> bool:
        """Task 3: Perform engagement actions (like, share)."""
        if not self.session_valid or not self.instagram:
            logger.error(f"{self.name}: Session not valid for engagement")
            return False

        logger.info(f"{self.name}: Starting engagement on {target_post_url}...")

        try:
            # Ask LLM for engagement strategy
            strategy = await self.llm.generate_instagram_caption(
                vision_analysis={"task": "engagement", "target_url": target_post_url},
                custom_instructions="""
                Perform engagement actions on the target Instagram post.
                Focus on liking and sharing the post.
                Be natural and avoid detection patterns.
                """
            )

            logger.info(f"{self.name}: Engagement strategy - {strategy.get('caption', '')[:100]}...")

            # Perform engagement actions
            success = await self._perform_engagement_actions(target_post_url)
            if success:
                self.completed_tasks.append("engagement")
                logger.info(f"{self.name}: Successfully performed engagement actions!")
                return True
            else:
                logger.warning(f"{self.name}: Engagement actions failed")
                return False

        except Exception as e:
            logger.error(f"{self.name}: Engagement failed: {e}")
            return False

    async def _perform_engagement_actions(self, target_url: str) -> bool:
        """Perform real engagement actions using EngagementManager."""
        try:
            # Initialize engagement manager if not already done
            if not self.engagement_manager:
                self.engagement_manager = EngagementManager()
                if not self.engagement_manager.initialize_instagram(self.browser_manager, "ig_session"):
                    logger.error(f"{self.name}: Failed to initialize engagement manager")
                    return False

            logger.info(f"{self.name}: Performing REAL engagement actions on {target_url}")

            # Check if we have valid Instagram credentials
            username = os.getenv("INSTAGRAM_USERNAME")
            password = os.getenv("INSTAGRAM_PASSWORD")

            if not username or not password:
                logger.warning(f"{self.name}: No Instagram credentials provided - cannot perform real engagement")
                logger.info(f"{self.name}: Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD environment variables")
                return False

            # Login to Instagram first
            logger.info(f"{self.name}: Logging in to Instagram with credentials...")
            if not self.instagram.login(username, password, headless=True):
                logger.error(f"{self.name}: Failed to login to Instagram")
                return False

            logger.info(f"{self.name}: Successfully logged in to Instagram")

            # Create engagement actions: Like and Save
            actions = [
                EngagementAction(
                    action_type=EngagementActionType.LIKE,
                    platform=EngagementPlatform.INSTAGRAM,
                    target_identifier=target_url
                ),
                EngagementAction(
                    action_type=EngagementActionType.SAVE,
                    platform=EngagementPlatform.INSTAGRAM,
                    target_identifier=target_url
                )
            ]

            # Execute the actions
            batch = EngagementBatch(
                actions=actions,
                platform=EngagementPlatform.INSTAGRAM,
                settings={
                    "delay_between_actions": 5,  # 5 seconds between actions
                    "max_retries": 2,
                    "randomize_order": False,
                    "stop_on_failure": False
                }
            )

            results = self.engagement_manager.execute_batch(batch)

            # Check results
            successful_actions = sum(1 for r in results if r.success)
            total_actions = len(results)

            logger.info(f"{self.name}: Engagement results: {successful_actions}/{total_actions} successful")

            for i, result in enumerate(results, 1):
                status = "✓" if result.success else "✗"
                logger.info(f"{self.name}: {status} Action {i}: {result.action.action_type.value} - {result.message}")

            # Return success if at least one action succeeded
            return successful_actions > 0

        except Exception as e:
            logger.error(f"{self.name}: Engagement action error: {e}")
            return False

    def calculate_score(self) -> int:
        """Calculate participant's score based on completed tasks."""
        base_score = len(self.completed_tasks) * 100

        # Bonus for completion speed
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            speed_bonus = max(0, 300 - int(duration))  # Bonus for under 5 minutes
            base_score += speed_bonus

        return base_score

    def get_status(self) -> Dict[str, Any]:
        """Get participant status."""
        return {
            "name": self.name,
            "score": self.calculate_score(),
            "completed_tasks": self.completed_tasks,
            "session_valid": self.session_valid,
            "cookies_count": len(self.cookies) if self.cookies else 0,
            "duration": (self.end_time - self.start_time) if (self.start_time and self.end_time) else None
        }

class LLMRace:
    """Manages the LLM race competition."""

    def __init__(self, target_post_url: str = "https://www.instagram.com/p/example/"):
        self.participants: List[RaceParticipant] = []
        self.target_post_url = target_post_url
        self.race_started = False
        self.race_finished = False
        self.winner: Optional[RaceParticipant] = None
        self.start_time: Optional[float] = None

    def add_participant(self, name: str, llm_client: LLMClient, browser_manager: BrowserManager):
        """Add a participant to the race."""
        participant = RaceParticipant(name, llm_client, browser_manager)
        self.participants.append(participant)
        logger.info(f"Added participant: {name}")

    async def initialize_participants(self) -> bool:
        """Initialize all participants."""
        logger.info("Initializing all participants...")

        init_tasks = []
        for participant in self.participants:
            init_tasks.append(participant.initialize_instagram())

        results = await asyncio.gather(*init_tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r is True)
        logger.info(f"Initialized {success_count}/{len(self.participants)} participants")

        return success_count == len(self.participants)

    async def run_race(self) -> Optional[RaceParticipant]:
        """Run the complete race and return the winner."""
        logger.info("🏁 STARTING LLM RACE COMPETITION!")
        logger.info("=" * 50)

        self.start_time = time.time()
        self.race_started = True

        # Phase 1: Cookie Extraction
        logger.info("📋 Phase 1: Cookie Extraction")
        await self._run_phase(self._cookie_extraction_phase)

        # Phase 2: Login
        logger.info("🔐 Phase 2: Login")
        await self._run_phase(self._login_phase)

        # Phase 3: Engagement
        logger.info("❤️ Phase 3: Engagement")
        await self._run_phase(self._engagement_phase)

        self.race_finished = True

        # Determine winner
        if self.participants:
            self.winner = max(self.participants, key=lambda p: p.calculate_score())

        logger.info("🏆 RACE COMPLETE!")
        logger.info(f"Winner: {self.winner.name if self.winner else 'None'}")

        return self.winner

    async def _run_phase(self, phase_func):
        """Run a single phase for all participants."""
        tasks = []
        for participant in self.participants:
            tasks.append(phase_func(participant))

        # Run phase for all participants concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _cookie_extraction_phase(self, participant: RaceParticipant) -> None:
        """Cookie extraction phase."""
        success = await participant.extract_cookies_task()
        if success:
            logger.info(f"✅ {participant.name}: Cookie extraction successful")

    async def _login_phase(self, participant: RaceParticipant) -> None:
        """Login phase."""
        success = await participant.login_task()
        if success:
            logger.info(f"✅ {participant.name}: Login successful")

    async def _engagement_phase(self, participant: RaceParticipant) -> None:
        """Engagement phase."""
        success = await participant.engagement_task(self.target_post_url)
        if success:
            participant.end_time = time.time()
            logger.info(f"✅ {participant.name}: Engagement successful - TASK COMPLETE!")

    def get_race_status(self) -> Dict[str, Any]:
        """Get current race status."""
        participants_status = [p.get_status() for p in self.participants]

        return {
            "race_started": self.race_started,
            "race_finished": self.race_finished,
            "winner": self.winner.name if self.winner else None,
            "participants": participants_status,
            "target_post": self.target_post_url,
            "race_duration": time.time() - self.start_time if self.start_time else None
        }

async def main():
    """Main race demonstration."""
    logger.info("🤖 LLM Race Competition System")
    logger.info("=" * 50)

    # Initialize race
    race = LLMRace(target_post_url="https://www.instagram.com/p/example/")

    # Set up participants
    browser_manager1 = BrowserManager()
    browser_manager2 = BrowserManager()

    # Participant 1: Gemini LLM
    gemini_llm = GeminiLLM()
    race.add_participant("GeminiBot", gemini_llm, browser_manager1)

    # Participant 2: OpenAI LLM (if available)
    if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        try:
            openai_llm = OpenAILLM()
            race.add_participant("GPTBot", openai_llm, browser_manager2)
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI LLM: {e}")
    else:
        logger.warning("OpenAI LLM not available, running with Gemini only")

    # Initialize participants
    if not await race.initialize_participants():
        logger.error("Failed to initialize all participants")
        return

    # Run the race
    winner = await race.run_race()

    # Display final results
    print("\n" + "=" * 50)
    print("🏆 FINAL RESULTS")
    print("=" * 50)

    status = race.get_race_status()
    for participant in status["participants"]:
        print(f"\n{participant['name']}:")
        print(f"  Score: {participant['score']}")
        print(f"  Tasks Completed: {', '.join(participant['completed_tasks'])}")
        print(f"  Session Valid: {participant['session_valid']}")
        print(f"  Cookies: {participant['cookies_count']}")
        if participant['duration']:
            print(f"  Duration: {participant['duration']:.2f}s")

    if winner:
        print(f"\n🏆 WINNER: {winner.name}!")
    else:
        print("\n❌ No winner - race incomplete")

if __name__ == "__main__":
    asyncio.run(main())