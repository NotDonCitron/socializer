"""
Session orchestrator for managing multi-account browser sessions.

Coordinates browser sessions across multiple accounts with proxy rotation,
fingerprint management, and session persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import time
import threading
import os

from radar.browser import BrowserManager
from radar.proxy_manager import ProxyManager, ProxyConfig
from radar.fingerprint_generator import FingerprintGenerator, BrowserFingerprint
from radar.session_persistence import SessionPersistence, SessionData
from radar.account_pool import AccountPool, Account, AccountPriority, AccountStatus


class EngagementPlatform(Enum):
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"


@dataclass
class SessionContext:
    """Active browser session context."""
    account_id: str
    platform: EngagementPlatform
    browser_context: Any  # Playwright BrowserContext
    proxy_config: Optional[ProxyConfig] = None
    fingerprint: Optional[BrowserFingerprint] = None
    session_data: Optional[SessionData] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    is_healthy: bool = True
    consecutive_errors: int = 0

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def mark_error(self):
        """Mark an error occurred."""
        self.consecutive_errors += 1
        self.is_healthy = self.consecutive_errors < 3

    def reset_errors(self):
        """Reset error counter after successful operation."""
        self.consecutive_errors = 0
        self.is_healthy = True


class SessionOrchestrator:
    """
    Orchestrates browser sessions for multi-account social media automation.

    Features:
    - Session lifecycle management
    - Proxy rotation and binding
    - Fingerprint application
    - Health monitoring and recovery
    - Account pool integration
    - Resource cleanup
    """

    def __init__(
        self,
        browser_manager: Optional[BrowserManager] = None,
        proxy_manager: Optional[ProxyManager] = None,
        fingerprint_generator: Optional[FingerprintGenerator] = None,
        session_persistence: Optional[SessionPersistence] = None,
        account_pool: Optional[AccountPool] = None,
        db_path: str = "data/radar.sqlite",
        max_sessions_per_platform: int = 5,
        session_timeout_minutes: int = 30,
        health_check_interval: int = 60
    ):
        """
        Initialize session orchestrator.

        Args:
            browser_manager: Browser manager instance
            proxy_manager: Proxy manager instance
            fingerprint_generator: Fingerprint generator instance
            session_persistence: Session persistence instance
            account_pool: Account pool instance
            db_path: Database path
            max_sessions_per_platform: Maximum concurrent sessions per platform
            session_timeout_minutes: Session timeout in minutes
            health_check_interval: Health check interval in seconds
        """
        self.browser_manager = browser_manager or BrowserManager()
        self.proxy_manager = proxy_manager or ProxyManager(db_path)
        self.fingerprint_generator = fingerprint_generator or FingerprintGenerator(db_path)
        self.session_persistence = session_persistence or SessionPersistence(db_path)
        self.account_pool = account_pool or AccountPool(db_path)

        self.db_path = db_path
        self.max_sessions_per_platform = max_sessions_per_platform
        self.session_timeout_minutes = session_timeout_minutes
        self.health_check_interval = health_check_interval

        # Active sessions: platform -> account_id -> SessionContext
        self._active_sessions: Dict[str, Dict[str, SessionContext]] = {}
        self._session_lock = threading.Lock()

        # Background health monitoring
        self._health_monitor_thread: Optional[threading.Thread] = None
        self._health_monitor_running = False

        # Initialize platform-specific session tracking
        for platform in EngagementPlatform:
            self._active_sessions[platform.value] = {}

    def start_health_monitoring(self):
        """Start background health monitoring thread."""
        if self._health_monitor_thread and self._health_monitor_thread.is_alive():
            return

        self._health_monitor_running = True
        self._health_monitor_thread = threading.Thread(
            target=self._health_monitor_loop,
            daemon=True
        )
        self._health_monitor_thread.start()

    def stop_health_monitoring(self):
        """Stop background health monitoring."""
        self._health_monitor_running = False
        if self._health_monitor_thread:
            self._health_monitor_thread.join(timeout=5)

    def _health_monitor_loop(self):
        """Background health monitoring loop."""
        while self._health_monitor_running:
            try:
                self._perform_health_checks()
                self._cleanup_expired_sessions()
            except Exception as e:
                print(f"Health monitor error: {e}")

            time.sleep(self.health_check_interval)

    def _perform_health_checks(self):
        """Perform health checks on active sessions."""
        with self._session_lock:
            for platform, sessions in self._active_sessions.items():
                for account_id, context in list(sessions.items()):
                    # Check if session has been idle too long
                    idle_time = datetime.now() - context.last_activity
                    if idle_time > timedelta(minutes=self.session_timeout_minutes):
                        print(f"Session {account_id} idle for {idle_time}, closing")
                        self._close_session(context)
                        continue

                    # Check session health
                    if not context.is_healthy:
                        print(f"Session {account_id} marked unhealthy, attempting recovery")
                        self._recover_session(context)

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions from persistence layer."""
        try:
            cleaned = self.session_persistence.cleanup_expired_sessions()
            if cleaned > 0:
                print(f"Cleaned up {cleaned} expired sessions")
        except Exception as e:
            print(f"Error cleaning expired sessions: {e}")

    def create_session(
        self,
        account_id: str,
        platform: EngagementPlatform,
        user_data_dir: Optional[str] = None,
        proxy_id: Optional[str] = None,
        fingerprint_id: Optional[str] = None,
        headless: bool = True
    ) -> SessionContext:
        """
        Create a new browser session for an account.

        Args:
            account_id: Account identifier
            platform: Social media platform
            user_data_dir: Browser data directory (auto-generated if None)
            proxy_id: Specific proxy to use
            fingerprint_id: Specific fingerprint to use
            headless: Run headless

        Returns:
            SessionContext for the created session
        """
        with self._session_lock:
            platform_key = platform.value

            # Check session limits
            active_count = len(self._active_sessions[platform_key])
            if active_count >= self.max_sessions_per_platform:
                raise RuntimeError(f"Maximum sessions ({self.max_sessions_per_platform}) reached for {platform.value}")

            # Check if session already exists
            if account_id in self._active_sessions[platform_key]:
                return self._active_sessions[platform_key][account_id]

            # Generate user data directory if not provided
            if not user_data_dir:
                user_data_dir = f"data/sessions/{platform.value}/{account_id}"
                os.makedirs(user_data_dir, exist_ok=True)

            # Get or create session data
            session_data = self.session_persistence.load_session(account_id)
            if not session_data:
                session_data = SessionData(
                    account_id=account_id,
                    platform=platform.value
                )

            # Get proxy configuration
            proxy_config = None
            if proxy_id:
                proxy_config = self.proxy_manager.get_proxy(proxy_id)
            elif session_data.proxy_id:
                proxy_config = self.proxy_manager.get_proxy(session_data.proxy_id)
            else:
                # Get available proxy and bind it
                proxy_config = self.proxy_manager.get_available_proxy()
                if proxy_config:
                    self.proxy_manager.bind_to_account(account_id, proxy_config.id)
                    session_data.proxy_id = proxy_config.id

            # Get fingerprint
            fingerprint = None
            if fingerprint_id:
                fingerprint = self.fingerprint_generator.load_fingerprint(fingerprint_id)
            elif session_data.fingerprint_id:
                fingerprint = self.fingerprint_generator.load_fingerprint(session_data.fingerprint_id)
            else:
                # Generate new fingerprint
                fingerprint = self.fingerprint_generator.generate_fingerprint()
                fingerprint_id = self.fingerprint_generator.save_fingerprint(fingerprint)
                session_data.fingerprint_id = fingerprint_id

            # Update session data with current config
            if proxy_config:
                session_data.proxy_id = proxy_config.id
            if fingerprint:
                session_data.fingerprint_id = fingerprint.id
                session_data.user_agent = fingerprint.user_agent
                session_data.viewport = fingerprint.viewport
                session_data.timezone = fingerprint.timezone
                session_data.language = fingerprint.language

            # Launch browser context
            proxy_dict = proxy_config.to_playwright_format() if proxy_config else None

            context = self.browser_manager.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=headless,
                proxy=proxy_dict,
                fingerprint=fingerprint
            )

            # Restore session data if available
            if session_data.cookies:
                context.add_cookies(session_data.cookies)

            # Create session context
            session_context = SessionContext(
                account_id=account_id,
                platform=platform,
                browser_context=context,
                proxy_config=proxy_config,
                fingerprint=fingerprint,
                session_data=session_data
            )

            # Store in active sessions
            self._active_sessions[platform_key][account_id] = session_context

            # Update usage statistics
            if fingerprint:
                self.fingerprint_generator.update_usage(fingerprint.id)

            return session_context

    def get_session(self, account_id: str, platform: EngagementPlatform) -> Optional[SessionContext]:
        """
        Get an existing session for an account.

        Args:
            account_id: Account identifier
            platform: Social media platform

        Returns:
            SessionContext or None if not found
        """
        with self._session_lock:
            platform_key = platform.value
            return self._active_sessions.get(platform_key, {}).get(account_id)

    def close_session(self, account_id: str, platform: EngagementPlatform, save_session: bool = True):
        """
        Close a session and optionally save its state.

        Args:
            account_id: Account identifier
            platform: Social media platform
            save_session: Whether to save session data
        """
        with self._session_lock:
            platform_key = platform.value
            context = self._active_sessions.get(platform_key, {}).get(account_id)

            if context:
                self._close_session(context, save_session)

    def _close_session(self, context: SessionContext, save_session: bool = True):
        """Internal method to close a session."""
        try:
            # Save session data before closing
            if save_session and context.session_data:
                # Update cookies and storage
                try:
                    cookies = context.browser_context.cookies()
                    context.session_data.cookies = cookies
                except Exception:
                    pass  # Cookies might not be accessible

                self.session_persistence.save_session(context.session_data)

            # Close browser context
            context.browser_context.close()

        except Exception as e:
            print(f"Error closing session {context.account_id}: {e}")
        finally:
            # Remove from active sessions
            platform_key = context.platform.value
            self._active_sessions[platform_key].pop(context.account_id, None)

    def rotate_proxy(self, account_id: str, platform: EngagementPlatform) -> Optional[ProxyConfig]:
        """
        Rotate to a new proxy for an account.

        Args:
            account_id: Account identifier
            platform: Social media platform

        Returns:
            New ProxyConfig or None
        """
        with self._session_lock:
            context = self.get_session(account_id, platform)
            if not context:
                return None

            # Get new proxy
            new_proxy = self.proxy_manager.rotate_proxy(account_id)
            if not new_proxy:
                return None

            # Update session data
            context.proxy_config = new_proxy
            if context.session_data:
                context.session_data.proxy_id = new_proxy.id

            # Note: In a real implementation, you might need to restart the browser
            # context with the new proxy, but that's complex with persistent contexts
            print(f"Rotated proxy for {account_id} to {new_proxy.host}:{new_proxy.port}")

            return new_proxy

    def _recover_session(self, context: SessionContext) -> bool:
        """
        Attempt to recover an unhealthy session.

        Args:
            context: Session context to recover

        Returns:
            True if recovery successful
        """
        try:
            # Try rotating proxy first
            if context.proxy_config:
                new_proxy = self.rotate_proxy(context.account_id, context.platform)
                if new_proxy:
                    context.reset_errors()
                    return True

            # If proxy rotation fails, close and recreate session
            print(f"Recovery failed for {context.account_id}, recreating session")
            self._close_session(context, save_session=True)

            # Recreate session
            new_context = self.create_session(
                context.account_id,
                context.platform,
                fingerprint_id=context.fingerprint.id if context.fingerprint else None
            )

            return new_context.is_healthy

        except Exception as e:
            print(f"Session recovery failed for {context.account_id}: {e}")
            return False

    def get_active_sessions(self, platform: Optional[EngagementPlatform] = None) -> List[SessionContext]:
        """
        Get all active sessions.

        Args:
            platform: Optional platform filter

        Returns:
            List of active SessionContext objects
        """
        with self._session_lock:
            if platform:
                return list(self._active_sessions[platform.value].values())
            else:
                sessions = []
                for platform_sessions in self._active_sessions.values():
                    sessions.extend(platform_sessions.values())
                return sessions

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        with self._session_lock:
            total_sessions = 0
            healthy_sessions = 0
            platform_stats = {}

            for platform, sessions in self._active_sessions.items():
                platform_count = len(sessions)
                platform_healthy = sum(1 for s in sessions.values() if s.is_healthy)

                total_sessions += platform_count
                healthy_sessions += platform_healthy

                platform_stats[platform] = {
                    "total": platform_count,
                    "healthy": platform_healthy,
                    "health_rate": platform_healthy / max(platform_count, 1)
                }

            return {
                "total_active_sessions": total_sessions,
                "healthy_sessions": healthy_sessions,
                "overall_health_rate": healthy_sessions / max(total_sessions, 1),
                "platform_stats": platform_stats,
                "max_sessions_per_platform": self.max_sessions_per_platform
            }

    def cleanup_all_sessions(self, save_sessions: bool = True):
        """
        Clean up all active sessions.

        Args:
            save_sessions: Whether to save session data before closing
        """
        with self._session_lock:
            for platform_sessions in self._active_sessions.values():
                for context in list(platform_sessions.values()):
                    self._close_session(context, save_sessions)

    # Account Pool Integration Methods

    def select_account_for_platform(self, platform: str,
                                   priority_preference: Optional[AccountPriority] = None,
                                   exclude_recent: bool = True,
                                   max_risk_score: float = 0.7) -> Optional[Account]:
        """
        Select the best available account for a platform using account pool.

        Args:
            platform: Target platform
            priority_preference: Preferred priority level
            exclude_recent: Avoid recently used accounts
            max_risk_score: Maximum acceptable risk score

        Returns:
            Selected Account or None if no suitable account found
        """
        platform_enum = EngagementPlatform(platform.upper())
        return self.account_pool.select_account(
            platform=platform,
            priority_preference=priority_preference,
            exclude_recent=exclude_recent,
            max_risk_score=max_risk_score
        )

    def get_random_account_for_platform(self, platform: str,
                                       priority: Optional[AccountPriority] = None,
                                       max_risk_score: float = 0.7) -> Optional[Account]:
        """
        Get a random account for a platform using account pool.

        Args:
            platform: Target platform
            priority: Optional priority filter
            max_risk_score: Maximum acceptable risk score

        Returns:
            Randomly selected Account or None
        """
        return self.account_pool.get_random_account(
            platform=platform,
            priority=priority,
            max_risk_score=max_risk_score
        )

    def add_account_to_pool(self, account: Account) -> None:
        """
        Add an account to the account pool.

        Args:
            account: Account to add
        """
        self.account_pool.add_account(account)

    def get_account_from_pool(self, account_id: str) -> Optional[Account]:
        """
        Get an account from the account pool.

        Args:
            account_id: Account ID

        Returns:
            Account or None if not found
        """
        return self.account_pool.get_account(account_id)

    def quarantine_account(self, account_id: str, reason: str = "") -> bool:
        """
        Quarantine an account in the pool.

        Args:
            account_id: Account to quarantine
            reason: Reason for quarantine

        Returns:
            True if account was quarantined
        """
        return self.account_pool.quarantine_account(account_id, reason)

    def reactivate_account(self, account_id: str) -> bool:
        """
        Reactivate a quarantined account.

        Args:
            account_id: Account to reactivate

        Returns:
            True if account was reactivated
        """
        return self.account_pool.reactivate_account(account_id)

    def update_account_performance(self, account_id: str, session_success: bool = True,
                                 engagement_success: Optional[bool] = None) -> None:
        """
        Update account performance statistics.

        Args:
            account_id: Account ID
            session_success: Whether session was successful
            engagement_success: Whether engagement was successful (if applicable)
        """
        self.account_pool.update_account_stats(account_id, session_success, engagement_success)

    def get_combined_stats(self) -> Dict[str, Any]:
        """
        Get combined statistics for sessions and accounts.

        Returns:
            Dictionary with session and account statistics
        """
        session_stats = self.get_session_stats()
        account_stats = self.account_pool.get_pool_stats()

        # Calculate combined metrics
        total_accounts = account_stats.get("total_accounts", 0)
        active_accounts = account_stats.get("active_accounts", 0)
        active_sessions = session_stats.get("total_active_sessions", 0)

        return {
            "sessions": session_stats,
            "accounts": account_stats,
            "combined": {
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "active_sessions": active_sessions,
                "session_coverage": active_sessions / max(active_accounts, 1),
                "account_utilization": active_sessions / max(total_accounts, 1)
            }
        }

    def create_session_for_selected_account(self, platform: str,
                                          priority_preference: Optional[AccountPriority] = None,
                                          **kwargs) -> Optional[SessionContext]:
        """
        Select an account and create a session for it.

        Args:
            platform: Target platform
            priority_preference: Preferred account priority
            **kwargs: Additional arguments for create_session

        Returns:
            SessionContext or None if no suitable account found
        """
        account = self.select_account_for_platform(
            platform=platform,
            priority_preference=priority_preference
        )

        if not account:
            return None

        platform_enum = EngagementPlatform(platform.upper())
        return self.create_session(account.id, platform_enum, **kwargs)

    def __enter__(self):
        """Context manager entry."""
        self.start_health_monitoring()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_health_monitoring()
        self.cleanup_all_sessions()


# Convenience functions for common operations

def create_session_for_account(
    orchestrator: SessionOrchestrator,
    account_id: str,
    platform: str,
    **kwargs
) -> SessionContext:
    """
    Convenience function to create a session for an account.

    Args:
        orchestrator: SessionOrchestrator instance
        account_id: Account identifier
        platform: Platform name ('tiktok', 'instagram', etc.)
        **kwargs: Additional arguments for create_session

    Returns:
        SessionContext
    """
    platform_enum = EngagementPlatform(platform.upper())
    return orchestrator.create_session(account_id, platform_enum, **kwargs)


def get_session_for_account(
    orchestrator: SessionOrchestrator,
    account_id: str,
    platform: str
) -> Optional[SessionContext]:
    """
    Convenience function to get a session for an account.

    Args:
        orchestrator: SessionOrchestrator instance
        account_id: Account identifier
        platform: Platform name

    Returns:
        SessionContext or None
    """
    platform_enum = EngagementPlatform(platform.upper())
    return orchestrator.get_session(account_id, platform_enum)


def close_session_for_account(
    orchestrator: SessionOrchestrator,
    account_id: str,
    platform: str,
    save_session: bool = True
):
    """
    Convenience function to close a session for an account.

    Args:
        orchestrator: SessionOrchestrator instance
        account_id: Account identifier
        platform: Platform name
        save_session: Whether to save session data
    """
    platform_enum = EngagementPlatform(platform.upper())
    orchestrator.close_session(account_id, platform_enum, save_session)