# Instagram Automation Hardening

This document details the hardening measures implemented in `radar/instagram.py` to ensure robust upload flows for Instagram Reels and Posts on Desktop.

## Core Challenges Solved

1.  **"Cancel Contracts" & EU Consumer Rights Popups**
    *   **Issue:** Instagram/Facebook frequently opens new tabs/windows pointing to `facebook.com/help/cancelcontracts` or transparency pages, stealing focus and stalling the automation.
    *   **Solution:**
        *   **Network Blocking:** We explicitly abort requests to these URLs at the network layer using `context.route(..., lambda route: route.abort())`.
        *   **Aggressive Page Handling:** A global `context.on("page", ...)` handler detects these popups immediately, closes them, and brings the main page back to front.

2.  **Brittle "Next" / "Share" Buttons**
    *   **Issue:** Standard selectors like `button:has-text("Next")` were failing because the DOM often contains hidden buttons or alternate layouts (e.g., mobile views hidden on desktop).
    *   **Solution:**
        *   **Scoped Selectors:** All button searches are now scoped to the active `div[role="dialog"]` to avoid finding elements in the background.
        *   **Iterative Visible Check:** Instead of selecting the `.first` match of a combined selector, we iterate through a list of robust candidates (e.g., `div._ac7d [role="button"]`) and click the first one that is confirmed **visible**.

3.  **Edit -> Caption Transition Race Conditions**
    *   **Issue:** Clicking "Next" on the Edit screen sometimes didn't register, or the script checked for the Caption screen too early/late.
    *   **Solution:**
        *   **Robust State Detection:** The script uses the presence of the "Share" button to definitively confirm arrival at the Caption screen.
        *   **Retry Loop:** The transition logic attempts to click "Next" and checks for the new state up to 3 times before failing.

## Key Methods

### `_handle_new_page(self, page: Page)`
Automatically detects and closes blocking tabs. 

### `_upload_media(self, file_path, retry=True)`
Handles the file chooser and initial "Crop" screen.
*   **Feature:** Dispatches `input`, `blur`, and `focus` events to the file input to ensure React registers the file change.
*   **Feature:** Checks for immediate error messages (e.g., "Video too short") inside the dialog.

### `upload_video(self, file_path, caption, timeout)`
Orchestrates the full flow: Create -> Upload -> Crop -> Edit -> Caption -> Share.
*   **Feature:** Defines selectors *before* loops to avoid scope errors.
*   **Feature:** Uses robust "Share" button detection to verify state transitions.

## Debugging

To debug issues, run with `DEBUG=1`:

```bash
DEBUG=1 python3 your_script.py
```

This enables:
1.  **Screenshots:** Saved to `debug_shots/` with timestamps and step names.
2.  **HTML Dumps:** On failure, the inner HTML of the dialog is saved to `debug_shots/` for inspection.
3.  **Verbose Logging:** Prints detailed step-by-step progress and selector matches.

## Selectors Reference

If the UI changes, check these key selectors in `radar/instagram.py`:

*   **Dialog:** `div[role="dialog"]`
*   **Next/Share Header Container:** `div._ac7d`
*   **Next Button:** `div._ac7d [role="button"]`, `button:has-text("Next")`
*   **Share Button:** `div._ac7d [role="button"]` (distinguished by text "Share"/"Teilen")
*   **Caption Area:** `div[aria-label*="Write a caption"]`, `div[role="textbox"]`

---

## Production Deployment Checklist

### Pre-Flight Checks

- [ ] Python 3.11+ installed
- [ ] Playwright installed (`pip install playwright && playwright install chromium`)
- [ ] Dependencies installed (`pip install -e .`)

### Environment Setup

1. **Copy environment template:**
   ```powershell
   Copy-Item .env.example .env
   ```

2. **Configure credentials in `.env`:**
   ```env
   IG_USERNAME=your_test_account
   IG_PASSWORD=your_password
   IG_SESSION_DIR=ig_session
   IG_MAX_RETRIES=3
   ```

3. **Initialize session (first time only):**
   ```powershell
   python examples/instagram_interactive.py
   ```
   > Complete login manually in the browser, including any 2FA steps.

### Session Management

**Important:** Always use the same session directory to avoid rate limiting.

| Environment Variable | Purpose | Default |
|---------------------|---------|---------|
| `IG_SESSION_DIR` | Browser session storage | `ig_session` |
| `IG_MAX_RETRIES` | Retry attempts on failure | `3` |
| `IG_RETRY_DELAY` | Base delay between retries | `5.0`s |

### Running Uploads

**Windows PowerShell:**
```powershell
.\run_ig_upload.ps1 "C:\Videos\my_reel.mp4" "Caption here #hashtag"
```

**Direct Python:**
```powershell
$env:DEBUG = "1"  # Optional: enable debug screenshots
python examples/instagram_test_video.py
```

### Monitoring

- Debug screenshots saved to `debug_shots/` when `DEBUG=1`
- Check `automator.last_error` for failure details
- Session cookies auto-saved after successful operations

### Rate Limit Prevention

1. **Use consistent credentials** - Load from `.env` file
2. **Use persistent session** - Set `IG_SESSION_DIR` 
3. **Add delays** - Human-like pauses between actions
4. **Avoid repeated logins** - Session should persist

