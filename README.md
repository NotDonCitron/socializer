# Socializer

A comprehensive Python-based automation framework for TikTok and Instagram using Playwright with advanced anti-detection measures.

## Features

- 🎭 **Stealth Mode**: Anti-detection browser flags, randomized viewport/UA, undetected ChromeDriver
- 🖱️ **Human-like Behavior**: Bezier mouse movement, variable typing delays
- 🔄 **Retry Logic**: Exponential backoff on failures
- 💾 **Session Management**: SQLite persistence, health checks, cookie-based authentication
- 🤖 **Auto Caption Generation**: AI-powered captions and hashtags based on image content
- 🌐 **Multi-language Support**: Works with both English and German Instagram interfaces

## Project Structure

- `socializer/`: Core source code and package
- `scripts/`: Helper scripts for maintenance and execution
- `socializer-api/`: API components with FastAPI backend
- `_bmad/`: BMAD methodology integration
- Content generation and scheduling system

## Installation

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # use `.venv\\Scripts\\activate` on Windows

# Install the core packages and shared requirements
pip install -e socializer/ -e socializer-api/
pip install -r requirements.txt

# Install Playwright browsers that the automation scripts rely on
playwright install chromium

# Optional: stealth helpers
pip install undetected-chromedriver selenium

# Enable the project's pre-commit hooks
pip install pre-commit
pre-commit install
```

## Quick Start

### Interactive Uploads (Playwright Mode)

```bash
# TikTok
python socializer/examples/tiktok_interactive.py

# Instagram
python socializer/examples/instagram_interactive.py

# Start API server
uvicorn socializer_api.main:app --reload --port 8000
```

### Basic Upload with Auto Caption (Stealth Mode)

```bash
./run_upload.sh stealth "/path/to/your/image.jpg"
```

## How It Works

### Authentication
- Uses pre-configured Instagram session cookies
- Automatically handles URL decoding for cookie values
- Validates login status before proceeding
- Persistent browser sessions stored in SQLite

### Auto Caption Generation
- Extracts hashtags from Instagram's search results
- Falls back to scraping hashtags from related posts
- Generates contextual captions with relevant hashtags
- Limits to 15 hashtags for optimal engagement

### Upload Process
- Navigates to Instagram and handles Create button
- Automatically detects and uploads specified files
- Handles multi-step upload flow (Crop → Filter → Share)
- Auto-fills caption with generated content

## Configuration

### Cookie Setup

Edit your automation scripts or use environment variables:

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
- Videos: `.mp4`, `.mov`, `.avi`

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
   - Use session persistence to avoid re-authentication

### Debug Mode
Scripts keep the browser open for inspection after completion for debugging purposes.

## Security Notes

- **Never share your session cookies** - they provide full account access
- **Never commit credentials** - use environment variables (`.env` file)
- **Use in a controlled environment** - the script automates browser actions
- **Regular cookie rotation** - Update cookies periodically for reliability
- **Respect platform ToS** - Use responsibly and don't spam

## Documentation

For more detailed information:
- Core package: [socializer/README.md](socializer/README.md)
- Agent system: [socializer/AGENTS.md](socializer/AGENTS.md)
- Claude Code integration: [CLAUDE.md](CLAUDE.md)
- BMAD methodology: [BMAD_QUICK_START.md](BMAD_QUICK_START.md)

## Dependencies

All runtime dependencies are declared in `requirements.txt` and in the `pyproject.toml` files for `socializer` and `socializer-api`. The stack relies on:

- `fastapi`, `uvicorn`, `pydantic` to power the API.
- `playwright` and `playwright-stealth` for browser automation.
- `undetected-chromedriver` and `selenium` for optional stealth-only flows.

Run `pip install -r requirements.txt` after activating your virtual environment to pull in the shared dependencies before working on the automation scripts.

## License

MIT License – see [LICENSE](LICENSE) for the full terms.

## Contributing

We welcome contributions! Please review [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) for the workflow, coding standards, testing requirements, and GitHub templates we expect contributors to follow before submitting work.
