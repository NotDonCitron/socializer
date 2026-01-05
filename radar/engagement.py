"""
Engagement manager for batch operations and rate limiting.

Provides high-level engagement workflows, batch processing,
and rate limiting across multiple platforms.
"""
import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime
from radar.engagement_models import EngagementAction, EngagementResult, EngagementBatch, EngagementPlatform, EngagementStatus
from radar.instagram import InstagramAutomator
from radar.tiktok import TikTokAutomator
from radar.browser import BrowserManager

# Configure logging
logger = logging.getLogger(__name__)

class EngagementManager:
    """
    High-level engagement manager for batch operations.

    Handles rate limiting, error recovery, and cross-platform engagement workflows.
    """

    def __init__(self):
        self.instagram_automator: Optional[InstagramAutomator] = None
        self.tiktok_automator: Optional[TikTokAutomator] = None
        self.rate_limits = {
            EngagementPlatform.INSTAGRAM: {
                'min_delay': 30,  # seconds
                'max_delay': 60,
                'max_actions_per_hour': 120,
                'max_daily_actions': 500,
                'max_sequential_actions': 10
            },
            EngagementPlatform.TIKTOK: {
                'min_delay': 20,  # seconds
                'max_delay': 45,
                'max_actions_per_hour': 180,
                'max_daily_actions': 800,
                'max_sequential_actions': 15
            }
        }
        self.action_counts = {
            EngagementPlatform.INSTAGRAM: 0,
            EngagementPlatform.TIKTOK: 0
        }
        self.last_action_times = {
            EngagementPlatform.INSTAGRAM: 0,
            EngagementPlatform.TIKTOK: 0
        }
        # Monitoring and safety features
        self.daily_action_counts = {
            EngagementPlatform.INSTAGRAM: 0,
            EngagementPlatform.TIKTOK: 0
        }
        self.sequential_action_counts = {
            EngagementPlatform.INSTAGRAM: 0,
            EngagementPlatform.TIKTOK: 0
        }
        self.last_daily_reset = {
            EngagementPlatform.INSTAGRAM: datetime.now().date(),
            EngagementPlatform.TIKTOK: datetime.now().date()
        }
        self.error_counts = {
            EngagementPlatform.INSTAGRAM: 0,
            EngagementPlatform.TIKTOK: 0
        }
        self.session_start_time = datetime.now()
        self.activity_log = []
        self.safety_enabled = True
        logger.info("EngagementManager initialized with safety features enabled")

    def initialize_instagram(self, manager: BrowserManager, user_data_dir: str) -> bool:
        """Initialize Instagram automator."""
        try:
            self.instagram_automator = InstagramAutomator(manager, user_data_dir)
            return True
        except Exception as e:
            print(f"Failed to initialize Instagram automator: {e}")
            return False

    def initialize_tiktok(self, manager: BrowserManager, user_data_dir: str) -> bool:
        """Initialize TikTok automator."""
        try:
            self.tiktok_automator = TikTokAutomator(manager, user_data_dir)
            return True
        except Exception as e:
            print(f"Failed to initialize TikTok automator: {e}")
            return False

    def _apply_rate_limiting(self, platform: EngagementPlatform):
        """Apply rate limiting based on platform rules."""
        now = time.time()
        last_time = self.last_action_times.get(platform, 0)

        # Calculate time since last action
        time_since_last = now - last_time

        # Get rate limit settings
        limits = self.rate_limits.get(platform, {})
        min_delay = limits.get('min_delay', 30)
        max_delay = limits.get('max_delay', 60)

        # Calculate dynamic delay based on recent activity
        if time_since_last < min_delay:
            # We're going too fast, add the remaining delay
            remaining_delay = min_delay - time_since_last
            print(f"Rate limiting: Waiting {remaining_delay:.1f}s before next {platform.value} action")
            time.sleep(remaining_delay)

        # Add random human-like delay
        human_delay = random.uniform(min_delay, max_delay)
        print(f"Human-like delay: Waiting {human_delay:.1f}s before next action")
        time.sleep(human_delay)

        # Update counters
        self.action_counts[platform] = self.action_counts.get(platform, 0) + 1
        self.last_action_times[platform] = time.time()

        # Check hourly limits (reset if needed)
        self._check_hourly_limits(platform)

    def _check_hourly_limits(self, platform: EngagementPlatform):
        """Check and enforce hourly action limits."""
        limits = self.rate_limits.get(platform, {})
        max_per_hour = limits.get('max_actions_per_hour', 100)

        # Simple implementation - in production would track per-hour windows
        if self.action_counts[platform] >= max_per_hour:
            print(f"Warning: Approaching hourly limit for {platform.value}. Consider slowing down.")
            # Reset counter (simple approach - real implementation would use sliding window)
            self.action_counts[platform] = 0

    def _check_safety_limits(self, platform: EngagementPlatform) -> bool:
        """Check if action would exceed safety limits."""
        if not self.safety_enabled:
            return True

        current_date = datetime.now().date()
        
        # Reset daily counters if new day
        if current_date > self.last_daily_reset[platform]:
            self.daily_action_counts[platform] = 0
            self.last_daily_reset[platform] = current_date
            self.sequential_action_counts[platform] = 0

        limits = self.rate_limits.get(platform, {})
        
        # Check daily limits
        max_daily = limits.get('max_daily_actions', 500)
        if self.daily_action_counts[platform] >= max_daily:
            logger.warning(f"Daily action limit reached for {platform.value}: {max_daily}")
            return False

        # Check sequential limits
        max_sequential = limits.get('max_sequential_actions', 10)
        if self.sequential_action_counts[platform] >= max_sequential:
            logger.warning(f"Sequential action limit reached for {platform.value}: {max_sequential}")
            # Force a longer break
            break_duration = random.uniform(300, 600)  # 5-10 minutes
            print(f"Safety break: Pausing for {break_duration/60:.1f} minutes to avoid detection")
            time.sleep(break_duration)
            self.sequential_action_counts[platform] = 0

        return True

    def _update_counters(self, platform: EngagementPlatform, success: bool):
        """Update all counters after an action."""
        current_date = datetime.now().date()
        
        # Reset daily counters if new day
        if current_date > self.last_daily_reset[platform]:
            self.daily_action_counts[platform] = 0
            self.last_daily_reset[platform] = current_date
            self.sequential_action_counts[platform] = 0

        if success:
            self.daily_action_counts[platform] += 1
            self.sequential_action_counts[platform] += 1
        else:
            self.sequential_action_counts[platform] = 0  # Reset on failure
            self.error_counts[platform] += 1

    def _log_activity(self, action: EngagementAction, result: EngagementResult):
        """Log activity for monitoring."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "platform": action.platform.value,
            "action_type": action.action_type.value,
            "target": action.target_identifier,
            "success": result.success,
            "message": result.message,
            "session_duration": (datetime.now() - self.session_start_time).total_seconds()
        }
        self.activity_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.activity_log) > 1000:
            self.activity_log = self.activity_log[-1000:]

    def _execute_single_action(self, action: EngagementAction) -> EngagementResult:
        """Execute a single engagement action."""
        try:
            # Apply rate limiting
            self._apply_rate_limiting(action.platform)

            # Execute based on platform
            if action.platform == EngagementPlatform.INSTAGRAM:
                if not self.instagram_automator:
                    return EngagementResult(
                        action=action,
                        success=False,
                        message="Instagram automator not initialized"
                    )

                # Route to appropriate method
                if action.action_type.name == "LIKE":
                    return self.instagram_automator.like_post(action.target_identifier)
                elif action.action_type.name == "FOLLOW":
                    return self.instagram_automator.follow_user(action.target_identifier)
                elif action.action_type.name == "COMMENT":
                    return self.instagram_automator.comment_on_post(
                        action.target_identifier,
                        action.metadata.get("comment_text", "")
                    )
                elif action.action_type.name == "SAVE":
                    return self.instagram_automator.save_post(action.target_identifier)
                elif action.action_type.name == "SHARE":
                    return self.instagram_automator.share_post(
                        action.target_identifier,
                        action.metadata.get("method", "dm")
                    )
                else:
                    return EngagementResult(
                        action=action,
                        success=False,
                        message=f"Unsupported Instagram action: {action.action_type}"
                    )

            elif action.platform == EngagementPlatform.TIKTOK:
                if not self.tiktok_automator:
                    return EngagementResult(
                        action=action,
                        success=False,
                        message="TikTok automator not initialized"
                    )

                # Route to appropriate method
                if action.action_type.name == "LIKE":
                    return self.tiktok_automator.like_video(action.target_identifier)
                elif action.action_type.name == "FOLLOW":
                    return self.tiktok_automator.follow_creator(action.target_identifier)
                elif action.action_type.name == "COMMENT":
                    return self.tiktok_automator.comment_on_video(
                        action.target_identifier,
                        action.metadata.get("comment_text", "")
                    )
                elif action.action_type.name == "SAVE":
                    return self.tiktok_automator.save_video(action.target_identifier)
                elif action.action_type.name == "SHARE":
                    return self.tiktok_automator.share_video(
                        action.target_identifier,
                        action.metadata.get("method", "dm")
                    )
                else:
                    return EngagementResult(
                        action=action,
                        success=False,
                        message=f"Unsupported TikTok action: {action.action_type}"
                    )
            else:
                return EngagementResult(
                    action=action,
                    success=False,
                    message=f"Unsupported platform: {action.platform}"
                )

        except Exception as e:
            return EngagementResult(
                action=action,
                success=False,
                message=f"Action execution failed: {e}"
            )

    def execute_batch(self, batch: EngagementBatch) -> List[EngagementResult]:
        """Execute a batch of engagement actions."""
        results = []

        # Randomize order if configured
        actions = batch.actions.copy()
        if batch.settings.get("randomize_order", True):
            random.shuffle(actions)

        print(f"Starting engagement batch with {len(actions)} actions for {batch.platform.value}")

        for i, action in enumerate(actions, 1):
            print(f"\nProcessing action {i}/{len(actions)}: {action.action_type.value} on {action.target_identifier}")

            try:
                result = self._execute_single_action(action)

                # Update counters and log
                self._update_counters(action.platform, result.success)
                self._log_activity(action, result)

                # Handle retry logic if failed
                if not result.success and batch.settings.get("max_retries", 0) > 0:
                    for retry in range(batch.settings["max_retries"]):
                        print(f"Retry {retry + 1}/{batch.settings['max_retries']} for failed action")
                        result = self._execute_single_action(action)
                        if result.success:
                            self._update_counters(action.platform, True)
                            self._log_activity(action, result)
                            break

                results.append(result)

                # Stop on failure if configured
                if not result.success and batch.settings.get("stop_on_failure", False):
                    print(f"Stopping batch due to failure: {result.message}")
                    break

            except Exception as e:
                error_result = EngagementResult(
                    action=action,
                    success=False,
                    message=f"Batch execution error: {e}"
                )
                results.append(error_result)
                if batch.settings.get("stop_on_failure", False):
                    break

        print(f"\nBatch completed: {sum(1 for r in results if r.success)}/{len(results)} successful")
        return results

    def create_instagram_batch(self, actions: List[EngagementAction], settings: Dict = None) -> EngagementBatch:
        """Create an Instagram engagement batch."""
        return EngagementBatch(
            actions=actions,
            platform=EngagementPlatform.INSTAGRAM,
            settings=settings
        )

    def create_tiktok_batch(self, actions: List[EngagementAction], settings: Dict = None) -> EngagementBatch:
        """Create a TikTok engagement batch."""
        return EngagementBatch(
            actions=actions,
            platform=EngagementPlatform.TIKTOK,
            settings=settings
        )

    def get_engagement_stats(self) -> Dict:
        """Get current engagement statistics."""
        return {
            "action_counts": self.action_counts,
            "last_action_times": self.last_action_times,
            "rate_limits": self.rate_limits
        }

    def get_detailed_stats(self) -> Dict:
        """Get detailed engagement statistics and health metrics."""
        current_date = datetime.now().date()
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        
        stats = {
            "session_info": {
                "start_time": self.session_start_time.isoformat(),
                "duration_minutes": session_duration / 60,
                "safety_enabled": self.safety_enabled
            },
            "platform_stats": {}
        }
        
        for platform in [EngagementPlatform.INSTAGRAM, EngagementPlatform.TIKTOK]:
            current_date_reset = current_date > self.last_daily_reset[platform]
            if current_date_reset:
                self.daily_action_counts[platform] = 0
                self.last_daily_reset[platform] = current_date
                
            limits = self.rate_limits.get(platform, {})
            
            platform_stats = {
                "hourly_actions": self.action_counts[platform],
                "daily_actions": self.daily_action_counts[platform],
                "sequential_actions": self.sequential_action_counts[platform],
                "error_count": self.error_counts[platform],
                "last_action": datetime.fromtimestamp(self.last_action_times[platform]).isoformat() 
                    if self.last_action_times[platform] > 0 else None,
                "limits": {
                    "max_hourly": limits.get('max_actions_per_hour', 100),
                    "max_daily": limits.get('max_daily_actions', 500),
                    "max_sequential": limits.get('max_sequential_actions', 10),
                    "min_delay": limits.get('min_delay', 30),
                    "max_delay": limits.get('max_delay', 60)
                },
                "utilization": {
                    "hourly_percent": (self.action_counts[platform] / limits.get('max_actions_per_hour', 100)) * 100,
                    "daily_percent": (self.daily_action_counts[platform] / limits.get('max_daily_actions', 500)) * 100,
                    "sequential_percent": (self.sequential_action_counts[platform] / limits.get('max_sequential_actions', 10)) * 100
                }
            }
            stats["platform_stats"][platform.value] = platform_stats

        return stats

    def reset_counters(self):
        """Reset engagement counters."""
        self.action_counts = {
            EngagementPlatform.INSTAGRAM: 0,
            EngagementPlatform.TIKTOK: 0
        }
        self.last_action_times = {
            EngagementPlatform.INSTAGRAM: 0,
            EngagementPlatform.TIKTOK: 0
        }

    def enable_safety_mode(self, enabled: bool = True):
        """Enable or disable safety mode."""
        self.safety_enabled = enabled
        status = "enabled" if enabled else "disabled"
        logger.info(f"Safety mode {status}")
        print(f"[yellow]Safety mode {status}[/yellow]")

    def get_recent_activity(self, limit: int = 50) -> List[Dict]:
        """Get recent activity log."""
        return self.activity_log[-limit:] if self.activity_log else []

    def export_activity_log(self, filepath: str):
        """Export activity log to JSON file."""
        import json
        try:
            with open(filepath, 'w') as f:
                json.dump(self.activity_log, f, indent=2)
            print(f"[green]Activity log exported to {filepath}[/green]")
        except Exception as e:
            print(f"[red]Failed to export activity log: {e}[/red]")

    def health_check(self) -> Dict:
        """Perform a comprehensive health check."""
        health = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "warnings": [],
            "critical_issues": [],
            "recommendations": []
        }

        for platform in [EngagementPlatform.INSTAGRAM, EngagementPlatform.TIKTOK]:
            limits = self.rate_limits.get(platform, {})
            error_rate = self.error_counts[platform] / max(1, self.daily_action_counts[platform] + self.error_counts[platform])
            
            # Check error rate
            if error_rate > 0.1:  # More than 10% error rate
                health["warnings"].append(f"High error rate on {platform.value}: {error_rate:.1%}")
                health["overall_status"] = "warning"
            
            # Check daily utilization
            daily_percent = (self.daily_action_counts[platform] / limits.get('max_daily_actions', 500)) * 100
            if daily_percent > 90:
                health["warnings"].append(f"High daily utilization on {platform.value}: {daily_percent:.1f}%")
                health["overall_status"] = "warning"
            
            # Check for potential issues
            if self.error_counts[platform] > 10:
                health["critical_issues"].append(f"High error count on {platform.value}: {self.error_counts[platform]}")
                health["overall_status"] = "critical"

        # Generate recommendations
        if health["overall_status"] == "healthy":
            health["recommendations"].append("System operating normally")
        else:
            health["recommendations"].extend([
                "Consider reducing action frequency",
                "Enable safety mode if not already enabled",
                "Review recent activity logs for patterns"
            ])

        return health