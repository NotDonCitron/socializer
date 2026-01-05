"""
AI-powered decision making for autonomous Instagram posting.
Evaluates content, timing, and account strategy to make posting decisions.
"""
import datetime
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class PostingDecision(Enum):
    POST_NOW = "post_now"
    POST_LATER = "post_later"
    SKIP = "skip"
    QUEUE = "queue"

@dataclass
class AccountStrategy:
    """Account posting strategy and goals."""
    target_audience: str = "general"  # general, lifestyle, business, creative, etc.
    posting_frequency: str = "moderate"  # low, moderate, high
    preferred_times: List[str] = None  # ["09:00", "12:00", "18:00"]
    content_themes: List[str] = None  # ["nature", "urban", "people", "food"]
    avoid_hashtags: List[str] = None  # hashtags to avoid

    def __post_init__(self):
        if self.preferred_times is None:
            self.preferred_times = ["08:00", "12:00", "18:00", "20:00"]
        if self.content_themes is None:
            self.content_themes = ["general"]
        if self.avoid_hashtags is None:
            self.avoid_hashtags = []

@dataclass
class ContentEvaluation:
    """AI evaluation of content quality and fit."""
    vision_analysis: Dict
    caption_data: Dict
    quality_score: float  # 0-1
    relevance_score: float  # 0-1
    engagement_potential: str  # high, medium, low
    mood_match: str  # excellent, good, fair, poor

class AIDecisionMaker:
    """Makes autonomous posting decisions based on content analysis and strategy."""

    def __init__(self, strategy: AccountStrategy):
        self.strategy = strategy
        self.posting_history: List[datetime.datetime] = []
        self.daily_post_count = 0
        self.last_post_time: Optional[datetime.datetime] = None

    def evaluate_content(self, image_path: str, vision_analysis: Dict, caption_data: Dict) -> ContentEvaluation:
        """Evaluate content quality and strategic fit."""

        # Quality score based on image analysis
        quality_score = self._calculate_quality_score(vision_analysis)

        # Relevance score based on account strategy
        relevance_score = self._calculate_relevance_score(vision_analysis)

        # Get engagement potential from caption generation
        engagement_potential = caption_data.get("engagement_potential", "medium")

        # Mood match from caption generation
        mood_match = caption_data.get("mood_match", "good")

        return ContentEvaluation(
            vision_analysis=vision_analysis,
            caption_data=caption_data,
            quality_score=quality_score,
            relevance_score=relevance_score,
            engagement_potential=engagement_potential,
            mood_match=mood_match
        )

    def _calculate_quality_score(self, vision_analysis: Dict) -> float:
        """Calculate content quality score (0-1)."""
        score = 0.5  # Base score

        # Boost for clear subjects
        objects = vision_analysis.get('objects', [])
        if len(objects) > 0 and 'unknown' not in objects:
            score += 0.2

        # Boost for positive mood
        mood = vision_analysis.get('mood', '').lower()
        if any(word in mood for word in ['happy', 'peaceful', 'joyful', 'beautiful']):
            score += 0.15
        elif any(word in mood for word in ['dark', 'sad', 'angry']):
            score -= 0.1

        # Boost for good composition (people or interesting scenes)
        people_count = vision_analysis.get('people_count', 0)
        scene = vision_analysis.get('scene', '').lower()

        if people_count > 0:
            score += 0.1
        if scene in ['nature', 'urban', 'outdoor']:
            score += 0.1

        # Penalize for unclear or generic content
        if vision_analysis.get('text_content') and len(vision_analysis['text_content']) > 50:
            score -= 0.1  # Too much text might be cluttered

        return max(0.0, min(1.0, score))

    def _calculate_relevance_score(self, vision_analysis: Dict) -> float:
        """Calculate how well content fits account strategy (0-1)."""
        score = 0.5  # Base score

        # Theme matching
        scene = vision_analysis.get('scene', '').lower()
        objects = [obj.lower() for obj in vision_analysis.get('objects', [])]

        for theme in self.strategy.content_themes:
            theme_lower = theme.lower()
            if theme_lower in scene or any(theme_lower in obj for obj in objects):
                score += 0.3
                break

        # Audience alignment
        audience = self.strategy.target_audience.lower()
        if audience == "lifestyle" and (scene in ['urban', 'indoor'] or 'people' in objects):
            score += 0.2
        elif audience == "nature" and scene == "nature":
            score += 0.2
        elif audience == "business" and any(word in ' '.join(objects) for word in ['office', 'computer', 'meeting']):
            score += 0.2

        return max(0.0, min(1.0, score))

    def decide_posting_action(self, evaluation: ContentEvaluation) -> Tuple[PostingDecision, Optional[datetime.datetime]]:
        """
        Decide whether and when to post based on content evaluation and strategy.

        Returns:
            (decision, scheduled_time)
        """

        # Check quality threshold
        min_quality = 0.4
        if evaluation.quality_score < min_quality:
            return PostingDecision.SKIP, None

        # Check relevance threshold
        min_relevance = 0.3
        if evaluation.relevance_score < min_relevance:
            return PostingDecision.SKIP, None

        # Check posting frequency limits
        now = datetime.datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Reset daily count if it's a new day
        if self.last_post_time and self.last_post_time < today_start:
            self.daily_post_count = 0

        # Frequency limits
        max_daily_posts = {
            'low': 1,
            'moderate': 3,
            'high': 5
        }.get(self.strategy.posting_frequency, 3)

        if self.daily_post_count >= max_daily_posts:
            return PostingDecision.QUEUE, None  # Queue for tomorrow

        # Check timing
        current_hour = now.hour
        preferred_hours = [int(time.split(':')[0]) for time in self.strategy.preferred_times]

        # If current time is within preferred posting window
        if current_hour in preferred_hours:
            return PostingDecision.POST_NOW, None

        # Find next preferred time
        next_post_time = self._find_next_preferred_time(now, preferred_hours)

        # If next time is within 2 hours, schedule it
        if next_post_time and (next_post_time - now).total_seconds() < 7200:  # 2 hours
            return PostingDecision.POST_LATER, next_post_time

        # Otherwise, queue for optimal time tomorrow
        return PostingDecision.QUEUE, self._get_optimal_tomorrow_time()

    def _find_next_preferred_time(self, now: datetime.datetime, preferred_hours: List[int]) -> Optional[datetime.datetime]:
        """Find the next preferred posting time today."""
        current_hour = now.hour

        for hour in sorted(preferred_hours):
            if hour > current_hour:
                next_time = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                # Add some randomness to avoid exact timing
                next_time += datetime.timedelta(minutes=random.randint(0, 59))
                return next_time

        return None  # No more times today

    def _get_optimal_tomorrow_time(self) -> datetime.datetime:
        """Get optimal posting time for tomorrow."""
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        tomorrow = tomorrow.replace(hour=12, minute=0, second=0, microsecond=0)  # Default to noon

        # Pick a random preferred time for tomorrow
        if self.strategy.preferred_times:
            random_time = random.choice(self.strategy.preferred_times)
            hour, minute = map(int, random_time.split(':'))
            tomorrow = tomorrow.replace(hour=hour, minute=minute)

        return tomorrow

    def record_post(self, post_time: datetime.datetime):
        """Record a successful post for frequency tracking."""
        self.posting_history.append(post_time)
        self.last_post_time = post_time
        self.daily_post_count += 1

        # Keep only recent history
        cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
        self.posting_history = [t for t in self.posting_history if t > cutoff]

    def should_post_based_on_engagement(self, recent_engagement_rate: float) -> bool:
        """Decide whether to continue posting based on recent engagement."""
        # Adjust posting frequency based on engagement
        if recent_engagement_rate > 0.05:  # >5% engagement
            return True  # Continue posting
        elif recent_engagement_rate > 0.02:  # >2% engagement
            return random.random() < 0.7  # 70% chance
        else:  # Low engagement
            return random.random() < 0.3  # 30% chance

        return True