"""
Session persistence module for storing and recovering browser sessions.

Handles cookies, localStorage, sessionStorage, and other browser state
that needs to persist across automation runs.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import sqlite3
import os
from pathlib import Path
from radar.proxy_manager import ProxyConfig
from radar.fingerprint_generator import BrowserFingerprint


@dataclass
class SessionData:
    """Complete browser session data."""
    account_id: str
    platform: str  # 'tiktok', 'instagram', etc.
    cookies: List[Dict[str, Any]] = field(default_factory=list)
    local_storage: Dict[str, str] = field(default_factory=dict)
    session_storage: Dict[str, str] = field(default_factory=dict)
    indexed_db: Dict[str, Any] = field(default_factory=dict)
    proxy_id: Optional[str] = None
    fingerprint_id: Optional[str] = None
    user_agent: Optional[str] = None
    viewport: Optional[Dict[str, int]] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    is_logged_in: bool = False
    last_login_attempt: Optional[datetime] = None
    login_success_count: int = 0
    login_failure_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "account_id": self.account_id,
            "platform": self.platform,
            "cookies": self.cookies,
            "local_storage": self.local_storage,
            "session_storage": self.session_storage,
            "indexed_db": self.indexed_db,
            "proxy_id": self.proxy_id,
            "fingerprint_id": self.fingerprint_id,
            "user_agent": self.user_agent,
            "viewport": self.viewport,
            "timezone": self.timezone,
            "language": self.language,
            "is_logged_in": self.is_logged_in,
            "last_login_attempt": self.last_login_attempt.isoformat() if self.last_login_attempt else None,
            "login_success_count": self.login_success_count,
            "login_failure_count": self.login_failure_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_used": self.last_used.isoformat(),
            "usage_count": self.usage_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Deserialize from dictionary."""
        return cls(
            account_id=data["account_id"],
            platform=data["platform"],
            cookies=data.get("cookies", []),
            local_storage=data.get("local_storage", {}),
            session_storage=data.get("session_storage", {}),
            indexed_db=data.get("indexed_db", {}),
            proxy_id=data.get("proxy_id"),
            fingerprint_id=data.get("fingerprint_id"),
            user_agent=data.get("user_agent"),
            viewport=data.get("viewport"),
            timezone=data.get("timezone"),
            language=data.get("language"),
            is_logged_in=data.get("is_logged_in", False),
            last_login_attempt=datetime.fromisoformat(data["last_login_attempt"]) if data.get("last_login_attempt") else None,
            login_success_count=data.get("login_success_count", 0),
            login_failure_count=data.get("login_failure_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            last_used=datetime.fromisoformat(data["last_used"]),
            usage_count=data.get("usage_count", 0)
        )


class SessionPersistence:
    """
    Manages browser session persistence across automation runs.

    Features:
    - Cookie storage and recovery
    - localStorage/sessionStorage persistence
    - Login state tracking
    - Session health monitoring
    - Automatic cleanup of expired sessions
    """

    def __init__(self, db_path: str = "data/radar.sqlite"):
        """
        Initialize session persistence.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._sessions: Dict[str, SessionData] = {}  # account_id -> SessionData
        self._init_database()

    def _init_database(self):
        """Initialize SQLite tables for session storage."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    account_id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    cookies TEXT NOT NULL,  -- JSON
                    local_storage TEXT NOT NULL,  -- JSON
                    session_storage TEXT NOT NULL,  -- JSON
                    indexed_db TEXT NOT NULL,  -- JSON
                    proxy_id TEXT,
                    fingerprint_id TEXT,
                    user_agent TEXT,
                    viewport TEXT,  -- JSON
                    timezone TEXT,
                    language TEXT,
                    is_logged_in INTEGER DEFAULT 0,
                    last_login_attempt TEXT,
                    login_success_count INTEGER DEFAULT 0,
                    login_failure_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_used TEXT DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0
                )
            """)

            # Session health tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_health (
                    account_id TEXT PRIMARY KEY,
                    last_health_check TEXT,
                    is_healthy INTEGER DEFAULT 1,
                    consecutive_failures INTEGER DEFAULT 0,
                    total_requests INTEGER DEFAULT 0,
                    successful_requests INTEGER DEFAULT 0,
                    last_error TEXT,
                    FOREIGN KEY (account_id) REFERENCES sessions(account_id)
                )
            """)

            conn.commit()

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import uuid
        return str(uuid.uuid4())[:8]

    def save_session(self, session: SessionData) -> None:
        """
        Save session data to database.

        Args:
            session: SessionData to save
        """
        session.updated_at = datetime.now()
        session.last_used = datetime.now()
        session.usage_count += 1

        self._sessions[session.account_id] = session

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sessions
                (account_id, platform, cookies, local_storage, session_storage, indexed_db,
                 proxy_id, fingerprint_id, user_agent, viewport, timezone, language,
                 is_logged_in, last_login_attempt, login_success_count, login_failure_count,
                 created_at, updated_at, last_used, usage_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.account_id,
                session.platform,
                json.dumps(session.cookies),
                json.dumps(session.local_storage),
                json.dumps(session.session_storage),
                json.dumps(session.indexed_db),
                session.proxy_id,
                session.fingerprint_id,
                session.user_agent,
                json.dumps(session.viewport) if session.viewport else None,
                session.timezone,
                session.language,
                1 if session.is_logged_in else 0,
                session.last_login_attempt.isoformat() if session.last_login_attempt else None,
                session.login_success_count,
                session.login_failure_count,
                session.created_at.isoformat(),
                session.updated_at.isoformat(),
                session.last_used.isoformat(),
                session.usage_count
            ))
            conn.commit()

    def load_session(self, account_id: str) -> Optional[SessionData]:
        """
        Load session data from database.

        Args:
            account_id: Account ID to load session for

        Returns:
            SessionData or None if not found
        """
        if account_id in self._sessions:
            return self._sessions[account_id]

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM sessions WHERE account_id = ?", (account_id,)).fetchone()

            if row:
                session = SessionData(
                    account_id=row["account_id"],
                    platform=row["platform"],
                    cookies=json.loads(row["cookies"]) if row["cookies"] else [],
                    local_storage=json.loads(row["local_storage"]) if row["local_storage"] else {},
                    session_storage=json.loads(row["session_storage"]) if row["session_storage"] else {},
                    indexed_db=json.loads(row["indexed_db"]) if row["indexed_db"] else {},
                    proxy_id=row["proxy_id"],
                    fingerprint_id=row["fingerprint_id"],
                    user_agent=row["user_agent"],
                    viewport=json.loads(row["viewport"]) if row["viewport"] else None,
                    timezone=row["timezone"],
                    language=row["language"],
                    is_logged_in=bool(row["is_logged_in"]),
                    last_login_attempt=datetime.fromisoformat(row["last_login_attempt"]) if row["last_login_attempt"] else None,
                    login_success_count=row["login_success_count"] or 0,
                    login_failure_count=row["login_failure_count"] or 0,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    last_used=datetime.fromisoformat(row["last_used"]),
                    usage_count=row["usage_count"] or 0
                )

                self._sessions[account_id] = session
                return session

        return None

    def update_cookies(self, account_id: str, cookies: List[Dict[str, Any]]) -> None:
        """
        Update cookies for a session.

        Args:
            account_id: Account ID
            cookies: List of cookie dictionaries
        """
        session = self.load_session(account_id)
        if not session:
            return

        session.cookies = cookies
        session.updated_at = datetime.now()
        self.save_session(session)

    def update_local_storage(self, account_id: str, local_storage: Dict[str, str]) -> None:
        """
        Update localStorage for a session.

        Args:
            account_id: Account ID
            local_storage: localStorage data
        """
        session = self.load_session(account_id)
        if not session:
            return

        session.local_storage = local_storage
        session.updated_at = datetime.now()
        self.save_session(session)

    def update_login_status(self, account_id: str, is_logged_in: bool, success: bool = True) -> None:
        """
        Update login status for a session.

        Args:
            account_id: Account ID
            is_logged_in: Whether currently logged in
            success: Whether the login attempt was successful
        """
        session = self.load_session(account_id)
        if not session:
            return

        session.is_logged_in = is_logged_in
        session.last_login_attempt = datetime.now()

        if success:
            session.login_success_count += 1
        else:
            session.login_failure_count += 1

        session.updated_at = datetime.now()
        self.save_session(session)

    def get_session_health(self, account_id: str) -> Dict[str, Any]:
        """
        Get health statistics for a session.

        Args:
            account_id: Account ID

        Returns:
            Health statistics dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT * FROM session_health WHERE account_id = ?
            """, (account_id,)).fetchone()

            if row:
                return {
                    "last_health_check": datetime.fromisoformat(row["last_health_check"]) if row["last_health_check"] else None,
                    "is_healthy": bool(row["is_healthy"]),
                    "consecutive_failures": row["consecutive_failures"] or 0,
                    "total_requests": row["total_requests"] or 0,
                    "successful_requests": row["successful_requests"] or 0,
                    "success_rate": (row["successful_requests"] or 0) / max(row["total_requests"] or 1, 1),
                    "last_error": row["last_error"]
                }

        return {
            "last_health_check": None,
            "is_healthy": True,
            "consecutive_failures": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "success_rate": 1.0,
            "last_error": None
        }

    def update_session_health(self, account_id: str, success: bool, error: Optional[str] = None) -> None:
        """
        Update session health statistics.

        Args:
            account_id: Account ID
            success: Whether the request was successful
            error: Error message if failed
        """
        with sqlite3.connect(self.db_path) as conn:
            # Get current health data
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM session_health WHERE account_id = ?", (account_id,)).fetchone()

            if row:
                consecutive_failures = row["consecutive_failures"] or 0
                total_requests = row["total_requests"] or 0
                successful_requests = row["successful_requests"] or 0

                if success:
                    consecutive_failures = 0
                    successful_requests += 1
                else:
                    consecutive_failures += 1

                total_requests += 1
                is_healthy = consecutive_failures < 3  # Consider unhealthy after 3 consecutive failures

                conn.execute("""
                    UPDATE session_health
                    SET last_health_check = ?, is_healthy = ?, consecutive_failures = ?,
                        total_requests = ?, successful_requests = ?, last_error = ?
                    WHERE account_id = ?
                """, (
                    datetime.now().isoformat(),
                    1 if is_healthy else 0,
                    consecutive_failures,
                    total_requests,
                    successful_requests,
                    error,
                    account_id
                ))
            else:
                # Create new health record
                conn.execute("""
                    INSERT INTO session_health
                    (account_id, last_health_check, is_healthy, consecutive_failures,
                     total_requests, successful_requests, last_error)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    account_id,
                    datetime.now().isoformat(),
                    1 if success else 0,
                    0 if success else 1,
                    1,
                    1 if success else 0,
                    error
                ))

            conn.commit()

    def delete_session(self, account_id: str) -> None:
        """
        Delete session data.

        Args:
            account_id: Account ID to delete
        """
        self._sessions.pop(account_id, None)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM sessions WHERE account_id = ?", (account_id,))
            conn.execute("DELETE FROM session_health WHERE account_id = ?", (account_id,))
            conn.commit()

    def list_sessions(self, platform: Optional[str] = None) -> List[SessionData]:
        """
        List all sessions, optionally filtered by platform.

        Args:
            platform: Optional platform filter

        Returns:
            List of SessionData objects
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if platform:
                rows = conn.execute("SELECT * FROM sessions WHERE platform = ? ORDER BY last_used DESC", (platform,))
            else:
                rows = conn.execute("SELECT * FROM sessions ORDER BY last_used DESC")

            sessions = []
            for row in rows:
                session = SessionData(
                    account_id=row["account_id"],
                    platform=row["platform"],
                    cookies=json.loads(row["cookies"]) if row["cookies"] else [],
                    local_storage=json.loads(row["local_storage"]) if row["local_storage"] else {},
                    session_storage=json.loads(row["session_storage"]) if row["session_storage"] else {},
                    indexed_db=json.loads(row["indexed_db"]) if row["indexed_db"] else {},
                    proxy_id=row["proxy_id"],
                    fingerprint_id=row["fingerprint_id"],
                    user_agent=row["user_agent"],
                    viewport=json.loads(row["viewport"]) if row["viewport"] else None,
                    timezone=row["timezone"],
                    language=row["language"],
                    is_logged_in=bool(row["is_logged_in"]),
                    last_login_attempt=datetime.fromisoformat(row["last_login_attempt"]) if row["last_login_attempt"] else None,
                    login_success_count=row["login_success_count"] or 0,
                    login_failure_count=row["login_failure_count"] or 0,
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    last_used=datetime.fromisoformat(row["last_used"]),
                    usage_count=row["usage_count"] or 0
                )

                self._sessions[session.account_id] = session
                sessions.append(session)

            return sessions

    def cleanup_expired_sessions(self, max_age_days: int = 30) -> int:
        """
        Clean up old sessions.

        Args:
            max_age_days: Maximum age in days for sessions to keep

        Returns:
            Number of sessions deleted
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT account_id FROM sessions WHERE last_used < ?", (cutoff_date.isoformat(),))
            expired_accounts = [row[0] for row in cursor.fetchall()]

            if expired_accounts:
                # Delete from sessions table
                conn.execute("DELETE FROM sessions WHERE last_used < ?", (cutoff_date.isoformat(),))
                # Delete from health table
                conn.execute("DELETE FROM session_health WHERE account_id IN ({})".format(
                    ','.join('?' * len(expired_accounts))
                ), expired_accounts)

                conn.commit()

                # Remove from memory cache
                for account_id in expired_accounts:
                    self._sessions.pop(account_id, None)

                return len(expired_accounts)

        return 0

    def export_sessions(self, file_path: str, platform: Optional[str] = None) -> None:
        """
        Export sessions to JSON file.

        Args:
            file_path: Path to export file
            platform: Optional platform filter
        """
        sessions = self.list_sessions(platform)

        data = {
            "sessions": [s.to_dict() for s in sessions],
            "exported_at": datetime.now().isoformat(),
            "platform_filter": platform
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def import_sessions(self, file_path: str) -> int:
        """
        Import sessions from JSON file.

        Args:
            file_path: Path to import file

        Returns:
            Number of sessions imported
        """
        with open(file_path, 'r') as f:
            data = json.load(f)

        count = 0
        for session_data in data.get("sessions", []):
            session = SessionData.from_dict(session_data)
            self.save_session(session)
            count += 1

        return count

    def get_session_stats(self) -> Dict[str, Any]:
        """Get overall session statistics."""
        sessions = self.list_sessions()

        total_sessions = len(sessions)
        logged_in = sum(1 for s in sessions if s.is_logged_in)
        total_successes = sum(s.login_success_count for s in sessions)
        total_failures = sum(s.login_failure_count for s in sessions)

        platforms = {}
        for session in sessions:
            platforms[session.platform] = platforms.get(session.platform, 0) + 1

        return {
            "total_sessions": total_sessions,
            "logged_in_sessions": logged_in,
            "login_success_rate": total_successes / max(total_successes + total_failures, 1),
            "platforms": platforms,
            "avg_usage_per_session": sum(s.usage_count for s in sessions) / max(total_sessions, 1)
        }