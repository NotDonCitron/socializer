"""
Account scheduler for intelligent multi-account social media automation.

Manages timing, rotation, and coordination of engagement tasks across multiple accounts.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
import time
import threading
import heapq
import random
from radar.account_pool import AccountPool, Account, AccountPriority, AccountStatus


class TaskType(Enum):
    """Types of engagement tasks."""
    LIKE = "like"
    FOLLOW = "follow"
    COMMENT = "comment"
    SAVE = "save"
    SHARE = "share"
    UNFOLLOW = "unfollow"
    VIEW_STORY = "view_story"
    SEND_DM = "send_dm"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass(order=True)
class ScheduledTask:
    """A scheduled engagement task."""
    scheduled_time: datetime
    task_id: str = field(compare=False)
    account_id: str = field(compare=False)
    platform: str = field(compare=False)
    task_type: TaskType = field(compare=False)
    target_identifier: str = field(compare=False)
    priority: TaskPriority = field(compare=False, default=TaskPriority.NORMAL)
    metadata: Dict[str, Any] = field(compare=False, default_factory=dict)
    created_at: datetime = field(compare=False, default_factory=datetime.now)
    retry_count: int = field(compare=False, default=0)
    max_retries: int = field(compare=False, default=3)
    callback: Optional[Callable] = field(compare=False, default=None)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scheduled_time": self.scheduled_time.isoformat(),
            "task_id": self.task_id,
            "account_id": self.account_id,
            "platform": self.platform,
            "task_type": self.task_type.value,
            "target_identifier": self.target_identifier,
            "priority": self.priority.value,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], callback: Optional[Callable] = None) -> "ScheduledTask":
        """Deserialize from dictionary."""
        return cls(
            scheduled_time=datetime.fromisoformat(data["scheduled_time"]),
            task_id=data["task_id"],
            account_id=data["account_id"],
            platform=data["platform"],
            task_type=TaskType(data["task_type"]),
            target_identifier=data["target_identifier"],
            priority=TaskPriority(data.get("priority", "normal")),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            callback=callback
        )


class AccountScheduler:
    """
    Intelligent scheduler for coordinating engagement tasks across multiple accounts.

    Features:
    - Time-based task scheduling with jitter
    - Account rotation and cooldown management
    - Priority-based task queuing
    - Rate limiting and burst control
    - Platform-specific timing rules
    """

    def __init__(self, account_pool: AccountPool, db_path: str = "data/radar.sqlite"):
        """
        Initialize account scheduler.

        Args:
            account_pool: AccountPool instance
            db_path: Database path for persistence
        """
        self.account_pool = account_pool
        self.db_path = db_path

        # Task queue (min-heap by scheduled_time)
        self._task_queue: List[ScheduledTask] = []
        self._queue_lock = threading.Lock()

        # Active tasks tracking
        self._active_tasks: Dict[str, ScheduledTask] = {}
        self._active_lock = threading.Lock()

        # Scheduler control
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None

        # Platform-specific timing rules
        self._platform_rules = {
            "instagram": {
                "min_delay_between_tasks": 30,  # seconds
                "max_burst_size": 5,  # max tasks per burst
                "burst_cooldown": 300,  # seconds after burst
                "daily_limit": 200,  # max tasks per day per account
                "hourly_limit": 30,  # max tasks per hour per account
                "jitter_range": (0.8, 1.2),  # timing variation
            },
            "tiktok": {
                "min_delay_between_tasks": 20,
                "max_burst_size": 3,
                "burst_cooldown": 180,
                "daily_limit": 150,
                "hourly_limit": 25,
                "jitter_range": (0.7, 1.3),
            }
        }

        # Task history for analytics
        self._task_history: List[Dict[str, Any]] = []
        self._history_lock = threading.Lock()

    def start_scheduler(self):
        """Start the background scheduler thread."""
        if self._running:
            return

        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def stop_scheduler(self):
        """Stop the background scheduler."""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)

    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                current_time = datetime.now()

                # Process due tasks
                self._process_due_tasks(current_time)

                # Small sleep to prevent busy waiting
                time.sleep(1)

            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(5)  # Longer sleep on error

    def _process_due_tasks(self, current_time: datetime):
        """Process tasks that are due for execution."""
        with self._queue_lock:
            # Find due tasks
            due_tasks = []
            remaining_tasks = []

            for task in self._task_queue:
                if task.scheduled_time <= current_time:
                    due_tasks.append(task)
                else:
                    remaining_tasks.append(task)

            self._task_queue = remaining_tasks

            # Execute due tasks
            for task in due_tasks:
                self._execute_task(task)

    def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task."""
        with self._active_lock:
            self._active_tasks[task.task_id] = task

        try:
            # Check if account is available
            account = self.account_pool.get_account(task.account_id)
            if not account or account.status != AccountStatus.ACTIVE:
                self._handle_task_failure(task, "Account not available")
                return

            if not account.can_perform_engagement():
                self._handle_task_failure(task, "Account at usage limit")
                return

            # Execute the task via callback
            if task.callback:
                success = task.callback(task)
            else:
                # Default execution - just record the engagement
                account.record_engagement(success=True)
                self.account_pool.add_account(account)
                success = True

            # Record result
            self._record_task_result(task, success)

            if success:
                self._handle_task_success(task)
            else:
                self._handle_task_failure(task, "Task execution failed")

        except Exception as e:
            self._handle_task_failure(task, f"Execution error: {e}")

        finally:
            with self._active_lock:
                self._active_tasks.pop(task.task_id, None)

    def _handle_task_success(self, task: ScheduledTask):
        """Handle successful task completion."""
        # Update account statistics
        self.account_pool.update_account_stats(task.account_id, engagement_success=True)

        # Record in history
        self._add_to_history(task, "success", None)

    def _handle_task_failure(self, task: ScheduledTask, reason: str):
        """Handle task failure with retry logic."""
        task.retry_count += 1

        if task.retry_count < task.max_retries:
            # Schedule retry with exponential backoff
            retry_delay = 60 * (2 ** task.retry_count)  # 1min, 2min, 4min
            retry_time = datetime.now() + timedelta(seconds=retry_delay)

            task.scheduled_time = retry_time
            self.schedule_task(task)
        else:
            # Max retries reached
            self._record_task_result(task, False)
            self.account_pool.update_account_stats(task.account_id, engagement_success=False)
            self._add_to_history(task, "failed", reason)

    def _record_task_result(self, task: ScheduledTask, success: bool):
        """Record task execution result."""
        self._add_to_history(task, "success" if success else "failed", None)

    def _add_to_history(self, task: ScheduledTask, status: str, error: Optional[str]):
        """Add task to execution history."""
        with self._history_lock:
            history_entry = {
                "task_id": task.task_id,
                "account_id": task.account_id,
                "platform": task.platform,
                "task_type": task.task_type.value,
                "target_identifier": task.target_identifier,
                "status": status,
                "error": error,
                "scheduled_time": task.scheduled_time.isoformat(),
                "executed_at": datetime.now().isoformat(),
                "retry_count": task.retry_count,
                "priority": task.priority.value
            }

            self._task_history.append(history_entry)

            # Keep only recent history (last 1000 entries)
            if len(self._task_history) > 1000:
                self._task_history = self._task_history[-1000:]

    def schedule_task(self, task: ScheduledTask) -> bool:
        """
        Schedule a task for execution.

        Args:
            task: Task to schedule

        Returns:
            True if scheduled successfully
        """
        # Validate task
        account = self.account_pool.get_account(task.account_id)
        if not account:
            return False

        if account.status != AccountStatus.ACTIVE:
            return False

        # Check platform-specific rules
        rules = self._platform_rules.get(task.platform, self._platform_rules["instagram"])
        if not self._validate_task_timing(task, rules):
            return False

        # Add to queue
        with self._queue_lock:
            heapq.heappush(self._task_queue, task)

        return True

    def _validate_task_timing(self, task: ScheduledTask, rules: Dict[str, Any]) -> bool:
        """
        Validate task timing against platform rules.

        Args:
            task: Task to validate
            rules: Platform timing rules

        Returns:
            True if timing is valid
        """
        account = self.account_pool.get_account(task.account_id)
        if not account:
            return False

        # Check if account would exceed limits
        if account.todays_usage >= rules["daily_limit"]:
            return False

        if account.last_hour_usage >= rules["hourly_limit"]:
            return False

        return True

    def schedule_engagement_batch(self, platform: str, task_type: TaskType,
                                target_identifiers: List[str],
                                priority: TaskPriority = TaskPriority.NORMAL,
                                delay_between_tasks: int = 60,
                                callback: Optional[Callable] = None) -> List[str]:
        """
        Schedule a batch of engagement tasks with intelligent account selection.

        Args:
            platform: Target platform
            task_type: Type of engagement task
            target_identifiers: List of target identifiers (URLs, usernames, etc.)
            priority: Task priority
            delay_between_tasks: Minimum delay between tasks in seconds
            callback: Task execution callback

        Returns:
            List of scheduled task IDs
        """
        scheduled_tasks = []
        current_time = datetime.now()

        for i, target_id in enumerate(target_identifiers):
            # Select account for this task
            account = self.account_pool.select_account(
                platform=platform,
                priority_preference=AccountPriority.SECONDARY,
                exclude_recent=True
            )

            if not account:
                print(f"No available account for {platform} task {i+1}")
                continue

            # Calculate schedule time with jitter
            schedule_time = current_time + timedelta(seconds=i * delay_between_tasks)
            schedule_time = self._apply_timing_jitter(schedule_time, platform)

            # Create task
            task = ScheduledTask(
                scheduled_time=schedule_time,
                task_id=f"{platform}_{task_type.value}_{account.id}_{int(time.time())}_{i}",
                account_id=account.id,
                platform=platform,
                task_type=task_type,
                target_identifier=target_id,
                priority=priority,
                callback=callback
            )

            # Schedule task
            if self.schedule_task(task):
                scheduled_tasks.append(task.task_id)

        return scheduled_tasks

    def _apply_timing_jitter(self, base_time: datetime, platform: str) -> datetime:
        """
        Apply timing jitter to prevent detection patterns.

        Args:
            base_time: Base schedule time
            platform: Target platform

        Returns:
            Time with jitter applied
        """
        rules = self._platform_rules.get(platform, self._platform_rules["instagram"])
        jitter_min, jitter_max = rules["jitter_range"]

        # Apply random jitter within range
        jitter_factor = random.uniform(jitter_min, jitter_max)
        jitter_seconds = int(60 * (jitter_factor - 1.0))  # Convert to seconds

        return base_time + timedelta(seconds=jitter_seconds)

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if task was cancelled
        """
        with self._queue_lock:
            # Remove from queue
            self._task_queue = [t for t in self._task_queue if t.task_id != task_id]

        with self._active_lock:
            # Cancel if currently executing
            active_task = self._active_tasks.get(task_id)
            if active_task:
                # Note: In a real implementation, you'd need a way to interrupt running tasks
                del self._active_tasks[task_id]
                return True

        return True

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status."""
        with self._queue_lock:
            queued_tasks = len(self._task_queue)

        with self._active_lock:
            active_tasks = len(self._active_tasks)

        # Group by platform and type
        platform_stats = {}
        for task in self._task_queue:
            platform = task.platform
            task_type = task.task_type.value

            if platform not in platform_stats:
                platform_stats[platform] = {}

            if task_type not in platform_stats[platform]:
                platform_stats[platform][task_type] = 0

            platform_stats[platform][task_type] += 1

        return {
            "queued_tasks": queued_tasks,
            "active_tasks": active_tasks,
            "total_pending": queued_tasks + active_tasks,
            "platform_breakdown": platform_stats
        }

    def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent task execution history.

        Args:
            limit: Maximum number of history entries to return

        Returns:
            List of history entries
        """
        with self._history_lock:
            return self._task_history[-limit:] if self._task_history else []

    def get_next_task_time(self, platform: Optional[str] = None) -> Optional[datetime]:
        """
        Get the scheduled time of the next task.

        Args:
            platform: Optional platform filter

        Returns:
            Next task time or None if no tasks scheduled
        """
        with self._queue_lock:
            for task in self._task_queue:
                if platform is None or task.platform == platform:
                    return task.scheduled_time

        return None

    def clear_queue(self, platform: Optional[str] = None):
        """
        Clear all queued tasks.

        Args:
            platform: Optional platform filter (clear all if None)
        """
        with self._queue_lock:
            if platform:
                self._task_queue = [t for t in self._task_queue if t.platform != platform]
            else:
                self._task_queue.clear()

    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get comprehensive scheduler statistics."""
        queue_status = self.get_queue_status()
        history = self.get_task_history(1000)

        # Calculate success rates
        successful_tasks = sum(1 for h in history if h["status"] == "success")
        total_completed = len([h for h in history if h["status"] in ["success", "failed"]])
        success_rate = successful_tasks / total_completed if total_completed > 0 else 1.0

        # Platform breakdown
        platform_success = {}
        for entry in history:
            platform = entry["platform"]
            if platform not in platform_success:
                platform_success[platform] = {"total": 0, "successful": 0}

            platform_success[platform]["total"] += 1
            if entry["status"] == "success":
                platform_success[platform]["successful"] += 1

        for stats in platform_success.values():
            stats["success_rate"] = stats["successful"] / stats["total"] if stats["total"] > 0 else 1.0

        return {
            "queue_status": queue_status,
            "overall_success_rate": success_rate,
            "total_completed_tasks": total_completed,
            "successful_tasks": successful_tasks,
            "platform_success_rates": platform_success,
            "scheduler_running": self._running
        }


# Convenience functions for common operations

def schedule_like_batch(scheduler: AccountScheduler, platform: str,
                       post_urls: List[str], **kwargs) -> List[str]:
    """
    Schedule a batch of like tasks.

    Args:
        scheduler: AccountScheduler instance
        platform: Target platform
        post_urls: List of post URLs to like
        **kwargs: Additional scheduling options

    Returns:
        List of scheduled task IDs
    """
    return scheduler.schedule_engagement_batch(
        platform=platform,
        task_type=TaskType.LIKE,
        target_identifiers=post_urls,
        **kwargs
    )


def schedule_follow_batch(scheduler: AccountScheduler, platform: str,
                         usernames: List[str], **kwargs) -> List[str]:
    """
    Schedule a batch of follow tasks.

    Args:
        scheduler: AccountScheduler instance
        platform: Target platform
        usernames: List of usernames to follow
        **kwargs: Additional scheduling options

    Returns:
        List of scheduled task IDs
    """
    return scheduler.schedule_engagement_batch(
        platform=platform,
        task_type=TaskType.FOLLOW,
        target_identifiers=usernames,
        **kwargs
    )


def schedule_comment_batch(scheduler: AccountScheduler, platform: str,
                          comments: List[Tuple[str, str]], **kwargs) -> List[str]:
    """
    Schedule a batch of comment tasks.

    Args:
        scheduler: AccountScheduler instance
        platform: Target platform
        comments: List of (post_url, comment_text) tuples
        **kwargs: Additional scheduling options

    Returns:
        List of scheduled task IDs
    """
    task_ids = []

    for post_url, comment_text in comments:
        # Select account
        account = scheduler.account_pool.select_account(platform=platform)

        if account:
            task = ScheduledTask(
                scheduled_time=datetime.now(),
                task_id=f"{platform}_comment_{account.id}_{int(time.time())}",
                account_id=account.id,
                platform=platform,
                task_type=TaskType.COMMENT,
                target_identifier=post_url,
                metadata={"comment_text": comment_text},
                **kwargs
            )

            if scheduler.schedule_task(task):
                task_ids.append(task.task_id)

    return task_ids