# CLAUDE.md - Socializer Project Guidelines

## Project Overview
Socializer is a Python-based automation framework for TikTok and Instagram using Playwright with advanced anti-detection measures. The project includes:
- Core automation package (`socializer/`)
- FastAPI backend (`socializer-api/`)
- BMAD methodology integration (`_bmad/`)
- Content generation and scheduling

## Befehle / Commands

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install main package
pip install -e socializer/

# Install API package
pip install -e socializer-api/

# Install Playwright browsers
playwright install chromium
```

### Running the Application
```bash
# Start the API server (FastAPI)
uvicorn socializer_api.main:app --reload --port 8000

# Alternative: Run with custom port
uvicorn socializer_api.main:app --reload --port 8001

# Run TikTok interactive uploader
python socializer/examples/tiktok_interactive.py

# Run Instagram interactive uploader
python socializer/examples/instagram_interactive.py
```

### Testing
```bash
# Run tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_specific.py
```

### Database Management
```bash
# Check database status
python socializer/check_db.py

# Clear database
python socializer/clear_db.py
```

### Code Quality
```bash
# Run linter (Ruff)
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Type checking (MyPy)
mypy socializer/
```

## Coding Standards

### Language & Style
- **Language**: Python 3.11+
- **Type Hints**: Always use type hints for function parameters and return values
- **Formatting**: Follow PEP 8, enforced by Ruff (line length: 100)
- **Imports**: Use absolute imports, organize them (stdlib, third-party, local)

### Python Best Practices
```python
# ✅ GOOD: Type hints and clear naming
def upload_content(platform: str, media_path: Path) -> bool:
    """Upload media content to specified platform."""
    try:
        # Implementation
        return True
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return False

# ❌ BAD: No type hints, unclear naming
def upload(p, m):
    # Implementation
    return True
```

### Error Handling
- **Always** use try-catch blocks for:
  - API calls
  - File I/O operations
  - Playwright interactions
  - Database operations
- Log errors with context using the logging module
- Never use bare `except:` - always specify exception types

### Asynchronous Code
- Use `async/await` for Playwright operations
- Properly handle asyncio event loops
- Use `asyncio.gather()` for concurrent operations when appropriate

### Security
- **Never** commit credentials or API keys
- Use environment variables for sensitive data (`.env` file)
- Sanitize user inputs before database queries
- Use parameterized queries to prevent SQL injection
- Be cautious with `eval()` and `exec()` - avoid if possible

## Architektur & Struktur

### Project Layout
```
socializer/
├── socializer/              # Core automation package
│   ├── radar/              # AI agent radar module
│   ├── examples/           # Example scripts
│   ├── scripts/            # Utility scripts
│   └── pyproject.toml      # Package configuration
├── socializer-api/         # FastAPI backend
│   ├── socializer_api/     # API source code
│   │   ├── main.py        # FastAPI app entry point
│   │   ├── db.py          # Database operations
│   │   └── scheduler/     # Background job scheduler
│   └── pyproject.toml      # API package configuration
├── _bmad/                  # BMAD methodology framework
│   └── modules/            # BMAD agent modules
├── content/                # Generated content storage
├── scripts/                # Helper scripts
├── .env                    # Environment variables (not committed)
└── *.sqlite                # SQLite databases
```

### Key Components
- **Playwright Automation**: Use stealth mode and anti-detection measures
- **Session Management**: Persistent sessions stored in SQLite
- **API Backend**: FastAPI for RESTful endpoints
- **Content Scheduling**: Background scheduler for automated posts
- **BMAD Integration**: Methodology for agentic development

## Database

### Schema
- **Sessions**: Browser session persistence (cookies, state)
- **Content**: Scheduled posts and generated content
- **Logs**: Upload history and error tracking

### Best Practices
- Use SQLite for development/testing
- Consider PostgreSQL for production
- Always use context managers (`with`) for database connections
- Implement proper transaction handling

## Playwright Best Practices

### Stealth Mode
```python
# Always use stealth settings
from playwright_stealth import stealth_async

async with async_playwright() as p:
    browser = await p.chromium.launch(
        headless=False,
        args=['--disable-blink-features=AutomationControlled']
    )
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='...'  # Randomize user agent
    )
    page = await context.new_page()
    await stealth_async(page)
```

### Human-like Behavior
- Use random delays between actions: `await page.wait_for_timeout(random.randint(1000, 3000))`
- Implement Bezier curves for mouse movement
- Vary typing speed and add occasional typos
- Take screenshots for debugging: `await page.screenshot(path=f'debug_{timestamp}.png')`

### Error Handling
- Always wait for elements before interacting
- Use retry logic with exponential backoff
- Save debug screenshots on failures
- Check for pop-ups and cookie banners

## BMAD Methodology

This project uses BMAD (Brian's Methodology for Agentic Development):
- See `BMAD_QUICK_START.md` for getting started
- Agent definitions in `_bmad/modules/`
- Workflows for different development tasks
- Integration with Gemini CLI via `.gemini/commands/`

### Using BMAD with Claude
- Reference BMAD workflows in prompts when needed
- Use structured thinking for complex features
- Follow the agent roles (dev, pm, architect, etc.)

## Lessons Learned (Wichtig!)

### Common Mistakes to Avoid
1. **Never use `any` type** - Always specify proper types, even if it's `Union[str, int]`
2. **Don't skip session persistence** - Always save browser sessions to avoid re-authentication
3. **Avoid hardcoded delays** - Use `page.wait_for_selector()` instead of fixed `sleep()`
4. **Check for platform changes** - Instagram/TikTok selectors change frequently, verify before bulk operations
5. **Handle popups first** - Always check for cookie banners, login prompts before main actions
6. **Log everything important** - Debugging Playwright issues requires good logging
7. **Test with headless=False first** - Visual debugging saves time
8. **Respect rate limits** - Add random delays between bulk operations to avoid detection
9. **Validate file paths** - Always check if media files exist before upload attempts
10. **Use environment variables** - Never hardcode credentials, even in test files

### Platform-Specific Notes
- **Instagram**: Login state expires, implement session health checks
- **TikTok**: Upload flow varies by region, test thoroughly
- **Both**: Frequent UI changes require selector maintenance

## API Development

### FastAPI Guidelines
- Use Pydantic models for request/response validation
- Implement proper HTTP status codes
- Add request validation and error responses
- Use dependency injection for database connections
- Document endpoints with OpenAPI/Swagger (automatic with FastAPI)

### Example Endpoint
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class ContentRequest(BaseModel):
    platform: str
    media_path: str
    caption: str

@app.post("/upload")
async def upload_content(request: ContentRequest):
    """Upload content to social media platform."""
    if request.platform not in ["tiktok", "instagram"]:
        raise HTTPException(status_code=400, detail="Invalid platform")

    # Implementation
    return {"status": "success", "upload_id": "..."}
```

## Environment Variables

Required in `.env`:
```bash
# API Keys (never commit these!)
GEMINI_API_KEY=your_key_here

# Platform Credentials
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password
TIKTOK_USERNAME=your_username
TIKTOK_PASSWORD=your_password

# Configuration
API_PORT=8000
DEBUG=True
```

## Git Workflow

- **Main branch**: `master`
- Commit messages should be descriptive
- Don't commit:
  - `.env` files
  - `*.sqlite` databases
  - Session directories (`ig_session/`, `tiktok_session/`)
  - Debug screenshots
  - `__pycache__/` directories

## Documentation

- Update README.md when adding major features
- Document new API endpoints in code (FastAPI auto-generates docs)
- Keep AGENTS.md updated when modifying agent behavior
- Add examples for new automation workflows

## Performance Considerations

- Use async/await for I/O-bound operations
- Implement connection pooling for databases
- Cache frequently accessed data
- Monitor memory usage during long automation sessions
- Close browser contexts properly to avoid leaks

---

**Last Updated**: 2026-01-05
**Maintained by**: Claude Code with BMAD methodology
