"""
Session management for persistent browser sessions.

Provides SQLite-based storage for cookies, session states, and expiry tracking
to maintain long-running automation sessions across script restarts.
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from playwright.sync_api import Page, BrowserContext


class SessionManager:
    """
    Manages browser session persistence with SQLite storage.
    
    Features:
    - Cookie and storage state persistence
    - Expiry tracking and auto-refresh detection
    - Multi-account session isolation
    - Health check validation
    """
    
    def __init__(self, db_path: str = "sessions.db"):
        """
        Initialize session manager with database path.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self._init_db()
    
    def _init_db(self) -> None:
        """Create database tables if they don't exist."""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                account_id TEXT PRIMARY KEY,
                platform TEXT NOT NULL,
                cookies TEXT,
                storage_state TEXT,
                user_data_dir TEXT,
                proxy TEXT,
                user_agent TEXT,
                last_used TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_valid INTEGER DEFAULT 1
            )
        ''')
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS session_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT,
                event_type TEXT,
                event_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
    
    def save_session(
        self, 
        account_id: str,
        platform: str,
        context: BrowserContext,
        user_data_dir: Optional[str] = None,
        proxy: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_days: int = 7
    ) -> None:
        """
        Save browser context session to database.
        
        Args:
            account_id: Unique identifier for the account
            platform: Platform name (tiktok, instagram)
            context: Playwright BrowserContext to save
            user_data_dir: Path to persistent user data directory
            proxy: Proxy server URL if used
            user_agent: Custom user agent if used
            expires_days: Days until session should be refreshed
        """
        cookies = context.cookies()
        storage_state = context.storage_state()
        
        # Try to determine expiry from session cookie
        expires_at = datetime.now() + timedelta(days=expires_days)
        session_cookie = next(
            (c for c in cookies if 'session' in c.get('name', '').lower()),
            None
        )
        if session_cookie and 'expires' in session_cookie:
            try:
                expires_at = datetime.fromtimestamp(session_cookie['expires'])
            except (ValueError, TypeError):
                pass
        
        self.conn.execute('''
            INSERT OR REPLACE INTO sessions 
            (account_id, platform, cookies, storage_state, user_data_dir, 
             proxy, user_agent, last_used, expires_at, is_valid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (
            account_id,
            platform,
            json.dumps(cookies),
            json.dumps(storage_state),
            user_data_dir,
            proxy,
            user_agent,
            datetime.now(),
            expires_at
        ))
        self.conn.commit()
        
        self._log_event(account_id, 'session_saved', {'expires_at': str(expires_at)})
    
    def load_session(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session data for an account.
        
        Args:
            account_id: Unique identifier for the account
            
        Returns:
            Dict with session data, or None if not found
        """
        cursor = self.conn.execute('''
            SELECT platform, cookies, storage_state, user_data_dir, 
                   proxy, user_agent, last_used, expires_at, is_valid
            FROM sessions WHERE account_id = ?
        ''', (account_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        return {
            'account_id': account_id,
            'platform': row[0],
            'cookies': json.loads(row[1]) if row[1] else [],
            'storage_state': json.loads(row[2]) if row[2] else None,
            'user_data_dir': row[3],
            'proxy': row[4],
            'user_agent': row[5],
            'last_used': row[6],
            'expires_at': row[7],
            'is_valid': bool(row[8]),
        }
    
    def needs_refresh(self, account_id: str, buffer_days: int = 1) -> bool:
        """
        Check if session needs to be refreshed.
        
        Args:
            account_id: Unique identifier for the account
            buffer_days: Refresh this many days before actual expiry
            
        Returns:
            True if session should be refreshed
        """
        cursor = self.conn.execute('''
            SELECT expires_at, is_valid FROM sessions WHERE account_id = ?
        ''', (account_id,))
        
        row = cursor.fetchone()
        if not row:
            return True  # No session found
        
        if not row[1]:
            return True  # Session marked invalid
        
        try:
            expires = datetime.fromisoformat(row[0])
            threshold = datetime.now() + timedelta(days=buffer_days)
            return expires < threshold
        except (ValueError, TypeError):
            return True
    
    def mark_invalid(self, account_id: str, reason: str = "unknown") -> None:
        """
        Mark a session as invalid (requires re-login).
        
        Args:
            account_id: Unique identifier for the account
            reason: Reason for invalidation
        """
        self.conn.execute('''
            UPDATE sessions SET is_valid = 0 WHERE account_id = ?
        ''', (account_id,))
        self.conn.commit()
        
        self._log_event(account_id, 'session_invalidated', {'reason': reason})
    
    def update_last_used(self, account_id: str) -> None:
        """Update the last_used timestamp for an account."""
        self.conn.execute('''
            UPDATE sessions SET last_used = ? WHERE account_id = ?
        ''', (datetime.now(), account_id))
        self.conn.commit()
    
    def get_all_accounts(self, platform: Optional[str] = None) -> list:
        """
        Get all stored account IDs.
        
        Args:
            platform: Filter by platform (tiktok, instagram)
            
        Returns:
            List of account_id strings
        """
        if platform:
            cursor = self.conn.execute('''
                SELECT account_id FROM sessions WHERE platform = ?
            ''', (platform,))
        else:
            cursor = self.conn.execute('SELECT account_id FROM sessions')
        
        return [row[0] for row in cursor.fetchall()]
    
    def delete_session(self, account_id: str) -> None:
        """
        Delete a session from the database.
        
        Args:
            account_id: Unique identifier for the account
        """
        self.conn.execute('DELETE FROM sessions WHERE account_id = ?', (account_id,))
        self.conn.commit()
        self._log_event(account_id, 'session_deleted', {})
    
    def _log_event(self, account_id: str, event_type: str, event_data: dict) -> None:
        """Log a session event for debugging/auditing."""
        self.conn.execute('''
            INSERT INTO session_logs (account_id, event_type, event_data)
            VALUES (?, ?, ?)
        ''', (account_id, event_type, json.dumps(event_data)))
        self.conn.commit()
    
    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def validate_tiktok_session(page: Page) -> Dict[str, Any]:
    """
    Validate a TikTok session without performing expensive actions.
    
    Args:
        page: Playwright Page with TikTok loaded
        
    Returns:
        Dict with validation status and details
    """
    result = {'valid': False, 'reason': 'unknown'}
    
    try:
        # Check if we're on a login page
        if 'login' in page.url.lower():
            result['reason'] = 'redirected_to_login'
            return result
        
        # Try to find user avatar or profile indicator
        user_indicators = [
            '[data-e2e="profile-icon"]',
            '[class*="avatar"]',
            'a[href*="/profile"]',
        ]
        
        for selector in user_indicators:
            try:
                if page.is_visible(selector):
                    result['valid'] = True
                    result['reason'] = 'user_indicator_found'
                    return result
            except Exception:
                continue
        
        # Check for upload button as login indicator
        if page.is_visible('a[href*="upload"]') or page.is_visible('[data-e2e="upload-icon"]'):
            result['valid'] = True
            result['reason'] = 'upload_access'
            return result
        
        result['reason'] = 'no_login_indicators'
        return result
        
    except Exception as e:
        result['reason'] = f'error: {str(e)}'
        return result


def validate_instagram_session(page: Page) -> Dict[str, Any]:
    """
    Validate an Instagram session without performing expensive actions.
    
    Args:
        page: Playwright Page with Instagram loaded
        
    Returns:
        Dict with validation status and details
    """
    result = {'valid': False, 'reason': 'unknown'}
    
    try:
        # Check if we're on a login page
        if 'login' in page.url.lower() or 'accounts/login' in page.url:
            result['reason'] = 'redirected_to_login'
            return result
        
        # Try to find logged-in user indicators
        user_indicators = [
            'svg[aria-label="Home"]',
            'a[href*="/direct/inbox"]',
            'svg[aria-label="New post"]',
            'svg[aria-label="Create"]',
        ]
        
        for selector in user_indicators:
            try:
                if page.is_visible(selector):
                    result['valid'] = True
                    result['reason'] = 'user_indicator_found'
                    return result
            except Exception:
                continue
        
        result['reason'] = 'no_login_indicators'
        return result
        
    except Exception as e:
        result['reason'] = f'error: {str(e)}'
        return result
