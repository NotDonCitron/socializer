import pytest
from unittest.mock import MagicMock
from radar.tiktok import TikTokAutomator
from radar.browser import BrowserManager

@pytest.fixture
def mock_tiktok_automator():
    manager = MagicMock(spec=BrowserManager)
    automator = TikTokAutomator(manager, user_data_dir="/tmp/fake_tiktok")
    automator.page = MagicMock()
    return automator

def test_tiktok_upload_flow(mock_tiktok_automator):
    """
    Test the TikTok upload sequence:
    1. Navigation to upload
    2. Setting file
    3. Entering caption
    4. Clicking Post
    """
    mock_page = mock_tiktok_automator.page
    
    # Ensure selectors are "found"
    mock_page.is_visible.return_value = True
    
    # Run the method
    success = mock_tiktok_automator.upload_video("test_video.mp4", caption="TikTok Test")
    
    # Assertions
    assert mock_page.goto.called
    assert mock_page.set_input_files.called
    assert mock_page.keyboard.type.called
    assert mock_page.click.called
    assert success is True

def test_tiktok_upload_no_input(mock_tiktok_automator):
    """
    Test failure when upload input is not found.
    """
    mock_page = mock_tiktok_automator.page
    mock_page.wait_for_selector.side_effect = Exception("Not found")
    
    success = mock_tiktok_automator.upload_video("test_video.mp4")
    
    assert success is False
    assert "Could not find upload input" in mock_tiktok_automator.last_error
