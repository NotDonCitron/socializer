# Spec: TikTok Posting

## Goal
Enable the `TikTokAutomator` to upload videos to TikTok via the web interface.

## Requirements

### `upload_video(file_path: str, caption: str = "") -> bool`
1.  **Login Handling:** TikTok is very strict. Use persistent contexts.
2.  **Navigation:** Navigate to `https://www.tiktok.com/upload`.
3.  **File Picker:** Handle the `input[type="file"]`.
4.  **Flow:**
    *   Wait for upload processing.
    *   Enter caption.
    *   Click "Post".
5.  **Verification:** Detect success message or navigation back to profile.

## Challenges
*   **Intense Bot Detection:** TikTok uses sophisticated techniques to detect Playwright/Puppeteer.
*   **Captchas:** Frequent puzzles during login or upload.
*   **Dynamic Selectors:** UI changes often.
