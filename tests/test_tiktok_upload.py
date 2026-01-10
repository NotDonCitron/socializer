import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from radar.tiktok import TikTokAutomator
from radar.browser import BrowserManager

pytestmark = pytest.mark.skip(reason="TikTok flow disabled for Instagram-only deployment")


@pytest.fixture
def mock_tiktok_automator():
    manager = MagicMock(spec=BrowserManager)
    automator = TikTokAutomator(manager, user_data_dir="/tmp/fake_tiktok")
    automator.page = MagicMock()
    return automator


@pytest.fixture
def temp_video_file():
    """Create a temporary file to simulate a video."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fake video content")
        temp_path = f.name
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_tiktok_upload_flow(mock_tiktok_automator, temp_video_file):
    """
    Test the TikTok upload sequence:
    1. Navigation to upload
    2. Setting file
    3. Entering caption
    4. Clicking Post
    """
    mock_page = mock_tiktok_automator.page
    
    # Mock the page methods to simulate success
    mock_page.is_visible.return_value = False  # No loading indicators
    mock_page.is_enabled.return_value = True
    mock_page.wait_for_selector.return_value = MagicMock()
    mock_page.query_selector.return_value = MagicMock(bounding_box=lambda: {'x': 0, 'y': 0, 'width': 100, 'height': 50})
    mock_page.evaluate.return_value = {'x': 500, 'y': 500}
    mock_page.url = "https://www.tiktok.com/upload"
    
    # Mock success: first call to is_visible for loading is False, 
    # then for success dialog return True
    def side_effect(selector):
        if "Success" in selector or "uploaded" in selector:
            return True
        return False
    mock_page.is_visible.side_effect = side_effect

    # Patch time.sleep to avoid waiting
    with patch('time.sleep'):
        with patch('radar.tiktok.time.sleep'):  # Also patch in the module
            # Run the method with retry=False to avoid loops
            success = mock_tiktok_automator.upload_video(
                temp_video_file, 
                caption="TikTok Test",
                retry=False
            )
    
    # Assertions - the new implementation calls goto
    assert mock_page.goto.called
    assert mock_page.set_input_files.called
    assert success is True


def test_tiktok_upload_no_file(mock_tiktok_automator):
    """
    Test failure when video file does not exist.
    """
    success = mock_tiktok_automator.upload_video("nonexistent_video.mp4", retry=False)
    
    assert success is False
    assert "Video file not found" in mock_tiktok_automator.last_error


def test_tiktok_upload_no_page():
    """
    Test failure when page is not initialized.
    """
    manager = MagicMock(spec=BrowserManager)
    automator = TikTokAutomator(manager, user_data_dir="/tmp/fake_tiktok")
    # Don't set automator.page
    
    success = automator.upload_video("test.mp4", retry=False)
    
    assert success is False
    assert "Page not initialized" in automator.last_error


def test_retry_logic(mock_tiktok_automator, temp_video_file):
    """
    Test that retry logic respects max_retries.
    """
    mock_page = mock_tiktok_automator.page
    
    # Mock to always fail on finding elements
    mock_page.wait_for_selector.return_value = None
    mock_page.query_selector.return_value = None
    mock_page.is_visible.return_value = False
    
    # Set max retries to 1 for faster test
    mock_tiktok_automator.max_retries = 1
    
    with patch('time.sleep'):  # Skip actual waiting
        success = mock_tiktok_automator.upload_video(
            temp_video_file, 
            caption="Test",
            retry=True
        )
    
    assert success is False
    # Should have tried at least once
    assert mock_tiktok_automator.upload_attempts == 0  # Reset after failure


def test_verify_success_dialog(mock_tiktok_automator):
    """Test success verification via dialog."""
    mock_page = mock_tiktok_automator.page
    mock_page.is_visible.return_value = True
    
    with patch('radar.tiktok.time.sleep'):
        success = mock_tiktok_automator._verify_success(timeout=1)
    
    assert success is True


def test_verify_success_redirect(mock_tiktok_automator):
    """Test success verification via URL redirect."""
    mock_page = mock_tiktok_automator.page
    mock_page.is_visible.return_value = False
    mock_page.url = "https://www.tiktok.com/@user/video/123"
    
    with patch('radar.tiktok.time.sleep'):
        success = mock_tiktok_automator._verify_success(timeout=1)
    
    assert success is True


def test_dismiss_overlays(mock_tiktok_automator):
    """Test dismissing overlays."""
    mock_page = mock_tiktok_automator.page
    mock_page.is_visible.return_value = True
    mock_page.query_selector.return_value = MagicMock()
    
    mock_tiktok_automator._dismiss_overlays()
    
    # Should press Escape or click dismiss
    assert mock_page.keyboard.press.called or mock_page.click.called
