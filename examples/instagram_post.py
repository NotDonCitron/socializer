import os
import time
from radar.browser import BrowserManager
from radar.instagram import InstagramAutomator

def main():
    username = os.environ.get("IG_USER")
    password = os.environ.get("IG_PASS")
    user_data_dir = os.path.join(os.getcwd(), "ig_session")
    
    # Path to an image file you want to upload
    image_path = os.path.join(os.getcwd(), "test_image.jpg")
    
    # Ensure a test image exists
    if not os.path.exists(image_path):
        print(f"Error: {image_path} does not exist. Please put a 'test_image.jpg' in the current directory.")
        return

    print(f"Starting Instagram Post for user: {username}")
    
    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=user_data_dir)
        
        # 1. Login
        success = automator.login(username, password, headless=False)
        if not success:
            print(f"Login failed: {automator.last_error}")
            return
            
        print("Logged in. Attempting upload...")
        time.sleep(2)
        
        # 2. Upload
        if automator.upload_photo(image_path, caption="Automated post via #Playwright #Python"):
            print("SUCCESS: Post should be live!")
        else:
            print(f"UPLOAD FAILED: {automator.last_error}")
            
        time.sleep(5)

if __name__ == "__main__":
    main()
