import pytest
from unittest.mock import MagicMock, call
from radar.instagram import InstagramAutomator
from radar.browser import BrowserManager

@pytest.fixture
def mock_automator():
    manager = MagicMock(spec=BrowserManager)
    automator = InstagramAutomator(manager, user_data_dir="/tmp/fake")
    automator.page = MagicMock()
    return automator

def test_upload_photo_flow(mock_automator):
    """
    Test the upload_photo sequence:
    1. Click 'New Post'
    2. Handle FileChooser
    3. Click Next (Crop)
    4. Click Next (Filter)
    5. Enter Caption
    6. Click Share
    """
    # Setup mocks
    mock_page = mock_automator.page
    
    mock_context_manager = mock_page.expect_file_chooser.return_value
    mock_info = MagicMock()
    mock_context_manager.__enter__.return_value = mock_info
    
    mock_file_chooser = MagicMock()
    mock_info.value = mock_file_chooser
    
    # Ensure is_visible returns True so buttons are "found"
    mock_page.is_visible.return_value = True

    # Run the method
    success = mock_automator.upload_photo("test_image.jpg", caption="Hello World")
    
    # Assertions
    assert mock_page.click.called
    mock_file_chooser.set_files.assert_called_with("test_image.jpg")
    assert success is True

def test_upload_video_flow(mock_automator):
    """
    Test the upload sequence with a video file.
    """
    mock_page = mock_automator.page
    mock_context_manager = mock_page.expect_file_chooser.return_value
    mock_info = MagicMock()
    mock_context_manager.__enter__.return_value = mock_info
    mock_file_chooser = MagicMock()
    mock_info.value = mock_file_chooser
    
    mock_page.is_visible.return_value = True

    # Run the method with an mp4 file
    success = mock_automator.upload_photo("test_video.mp4", caption="Video Test")
    
    assert success is True
    mock_file_chooser.set_files.assert_called_with("test_video.mp4")
    assert mock_page.click.called

def test_upload_photo_file_chooser_timeout(mock_automator):
    """
    Test failure when file chooser doesn't appear.
    """
    mock_page = mock_automator.page
    # Make expect_file_chooser raise an error
    mock_page.expect_file_chooser.side_effect = Exception("Timeout")
    
    success = mock_automator.upload_photo("test_image.jpg")
    
    assert success is False
    assert "Timeout" in mock_automator.last_error