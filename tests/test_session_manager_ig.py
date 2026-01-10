"""
Tests for session management functions for Instagram.

Validates cookie loading, session validation, and cookie sanitization.
"""
import json
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from radar.session_manager import load_playwright_cookies, save_playwright_cookies


@pytest.fixture
def mock_context():
    """Create a mock Playwright BrowserContext."""
    context = MagicMock()
    context.add_cookies = MagicMock()
    context.cookies = MagicMock(return_value=[])
    return context


@pytest.fixture
def sample_cookies():
    """Sample cookie data for testing."""
    return [
        {
            "name": "sessionid",
            "value": "abc123",
            "domain": ".instagram.com",
            "path": "/",
            "expires": 1735689600,
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax"
        },
        {
            "name": "csrftoken",
            "value": "xyz789",
            "domain": ".instagram.com",
            "path": "/",
            "expires": 1735689600,
            "httpOnly": False,
            "secure": True,
            "sameSite": "Strict"
        }
    ]


@pytest.fixture
def invalid_samesite_cookies():
    """Cookies with invalid sameSite values (from Selenium export)."""
    return [
        {
            "name": "test_cookie",
            "value": "test_value",
            "domain": ".instagram.com",
            "sameSite": "unspecified"  # Invalid - should be removed
        },
        {
            "name": "another_cookie",
            "value": "another_value",
            "domain": ".instagram.com",
            "sameSite": True  # Invalid boolean - should be removed
        }
    ]


class TestLoadPlaywrightCookies:
    """Tests for load_playwright_cookies function."""

    def test_load_cookies_from_valid_file(self, mock_context, sample_cookies, tmp_path):
        """Should load cookies from a valid JSON file."""
        cookie_file = tmp_path / "cookies.json"
        cookie_file.write_text(json.dumps(sample_cookies))
        
        load_playwright_cookies(mock_context, str(cookie_file))
        
        mock_context.add_cookies.assert_called_once()
        loaded_cookies = mock_context.add_cookies.call_args[0][0]
        assert len(loaded_cookies) == 2
        assert loaded_cookies[0]["name"] == "sessionid"

    def test_load_cookies_cleans_invalid_samesite(self, mock_context, invalid_samesite_cookies, tmp_path):
        """Should remove invalid sameSite values from cookies."""
        cookie_file = tmp_path / "cookies.json"
        cookie_file.write_text(json.dumps(invalid_samesite_cookies))
        
        load_playwright_cookies(mock_context, str(cookie_file))
        
        loaded_cookies = mock_context.add_cookies.call_args[0][0]
        for cookie in loaded_cookies:
            assert "sameSite" not in cookie, "Invalid sameSite should be removed"

    def test_load_cookies_preserves_valid_samesite(self, mock_context, sample_cookies, tmp_path):
        """Should preserve valid sameSite values (Strict, Lax, None)."""
        cookie_file = tmp_path / "cookies.json"
        cookie_file.write_text(json.dumps(sample_cookies))
        
        load_playwright_cookies(mock_context, str(cookie_file))
        
        loaded_cookies = mock_context.add_cookies.call_args[0][0]
        assert loaded_cookies[0]["sameSite"] == "Lax"
        assert loaded_cookies[1]["sameSite"] == "Strict"

    def test_load_cookies_handles_missing_file(self, mock_context, capsys):
        """Should handle missing cookie file gracefully."""
        load_playwright_cookies(mock_context, "/nonexistent/path/cookies.json")
        
        mock_context.add_cookies.assert_not_called()
        captured = capsys.readouterr()
        assert "No cookies found" in captured.out

    def test_load_cookies_handles_invalid_json(self, mock_context, tmp_path, capsys):
        """Should handle invalid JSON gracefully."""
        cookie_file = tmp_path / "cookies.json"
        cookie_file.write_text("not valid json {{{")
        
        load_playwright_cookies(mock_context, str(cookie_file))
        
        mock_context.add_cookies.assert_not_called()
        captured = capsys.readouterr()
        assert "Failed to load" in captured.out


class TestSavePlaywrightCookies:
    """Tests for save_playwright_cookies function."""

    def test_save_cookies_creates_file(self, mock_context, sample_cookies, tmp_path):
        """Should save cookies to a JSON file."""
        mock_context.cookies.return_value = sample_cookies
        cookie_path = tmp_path / "session" / "cookies.json"
        
        with patch('radar.session_manager.COOKIES_PATH', str(cookie_path)):
            save_playwright_cookies(mock_context)
        
        assert cookie_path.exists()
        saved_data = json.loads(cookie_path.read_text())
        assert len(saved_data) == 2
        assert saved_data[0]["name"] == "sessionid"

    def test_save_cookies_creates_parent_directory(self, mock_context, sample_cookies, tmp_path):
        """Should create parent directories if they don't exist."""
        mock_context.cookies.return_value = sample_cookies
        cookie_path = tmp_path / "deeply" / "nested" / "cookies.json"
        
        with patch('radar.session_manager.COOKIES_PATH', str(cookie_path)):
            save_playwright_cookies(mock_context)
        
        assert cookie_path.parent.exists()


class TestInstagramSessionValidation:
    """Tests for Instagram-specific session validation."""

    def test_validate_instagram_session_with_profile_visible(self):
        """Should detect valid session when profile icon is visible."""
        # Note: validate_instagram_session doesn't exist yet for Instagram
        # This is a placeholder for when it's implemented
        pass

    def test_validate_instagram_session_on_login_page(self):
        """Should detect invalid session when on login page."""
        # Placeholder for Instagram session validation
        pass


class TestCookieSanitization:
    """Tests for cookie cleanup and sanitization."""

    def test_remove_expired_cookies(self, mock_context, tmp_path):
        """Should handle expired cookies appropriately."""
        expired_cookies = [
            {
                "name": "expired",
                "value": "old",
                "domain": ".instagram.com",
                "expires": 0  # Epoch = expired
            }
        ]
        cookie_file = tmp_path / "cookies.json"
        cookie_file.write_text(json.dumps(expired_cookies))
        
        # Cookies are loaded as-is; expiration is handled by Playwright
        load_playwright_cookies(mock_context, str(cookie_file))
        
        mock_context.add_cookies.assert_called_once()

    def test_handles_cookies_without_optional_fields(self, mock_context, tmp_path):
        """Should handle cookies missing optional fields."""
        minimal_cookies = [
            {
                "name": "minimal",
                "value": "data",
                "domain": ".instagram.com"
            }
        ]
        cookie_file = tmp_path / "cookies.json"
        cookie_file.write_text(json.dumps(minimal_cookies))
        
        load_playwright_cookies(mock_context, str(cookie_file))
        
        mock_context.add_cookies.assert_called_once()
        loaded = mock_context.add_cookies.call_args[0][0]
        assert loaded[0]["name"] == "minimal"
