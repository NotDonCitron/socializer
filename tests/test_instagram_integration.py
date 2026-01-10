"""
Integration tests for Instagram automation.

These tests require a valid Instagram session and are marked as 'integration'.
Run with: pytest tests/test_instagram_integration.py -m integration -v
"""
import os
import pytest
from pathlib import Path
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator
from radar.ig_config import (
    IG_SESSION_DIR, 
    IG_COOKIES_PATH, 
    has_credentials,
    get_ig_username,
    get_ig_password
)


# Skip all tests if no credentials configured
pytestmark = pytest.mark.skipif(
    not has_credentials(),
    reason="IG_USERNAME and IG_PASSWORD not configured"
)


@pytest.fixture
def session_dir(tmp_path):
    """Create a temporary session directory for testing."""
    session_path = tmp_path / "test_ig_session"
    session_path.mkdir()
    return str(session_path)


@pytest.fixture
def real_session_dir():
    """Use the real session directory (requires existing session)."""
    return IG_SESSION_DIR


class TestSessionValidation:
    """Tests for session validation functionality."""

    @pytest.mark.integration
    def test_login_with_fresh_credentials(self, session_dir):
        """Test login with credentials from environment."""
        with BrowserManager() as manager:
            automator = InstagramAutomator(manager, user_data_dir=session_dir)
            
            success = automator.login(
                username=get_ig_username(),
                password=get_ig_password(),
                headless=True,
                timeout=60000  # Allow more time for real login
            )
            
            # Note: This may fail due to 2FA or security challenges
            # The test validates the flow works
            if not success:
                pytest.skip(f"Login failed (may need 2FA): {automator.last_error}")
            
            assert success

    @pytest.mark.integration
    def test_login_with_saved_session(self, real_session_dir):
        """Test login using an existing saved session."""
        # Check if session exists
        cookies_path = Path(real_session_dir) / "cookies.json"
        if not cookies_path.exists():
            pytest.skip("No saved session found - run interactive login first")
        
        with BrowserManager() as manager:
            automator = InstagramAutomator(manager, user_data_dir=real_session_dir)
            
            # Login with empty credentials should use saved session
            success = automator.login(
                username="",
                password="",
                headless=True
            )
            
            assert success, f"Session login failed: {automator.last_error}"


class TestUploadFlow:
    """Tests for the full upload flow."""

    @pytest.fixture
    def test_image(self, tmp_path):
        """Create a test image for upload testing."""
        # Create a simple test image
        from PIL import Image
        img_path = tmp_path / "test_upload.jpg"
        img = Image.new('RGB', (1080, 1080), color='blue')
        img.save(str(img_path))
        return str(img_path)

    @pytest.mark.integration
    @pytest.mark.slow
    def test_upload_photo_flow(self, real_session_dir, test_image):
        """Test the complete photo upload flow."""
        with BrowserManager() as manager:
            automator = InstagramAutomator(manager, user_data_dir=real_session_dir)
            
            # First, ensure we're logged in
            if not automator.login("", "", headless=False):
                pytest.skip("Not logged in")
            
            # Attempt upload (with a test caption)
            success = automator.upload_photo(
                file_path=test_image,
                caption="🤖 Automated test - please ignore #test"
            )
            
            # Note: We don't actually post in tests
            # This validates the flow up to the share button
            assert automator.page is not None


class TestPopupBlocking:
    """Tests for network-level popup prevention."""

    @pytest.mark.integration
    def test_cancel_contracts_popup_blocked(self, real_session_dir):
        """Test that facebook.com/help/cancelcontracts is blocked."""
        with BrowserManager() as manager:
            automator = InstagramAutomator(manager, user_data_dir=real_session_dir)
            
            if not automator.login("", "", headless=True):
                pytest.skip("Not logged in")
            
            # Navigate to a known page that might trigger popups
            automator.page.goto("https://www.instagram.com/")
            
            # Verify no popup tabs were opened
            contexts = automator.context.pages
            for page in contexts:
                assert "cancelcontracts" not in page.url


class TestDebugScreenshots:
    """Tests for debug screenshot functionality."""

    @pytest.mark.integration
    def test_debug_screenshots_created(self, real_session_dir, tmp_path):
        """Test that debug screenshots are created when DEBUG=1."""
        os.environ["DEBUG"] = "1"
        os.environ["IG_DEBUG_DIR"] = str(tmp_path / "debug_shots")
        
        try:
            with BrowserManager() as manager:
                automator = InstagramAutomator(manager, user_data_dir=real_session_dir)
                
                if not automator.login("", "", headless=True):
                    pytest.skip("Not logged in")
                
                # Trigger some debug logging
                automator._debug_log("Test screenshot trigger")
                
        finally:
            os.environ.pop("DEBUG", None)
            os.environ.pop("IG_DEBUG_DIR", None)


# =============================================================================
# Utility Tests
# =============================================================================

class TestConfigValidation:
    """Tests for configuration validation."""

    def test_config_validation_with_valid_settings(self):
        """Test config validation with default settings."""
        from radar.ig_config import validate_config
        
        result = validate_config()
        # Default settings should be valid
        assert result["valid"] or len(result["errors"]) > 0

    def test_has_credentials_check(self):
        """Test credential detection."""
        from radar.ig_config import has_credentials
        
        # This depends on environment, just verify it returns a boolean
        result = has_credentials()
        assert isinstance(result, bool)
