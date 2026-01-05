"""
Engagement data models for social media interactions.

Defines standardized data structures for engagement actions, results,
and tracking across multiple platforms.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List
import datetime
import json

class EngagementActionType(Enum):
    """Types of engagement actions supported."""
    LIKE = "like"
    UNLIKE = "unlike"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    COMMENT = "comment"
    REPLY = "reply"
    SAVE = "save"
    UNSAVE = "unsave"
    SHARE = "share"
    STORY_VIEW = "story_view"
    DM_SEND = "dm_send"
    DM_REPLY = "dm_reply"

class EngagementPlatform(Enum):
    """Supported social media platforms."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"

class EngagementStatus(Enum):
    """Status of engagement actions."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"

@dataclass
class EngagementAction:
    """
    Base engagement action model.

    Attributes:
        action_type: Type of engagement action
        platform: Target platform
        target_identifier: URL, username, or post ID
        metadata: Additional action-specific data
        timestamp: When the action was created
        status: Current status
        error_message: Error details if failed
        retry_count: Number of retry attempts
    """
    action_type: EngagementActionType
    platform: EngagementPlatform
    target_identifier: str
    metadata: Optional[Dict] = None
    timestamp: datetime.datetime = datetime.datetime.now()
    status: EngagementStatus = EngagementStatus.PENDING
    error_message: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "action_type": self.action_type.value,
            "platform": self.platform.value,
            "target_identifier": self.target_identifier,
            "metadata": self.metadata or {},
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "error_message": self.error_message,
            "retry_count": self.retry_count
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'EngagementAction':
        """Create from dictionary."""
        return cls(
            action_type=EngagementActionType(data["action_type"]),
            platform=EngagementPlatform(data["platform"]),
            target_identifier=data["target_identifier"],
            metadata=data.get("metadata", {}),
            timestamp=datetime.datetime.fromisoformat(data["timestamp"]),
            status=EngagementStatus(data["status"]),
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0)
        )

@dataclass
class LikeAction(EngagementAction):
    """Like engagement action."""
    def __init__(self, platform: EngagementPlatform, target_identifier: str):
        super().__init__(
            action_type=EngagementActionType.LIKE,
            platform=platform,
            target_identifier=target_identifier
        )

@dataclass
class FollowAction(EngagementAction):
    """Follow engagement action."""
    def __init__(self, platform: EngagementPlatform, target_identifier: str):
        super().__init__(
            action_type=EngagementActionType.FOLLOW,
            platform=platform,
            target_identifier=target_identifier
        )

@dataclass
class CommentAction(EngagementAction):
    """Comment engagement action."""
    def __init__(self, platform: EngagementPlatform, target_identifier: str, comment_text: str):
        super().__init__(
            action_type=EngagementActionType.COMMENT,
            platform=platform,
            target_identifier=target_identifier,
            metadata={"comment_text": comment_text}
        )

@dataclass
class SaveAction(EngagementAction):
    """Save engagement action."""
    def __init__(self, platform: EngagementPlatform, target_identifier: str):
        super().__init__(
            action_type=EngagementActionType.SAVE,
            platform=platform,
            target_identifier=target_identifier
        )

@dataclass
class ShareAction(EngagementAction):
    """Share engagement action."""
    def __init__(self, platform: EngagementPlatform, target_identifier: str, method: str = "dm"):
        super().__init__(
            action_type=EngagementActionType.SHARE,
            platform=platform,
            target_identifier=target_identifier,
            metadata={"method": method}
        )

@dataclass
class EngagementResult:
    """
    Result of an engagement action.

    Attributes:
        action: The original engagement action
        success: Whether the action succeeded
        message: Result message
        timestamp: When the action completed
        platform_data: Platform-specific response data
    """
    action: EngagementAction
    success: bool
    message: str
    timestamp: datetime.datetime = datetime.datetime.now()
    platform_data: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "action": self.action.to_dict(),
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "platform_data": self.platform_data or {}
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'EngagementResult':
        """Create from dictionary."""
        return cls(
            action=EngagementAction.from_dict(data["action"]),
            success=data["success"],
            message=data["message"],
            timestamp=datetime.datetime.fromisoformat(data["timestamp"]),
            platform_data=data.get("platform_data", {})
        )

@dataclass
class EngagementBatch:
    """
    Batch of engagement actions for sequential processing.

    Attributes:
        actions: List of engagement actions
        platform: Target platform
        settings: Batch processing settings
    """
    actions: List[EngagementAction]
    platform: EngagementPlatform
    settings: Dict = None

    def __init__(self, actions: List[EngagementAction], platform: EngagementPlatform, settings: Dict = None):
        self.actions = actions
        self.platform = platform
        self.settings = settings or {
            "delay_between_actions": 30,  # seconds
            "max_retries": 3,
            "randomize_order": True,
            "stop_on_failure": False
        }

    def add_action(self, action: EngagementAction):
        """Add an action to the batch."""
        self.actions.append(action)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "actions": [action.to_dict() for action in self.actions],
            "platform": self.platform.value,
            "settings": self.settings
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'EngagementBatch':
        """Create from dictionary."""
        return cls(
            actions=[EngagementAction.from_dict(action_data) for action_data in data["actions"]],
            platform=EngagementPlatform(data["platform"]),
            settings=data.get("settings")
        )

class EngagementStorage:
    """
    Storage interface for engagement actions and results.

    Provides methods for persisting engagement data to various backends.
    """
    def __init__(self, storage_backend: str = "sqlite"):
        self.storage_backend = storage_backend

    def save_action(self, action: EngagementAction) -> bool:
        """Save an engagement action."""
        raise NotImplementedError("Subclasses must implement this method")

    def save_result(self, result: EngagementResult) -> bool:
        """Save an engagement result."""
        raise NotImplementedError("Subclasses must implement this method")

    def get_actions(self, platform: Optional[EngagementPlatform] = None) -> List[EngagementAction]:
        """Get engagement actions, optionally filtered by platform."""
        raise NotImplementedError("Subclasses must implement this method")

    def get_results(self, platform: Optional[EngagementPlatform] = None) -> List[EngagementResult]:
        """Get engagement results, optionally filtered by platform."""
        raise NotImplementedError("Subclasses must implement this method")

    def get_action_history(self, limit: int = 100) -> List[EngagementResult]:
        """Get recent engagement history."""
        raise NotImplementedError("Subclasses must implement this method")