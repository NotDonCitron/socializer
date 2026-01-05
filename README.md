# Instagram Stealth Uploader

Automated Instagram upload tool using undetected ChromeDriver with cookie-based authentication.

## Features

- **Stealth Mode**: Uses undetected ChromeDriver to avoid Instagram's bot detection
- **Cookie Authentication**: Bypasses login using pre-configured session cookies
- **Auto Caption Generation**: Automatically generates captions and hashtags based on image content
- **Smart File Detection**: Automatically finds files with common image extensions
- **Multi-language Support**: Works with both English and German Instagram interfaces

## Installation

1. Clone the repository and navigate to the directory
2. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install undetected-chromedriver selenium
   ```

## Usage

### Basic Upload with Auto Caption
```bash
./run_upload.sh stealth "/path/to/your/image.jpg"
```

### Manual Caption (if you modify the script)
The script will prompt for:
- Custom caption (leave empty for auto-generation)
- Topic for hashtag generation (e.g., nature, cats, gaming)

## How It Works

### 1. Authentication
- Uses pre-configured Instagram session cookies
- Automatically handles URL decoding for cookie values
- Validates login status before proceeding

### 2. Auto Caption Generation
- Extracts hashtags from Instagram's search results
- Falls back to scraping hashtags from related posts
- Generates contextual captions with relevant hashtags
- Limits to 15 hashtags for optimal engagement

### 3. Upload Process
- Navigates to Instagram and clicks "Create" button
- Automatically detects and uploads the specified file
- Handles the multi-step upload flow (Crop → Filter → Share)
- Auto-fills caption with generated content

## File Structure

```
.
├── run_upload.sh              # Main execution script
├── upload_instagram_stealth.py # Python automation script
├── venv/                      # Virtual environment
└── README.md                  # This documentation
```

## Configuration

### Cookie Setup
Edit `upload_instagram_stealth.py` to update your session cookies:

```python
manual_cookies = {
    "csrftoken": "YOUR_CSRF_TOKEN",
    "sessionid": "YOUR_SESSION_ID",
    "ds_user_id": "YOUR_USER_ID",
    # ... other cookies
}
```

### Supported File Types
- Images: `.png`, `.jpg`, `.jpeg`
- Videos: `.mp4`, `.mov`

## Troubleshooting

### Common Issues

1. **"File not found" Error**
   - Check file path and extension
   - Script automatically tries common extensions if exact match fails

2. **"Still on login page"**
   - Cookies may be expired
   - Update session cookies in the script

3. **"Could not find Create button"**
   - Script will wait for manual interaction
   - Click the [+] button manually when prompted

4. **Bot Detection**
   - If flagged, wait before retrying
   - Consider updating ChromeDriver version

### Debug Mode
To see what's happening, the script keeps the browser open for 60 seconds after completion.

## Security Notes

- **Never share your session cookies** - they provide full account access
- **Use in a controlled environment** - the script automates browser actions
- **Regular cookie rotation** - Update cookies periodically for reliability
- **Respect Instagram's ToS** - Use responsibly and don't spam

## Advanced Usage

### Custom Topics
Modify the default topic in the script for better hashtag generation:

```python
topic = "your_custom_topic"  # Instead of "screenshot"
```

### Manual Caption
Edit the script to enable manual caption input if needed.

## Dependencies

- `undetected-chromedriver`: Anti-detection Chrome driver
- `selenium`: Web browser automation
- `python3`: Runtime environment

## License

Use responsibly. This tool is for educational purposes and personal automation only.