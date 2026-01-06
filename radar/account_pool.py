"""
Account pool management system for multi-account social media automation.

Manages collections of accounts with prioritization, health monitoring,
and intelligent rotation strategies.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
import sqlite3
import json
import random
import threading
from radar.session_persistence import SessionPersistence


class AccountStatus(Enum):
    """Account status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    QUARANTINED = "quarantined"
    BANNED = "banned"
    SUSPENDED = "suspended"


class AccountPriority(Enum):
    """Account priority levels."""
    PRIMARY = "primary"      # Main accounts for high-value operations
    SECONDARY = "secondary"  # Backup accounts
    TERTIARY = "tertiary"    # Low-priority accounts for testing
    TEST = "test"           # Test accounts only


@dataclass
class Account:
    """Social media account representation."""
    id: str
    platform: str  # 'tiktok', 'instagram', etc.
    username: str
    priority: AccountPriority = AccountPriority.SECONDARY
    status: AccountStatus = AccountStatus.ACTIVE
    risk_score: float = 0.0  # 0.0 (safe) to 1.0 (high risk)
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Usage statistics
    total_sessions: int = 0
    successful_sessions: int = 0
    failed_sessions: int = 0
    total_engagements: int = 0
    successful_engagements: int = 0
    failed_engagements: int = 0

    # Rate limiting
    daily_limit: int = 100  # Max engagements per day
    hourly_limit: int = 20   # Max engagements per hour
    todays_usage: int = 0
    last_hour_usage: int = 0
    last_reset_date: Optional[datetime] = None
    last_reset_hour: Optional[datetime] = None

    # Metadata
    tags: Set[str] = field(default_factory=set)
    notes: str = ""
    custom_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "platform": self.platform,
            "username": self.username,
            "priority": self.priority.value,
            "status": self.status.value,
            "risk_score": self.risk_score,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "total_sessions": self.total_sessions,
            "successful_sessions": self.successful_sessions,
            "failed_sessions": self.failed_sessions,
            "total_engagements": self.total_engagements,
            "successful_engagements": self.successful_engagements,
            "failed_engagements": self.failed_engagements,
            "daily_limit": self.daily_limit,
            "hourly_limit": self.hourly_limit,
            "todays_usage": self.todays_usage,
            "last_hour_usage": self.last_hour_usage,
            "last_reset_date": self.last_reset_date.isoformat() if self.last_reset_date else None,
            "last_reset_hour": self.last_reset_hour.isoformat() if self.last_reset_hour else None,
            "tags": list(self.tags),
            "notes": self.notes,
            "custom_data": self.custom_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Account":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            platform=data["platform"],
            username=data["username"],
            priority=AccountPriority(data["priority"]),
            status=AccountStatus(data["status"]),
            risk_score=data.get("risk_score", 0.0),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            total_sessions=data.get("total_sessions", 0),
            successful_sessions=data.get("successful_sessions", 0),
            failed_sessions=data.get("failed_sessions", 0),
            total_engagements=data.get("total_engagements", 0),
            successful_engagements=data.get("successful_engagements", 0),
            failed_engagements=data.get("failed_engagements", 0),
            daily_limit=data.get("daily_limit", 100),
            hourly_limit=data.get("hourly_limit", 20),
            todays_usage=data.get("todays_usage", 0),
            last_hour_usage=data.get("last_hour_usage", 0),
            last_reset_date=datetime.fromisoformat(data["last_reset_date"]) if data.get("last_reset_date") else None,
            last_reset_hour=datetime.fromisoformat(data["last_reset_hour"]) if data.get("last_reset_hour") else None,
            tags=set(data.get("tags", [])),
            notes=data.get("notes", ""),
            custom_data=data.get("custom_data", {})
        )

    def update_usage_limits(self):
        """Update daily and hourly usage limits based on current time."""
        now = datetime.now()
        today = now.date()

        # Reset daily usage if it's a new day
        if self.last_reset_date and self.last_reset_date.date() < today:
            self.todays_usage = 0
            self.last_reset_date = now
        elif not self.last_reset_date:
            # First time initialization - set reset date but keep current usage
            self.last_reset_date = now

        # Reset hourly usage if it's a new hour
        if self.last_reset_hour and self.last_reset_hour.hour != now.hour:
            self.last_hour_usage = 0
            self.last_reset_hour = now
        elif not self.last_reset_hour:
            # First time initialization - set reset hour but keep current usage
            self.last_reset_hour = now

    def can_perform_engagement(self) -> bool:
        """Check if account can perform an engagement based on limits."""
        self.update_usage_limits()
        return (self.todays_usage < self.daily_limit and
                self.last_hour_usage < self.hourly_limit and
                self.status == AccountStatus.ACTIVE)

    def record_engagement(self, success: bool = True):
        """Record an engagement attempt."""
        self.update_usage_limits()

        self.total_engagements += 1
        if success:
            self.successful_engagements += 1
            self.todays_usage += 1
            self.last_hour_usage += 1
        else:
            self.failed_engagements += 1

        self.last_used = datetime.now()
        self.updated_at = datetime.now()

    def calculate_success_rate(self) -> float:
        """Calculate engagement success rate."""
        total = self.total_engagements
        return self.successful_engagements / total if total > 0 else 1.0

    def calculate_session_success_rate(self) -> float:
        """Calculate session success rate."""
        total = self.total_sessions
        return self.successful_sessions / total if total > 0 else 1.0

    def update_risk_score(self):
        """Update risk score based on account performance."""
        # Base risk factors
        failure_rate = 1.0 - self.calculate_success_rate()
        session_failure_rate = 1.0 - self.calculate_session_success_rate()

        # Recent activity factor (higher risk if recently active)
        recency_factor = 0.0
        if self.last_used:
            days_since_use = (datetime.now() - self.last_used).days
            recency_factor = max(0, 1.0 - (days_since_use / 30.0))  # Decrease over 30 days

        # Status-based risk
        status_risk = {
            AccountStatus.ACTIVE: 0.0,
            AccountStatus.INACTIVE: 0.2,
            AccountStatus.QUARANTINED: 0.5,
            AccountStatus.SUSPENDED: 0.8,
            AccountStatus.BANNED: 1.0
        }.get(self.status, 0.0)

        # Calculate weighted risk score
        self.risk_score = min(1.0, (
            failure_rate * 0.4 +
            session_failure_rate * 0.3 +
            recency_factor * 0.2 +
            status_risk * 0.1
        ))


class AccountPool:
    """
    Manages a pool of social media accounts with intelligent selection and rotation.

    Features:
    - Account prioritization and health monitoring
    - Intelligent selection algorithms
    - Automatic quarantine and recovery
    - Usage tracking and rate limiting
    """

    def __init__(self, db_path: str = "data/radar.sqlite"):
        """
        Initialize account pool.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._accounts: Dict[str, Account] = {}  # account_id -> Account
        self._platform_accounts: Dict[str, List[str]] = {}  # platform -> [account_ids]
        self._lock = threading.Lock()
        self._init_database()

    def _init_database(self):
        """Initialize account tables."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Accounts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    username TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    risk_score REAL DEFAULT 0.0,
                    last_used TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    total_sessions INTEGER DEFAULT 0,
                    successful_sessions INTEGER DEFAULT 0,
                    failed_sessions INTEGER DEFAULT 0,
                    total_engagements INTEGER DEFAULT 0,
                    successful_engagements INTEGER DEFAULT 0,
                    failed_engagements INTEGER DEFAULT 0,
                    daily_limit INTEGER DEFAULT 100,
                    hourly_limit INTEGER DEFAULT 20,
                    todays_usage INTEGER DEFAULT 0,
                    last_hour_usage INTEGER DEFAULT 0,
                    last_reset_date TEXT,
                    last_reset_hour TEXT,
                    tags TEXT NOT NULL,  -- JSON array
                    notes TEXT,
                    custom_data TEXT NOT NULL  -- JSON
                )
            """)

            conn.commit()

    def add_account(self, account: Account) -> None:
        """
        Add an account to the pool.

        Args:
            account: Account to add
        """
        with self._lock:
            account.updated_at = datetime.now()

            self._accounts[account.id] = account

            # Update platform index
            if account.platform not in self._platform_accounts:
                self._platform_accounts[account.platform] = []
            if account.id not in self._platform_accounts[account.platform]:
                self._platform_accounts[account.platform].append(account.id)

            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO accounts
                    (id, platform, username, priority, status, risk_score, last_used,
                     created_at, updated_at, total_sessions, successful_sessions, failed_sessions,
                     total_engagements, successful_engagements, failed_engagements,
                     daily_limit, hourly_limit, todays_usage, last_hour_usage,
                     last_reset_date, last_reset_hour, tags, notes, custom_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    account.id,
                    account.platform,
                    account.username,
                    account.priority.value,
                    account.status.value,
                    account.risk_score,
                    account.last_used.isoformat() if account.last_used else None,
                    account.created_at.isoformat(),
                    account.updated_at.isoformat(),
                    account.total_sessions,
                    account.successful_sessions,
                    account.failed_sessions,
                    account.total_engagements,
                    account.successful_engagements,
                    account.failed_engagements,
                    account.daily_limit,
                    account.hourly_limit,
                    account.todays_usage,
                    account.last_hour_usage,
                    account.last_reset_date.isoformat() if account.last_reset_date else None,
                    account.last_reset_hour.isoformat() if account.last_reset_hour else None,
                    json.dumps(list(account.tags)),
                    account.notes,
                    json.dumps(account.custom_data)
                ))
                conn.commit()

    def remove_account(self, account_id: str) -> bool:
        """
        Remove an account from the pool.

        Args:
            account_id: Account ID to remove

        Returns:
            True if account was removed
        """
        with self._lock:
            if account_id not in self._accounts:
                return False

            account = self._accounts[account_id]
            platform = account.platform

            # Remove from memory
            del self._accounts[account_id]

            # Remove from platform index
            if platform in self._platform_accounts and account_id in self._platform_accounts[platform]:
                self._platform_accounts[platform].remove(account_id)

            # Remove from database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
                conn.commit()

            return True

    def get_account(self, account_id: str) -> Optional[Account]:
        """
        Get an account by ID.

        Args:
            account_id: Account ID

        Returns:
            Account or None if not found
        """
        with self._lock:
            return self._accounts.get(account_id)

    def load_all(self) -> List[Account]:
        """
        Load all accounts from database into memory.

        Returns:
            List of all accounts
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT * FROM accounts").fetchall()

                for row in rows:
                    account = self._row_to_account(row)
                    self._accounts[account.id] = account

                    # Update platform index
                    if account.platform not in self._platform_accounts:
                        self._platform_accounts[account.platform] = []
                    if account.id not in self._platform_accounts[account.platform]:
                        self._platform_accounts[account.platform].append(account.id)

            return list(self._accounts.values())

    def _row_to_account(self, row: sqlite3.Row) -> Account:
        """Convert database row to Account object."""
        return Account(
            id=row["id"],
            platform=row["platform"],
            username=row["username"],
            priority=AccountPriority(row["priority"]),
            status=AccountStatus(row["status"]),
            risk_score=row["risk_score"] or 0.0,
            last_used=datetime.fromisoformat(row["last_used"]) if row["last_used"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.fromisoformat(row["created_at"]),
            total_sessions=row["total_sessions"] or 0,
            successful_sessions=row["successful_sessions"] or 0,
            failed_sessions=row["failed_sessions"] or 0,
            total_engagements=row["total_engagements"] or 0,
            successful_engagements=row["successful_engagements"] or 0,
            failed_engagements=row["failed_engagements"] or 0,
            daily_limit=row["daily_limit"] or 100,
            hourly_limit=row["hourly_limit"] or 20,
            todays_usage=row["todays_usage"] or 0,
            last_hour_usage=row["last_hour_usage"] or 0,
            last_reset_date=datetime.fromisoformat(row["last_reset_date"]) if row["last_reset_date"] else None,
            last_reset_hour=datetime.fromisoformat(row["last_reset_hour"]) if row["last_reset_hour"] else None,
            tags=set(json.loads(row["tags"]) if row["tags"] else []),
            notes=row["notes"] or "",
            custom_data=json.loads(row["custom_data"]) if row["custom_data"] else {}
        )

    def list_accounts(self, platform: Optional[str] = None,
                     status: Optional[AccountStatus] = None,
                     priority: Optional[AccountPriority] = None) -> List[Account]:
        """
        List accounts with optional filtering.

        Args:
            platform: Filter by platform
            status: Filter by status
            priority: Filter by priority

        Returns:
            List of matching accounts
        """
        with self._lock:
            # Load from database if not in memory
            if not self._accounts:
                self.load_all()

            accounts = list(self._accounts.values())

            if platform:
                accounts = [a for a in accounts if a.platform == platform]
            if status:
                accounts = [a for a in accounts if a.status == status]
            if priority:
                accounts = [a for a in accounts if a.priority == priority]

            return accounts

    def select_account(self, platform: str,
                      priority_preference: Optional[AccountPriority] = None,
                      exclude_recent: bool = True,
                      max_risk_score: float = 0.7) -> Optional[Account]:
        """
        Select the best available account for a platform.

        Selection criteria (in order):
        1. Status = ACTIVE
        2. Risk score <= max_risk_score
        3. Within usage limits
        4. Priority preference (if specified)
        5. Lowest risk score
        6. Least recently used (if exclude_recent=True)

        Args:
            platform: Target platform
            priority_preference: Preferred priority level
            exclude_recent: Avoid recently used accounts
            max_risk_score: Maximum acceptable risk score

        Returns:
            Selected Account or None if no suitable account found
        """
        with self._lock:
            candidates = []

            for account_id in self._platform_accounts.get(platform, []):
                account = self._accounts[account_id]

                # Basic filters
                if account.status != AccountStatus.ACTIVE:
                    continue
                if account.risk_score > max_risk_score:
                    continue
                if not account.can_perform_engagement():
                    continue

                candidates.append(account)

            if not candidates:
                return None

            # Sort by priority preference first, then risk score and usage
            if priority_preference:
                candidates.sort(key=lambda a: (
                    0 if a.priority == priority_preference else 1,  # Prefer priority_preference
                    a.risk_score,                                    # Then lowest risk
                    a.todays_usage,                                  # Then least used today
                    a.last_hour_usage                                # Then least used this hour
                ))
            else:
                # Without priority preference, sort by risk score and usage
                candidates.sort(key=lambda a: (a.risk_score, a.todays_usage, a.last_hour_usage))

            # Exclude recently used if requested
            if exclude_recent and len(candidates) > 1:
                now = datetime.now()
                recent_threshold = now - timedelta(minutes=30)  # 30 minute cooldown

                non_recent = [a for a in candidates if not a.last_used or a.last_used < recent_threshold]
                if non_recent:
                    candidates = non_recent

            return candidates[0] if candidates else None

    def get_random_account(self, platform: str,
                          priority: Optional[AccountPriority] = None,
                          max_risk_score: float = 0.7) -> Optional[Account]:
        """
        Select a random account from available candidates.

        Args:
            platform: Target platform
            priority: Optional priority filter
            max_risk_score: Maximum acceptable risk score

        Returns:
            Randomly selected Account or None
        """
        candidates = self.list_accounts(
            platform=platform,
            status=AccountStatus.ACTIVE,
            priority=priority
        )

        # Filter by risk score and usage limits
        candidates = [a for a in candidates
                     if a.risk_score <= max_risk_score and a.can_perform_engagement()]

        return random.choice(candidates) if candidates else None

    def quarantine_account(self, account_id: str, reason: str = "") -> bool:
        """
        Quarantine an account due to issues.

        Args:
            account_id: Account to quarantine
            reason: Reason for quarantine

        Returns:
            True if account was quarantined
        """
        with self._lock:
            account = self._accounts.get(account_id)
            if not account:
                return False

            account.status = AccountStatus.QUARANTINED
            account.notes = f"Quarantined: {reason}"
            account.updated_at = datetime.now()

            self.add_account(account)  # Save changes
            return True

    def reactivate_account(self, account_id: str) -> bool:
        """
        Reactivate a quarantined account.

        Args:
            account_id: Account to reactivate

        Returns:
            True if account was reactivated
        """
        with self._lock:
            account = self._accounts.get(account_id)
            if not account or account.status != AccountStatus.QUARANTINED:
                return False

            account.status = AccountStatus.ACTIVE
            account.notes = ""
            account.updated_at = datetime.now()

            self.add_account(account)  # Save changes
            return True

    def update_account_stats(self, account_id: str, session_success: bool = True,
                           engagement_success: Optional[bool] = None) -> None:
        """
        Update account statistics after a session/engagement.

        Args:
            account_id: Account ID
            session_success: Whether session was successful
            engagement_success: Whether engagement was successful (if applicable)
        """
        with self._lock:
            account = self._accounts.get(account_id)
            if not account:
                return

            # Update session stats
            account.total_sessions += 1
            if session_success:
                account.successful_sessions += 1
            else:
                account.failed_sessions += 1

            # Update engagement stats if provided
            if engagement_success is not None:
                account.record_engagement(engagement_success)

            # Recalculate risk score
            account.update_risk_score()

            self.add_account(account)  # Save changes

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get overall pool statistics."""
        with self._lock:
            accounts = list(self._accounts.values())

            if not accounts:
                return {"total_accounts": 0}

            total_accounts = len(accounts)
            active_accounts = sum(1 for a in accounts if a.status == AccountStatus.ACTIVE)
            quarantined_accounts = sum(1 for a in accounts if a.status == AccountStatus.QUARANTINED)

            platform_stats = {}
            for account in accounts:
                platform = account.platform
                if platform not in platform_stats:
                    platform_stats[platform] = {
                        "total": 0,
                        "active": 0,
                        "quarantined": 0,
                        "avg_risk_score": 0.0,
                        "total_engagements": 0
                    }

                platform_stats[platform]["total"] += 1
                if account.status == AccountStatus.ACTIVE:
                    platform_stats[platform]["active"] += 1
                elif account.status == AccountStatus.QUARANTINED:
                    platform_stats[platform]["quarantined"] += 1

                platform_stats[platform]["avg_risk_score"] += account.risk_score
                platform_stats[platform]["total_engagements"] += account.total_engagements

            # Calculate averages
            for stats in platform_stats.values():
                if stats["total"] > 0:
                    stats["avg_risk_score"] /= stats["total"]

            return {
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "quarantined_accounts": quarantined_accounts,
                "platform_stats": platform_stats
            }

    def cleanup_inactive_accounts(self, days_inactive: int = 90) -> int:
        """
        Remove accounts that haven't been used for specified days.

        Args:
            days_inactive: Days of inactivity threshold

        Returns:
            Number of accounts removed
        """
        with self._lock:
            cutoff_date = datetime.now() - timedelta(days=days_inactive)
            to_remove = []

            for account_id, account in self._accounts.items():
                if (account.last_used and account.last_used < cutoff_date and
                    account.status != AccountStatus.ACTIVE):
                    to_remove.append(account_id)

            for account_id in to_remove:
                self.remove_account(account_id)

            return len(to_remove)

    def export_accounts(self, file_path: str, platform: Optional[str] = None) -> None:
        """
        Export accounts to JSON file.

        Args:
            file_path: Path to export file
            platform: Optional platform filter
        """
        accounts = self.list_accounts(platform=platform)

        data = {
            "accounts": [a.to_dict() for a in accounts],
            "exported_at": datetime.now().isoformat(),
            "platform_filter": platform
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def import_accounts(self, file_path: str) -> int:
        """
        Import accounts from JSON file.

        Args:
            file_path: Path to import file

        Returns:
            Number of accounts imported
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        count = 0
        for account_data in data.get("accounts", []):
            account = Account.from_dict(account_data)
            self.add_account(account)
            count += 1

        return count