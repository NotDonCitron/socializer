import pytest
from radar.browser import BrowserManager
# We expect to create an InstagramAutomator in radar/instagram.py
# from radar.instagram import InstagramAutomator

def test_instagram_login_navigation(tmp_path):
    """
    Test that the automator can navigate to the login page.
    """
    # This will fail because InstagramAutomator doesn't exist yet
    from radar.instagram import InstagramAutomator

    with BrowserManager() as manager:
        browser = manager.launch_browser(headless=True)
        # Using a temporary user data dir for persistent context test
        user_data_dir = tmp_path / "test_ig_user_data"

        automator = InstagramAutomator(manager, user_data_dir=str(user_data_dir))
        # We don't provide real credentials here, just testing navigation/structure
        success = automator.login("test_user", "test_pass")

        # In a real test without credentials, this might fail,
        # but we want to check if it at least tried to navigate.
        assert not success # Should be false with fake creds

def test_instagram_login_failure_detection(tmp_path):
    """
    Test that the automator detects a failed login message.
    """
    from radar.instagram import InstagramAutomator

    with BrowserManager() as manager:
        browser = manager.launch_browser(headless=True)
        user_data_dir = tmp_path / "test_ig_failure_data"

        automator = InstagramAutomator(manager, user_data_dir=str(user_data_dir))
        # Using a password that is definitely wrong and a short timeout
        success = automator.login("invalid_user_name_xyz_123", "wrong_password_abc", timeout=10000)

        assert not success
        assert automator.last_error is not None
        print(f"Detected error: {automator.last_error}")
