# Spec: Instagram Posting

## Goal
Enable the `InstagramAutomator` to upload single photos to the Instagram feed via the mobile web interface emulation.

## Requirements

### `upload_photo(file_path: str, caption: str = "") -> bool`
1.  **Navigation:** Must ensure the "New Post" button is visible (usually the `+` icon in the bottom bar on mobile view).
2.  **File Picker:** Must handle the system file picker using Playwright's `page.set_input_files`.
3.  **Flow Navigation:**
    *   Click `+` -> Select File.
    *   Click "Next" (Crop screen).
    *   Click "Next" (Filter screen).
    *   Enter Caption.
    *   Click "Share".
4.  **Verification:** Return `True` if the "Post shared" confirmation (or equivalent) is detected.

## Edge Cases
*   **Popup Dialogs:** "Turn on Notifications?" or "Add to Home Screen?" popups might interrupt the flow.
*   **Selector Changes:** Instagram updates IDs/Classes frequently. Use resilient selectors (ARIA labels, text content) where possible.
