# Socializer System Documentation

Welcome to the **Socializer** documentation. This project is a full-stack automation platform designed for managing high-volume social media posting (TikTok & Instagram) with advanced anti-detection and human-like behavior.

## 🏗️ System Architecture

The project is split into two main components:

### 1. Automation Backend (`/socializer`)
A Python-based core that uses **Playwright** to drive browser sessions.
- **Stealth Engine**: Bypasses bot detection using randomized fingerprints, Bezier curves for mouse movements, and human-like typing patterns.
- **Modular Drivers**: Dedicated modules for TikTok (`radar/tiktok.py`) and Instagram (`radar/instagram.py`).
- **Session Manager**: Persists browser cookies and state in SQLite and local directories to avoid repeated logins.

### 2. Admin Panel (`/Socializer-Admin`)
A modern web dashboard built with **React (Vite)** and **Express**.
- **Dashboard**: Real-time analytics and system health monitoring.
- **Account Groups (Silos)**: Group accounts by proxy, email, or niche to isolate footprints.
- **Jobs Pipeline**: Schedule and monitor automated tasks with a live browser stream and logs.
- **Content Studio**: Tools for gathering sources, generating scripts, and reviewing AI-rendered videos.

---

## 🚀 Getting Started

### Prerequisites
- Node.js (v18+)
- Python (3.12+)
- Playwright dependencies

### 1. Setup the Backend
```bash
cd socializer
# It is recommended to use the global venv in the root
source ../venv/bin/activate
pip install -e .
playwright install chromium
```

### 2. Setup the Admin Panel
```bash
cd Socializer-Admin
npm install
npm run dev
```
The dashboard will be available at `http://localhost:5000`.

---

## 💎 Key Features

### Account Groups (Silos)
Socializer introduces the concept of **Silos**. Instead of managing accounts individually, you group them.
- **Shared Proxies**: All accounts in a group use the same proxy, ensuring your "Tech Niche" accounts never mix IP footprints with your "Lifestyle" accounts.
- **Resource Management**: Share recovery emails and topics across a cluster of accounts.

### Jobs & Live Pipeline
- **Real-time Monitoring**: Watch the automation happen live through the dashboard's screenshot stream.
- **Execution Logs**: Detailed, color-coded logs streamed via WebSockets from the Python worker.
- **Retry Logic**: Failed jobs can be analyzed and retried with a single click.

### Content Review
- **Video Artifacts**: Review AI-generated content before it goes live.
- **Suitability Scoring**: Automatically assess which platform (TikTok vs Instagram) a video is best suited for.

---

---

## 📡 Communication Protocol

The Admin Panel (`server/routes.ts`) and the Python Backend communicate through standard I/O and WebSockets.

### 1. Logs & Screenshots
The Python scripts output information to `stdout`. The Admin Panel parses these lines:
- **Screenshots**: Any line starting with `[SCREENSHOT] <base64_data>` is captured and broadcasted to the frontend as a live image.
- **System Logs**: Regular lines are prefixed with `[Python]` and stored as log entries.
- **Errors**: `stderr` is captured, prefixed with `[Python Error]`, and flagged as an error level in the database.

### 2. Process Control
- **Starting**: The Admin Panel uses `child_process.spawn` to run `dashboard_runner.py` with specific arguments (`--job-id`, `--content`, `--platform`, etc.).
- **Exit Codes**: 
  - `Code 0`: Job marked as `published`.
  - `Non-zero`: Job marked as `failed`.

---

## 🏗️ Development & Extension

### Adding new Automation Scripts
Automation logic lives in `socializer/radar/`. To add a new platform:
1. Create a new class in `socializer/radar/[platform].py`.
2. Inherit from `BaseAutomator` (if available) or use the `BrowserManager`.
3. Register the new script in `Socializer-Admin/server/routes.ts` within the `runPythonScript` helper.

### Database Schema
The system uses **Drizzle ORM** with a SQLite/PostgreSQL backend.
- Schema definition: `Socializer-Admin/shared/schema.ts`
- To update the DB: `cd Socializer-Admin && npm run db:push`

---

## 🧪 Testing the Radar CLI

### CLI Wrapper Pattern

The Radar CLI module (`radar/cli.py`) implements lightweight wrapper functions (lines 14-66) around core functionality. This design enables flexible testing by allowing tests to patch either:
- The wrapper: `@patch("radar.cli.fetch_releases")`
- The underlying module: `@patch("radar.sources.github.fetch_releases")`

### Why Use Wrappers?

The wrapper pattern provides two key benefits:
1. **Test Flexibility**: Tests can patch at the CLI layer for integration testing or at the module layer for unit testing
2. **Interface Stability**: CLI command logic can be tested independently of underlying implementations

### Testing CLI Commands

When testing CLI commands, patch the wrappers to isolate CLI logic:

```python
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from radar.cli import app

@patch("radar.cli.load_stack_config")
@patch("radar.cli.connect")
def test_run_command(mock_connect, mock_load_config):
    # Configure mocks
    mock_config = MagicMock()
    mock_config.sources = []
    mock_load_config.return_value = mock_config
    mock_connect.return_value = MagicMock()

    # Test CLI behavior
    runner = CliRunner()
    result = runner.invoke(app, ["run"])

    # Verify calls
    assert result.exit_code == 0
    mock_load_config.assert_called_once()
```

### Testing Async Wrappers

For async wrappers, use `AsyncMock` or let `@patch` handle it automatically:

```python
@pytest.mark.asyncio
async def test_async_wrapper():
    from radar import cli
    from radar.sources import github

    with patch.object(github, 'fetch_releases', new=AsyncMock()) as mock_fetch:
        mock_fetch.return_value = ["result"]

        # Test async wrapper
        result = await cli.fetch_releases(MagicMock(), token="test")
        assert result == ["result"]
```

### Running Tests

```bash
# Run full test suite
python -m pytest -v

# Run CLI tests only
python -m pytest tests/test_cli.py -v

# Run with coverage
python -m pytest --cov=radar --cov-report=html
```

### Test Organization

Tests are organized into focused files:
- `tests/test_cli.py` - CLI wrapper tests, command tests, and integration tests
- `tests/test_pipeline_*.py` - Pipeline stage tests (score, generate, render)
- `tests/test_sources.py` - Data source tests (GitHub, webpage)
- `tests/test_storage.py` - Database persistence tests
- `tests/test_llm.py` - LLM provider tests

---

## ⚠️ Troubleshooting

### ModuleNotFoundError: No module named 'playwright'
Ensure the Admin panel is pointing to the correct Python executable. The system is currently configured to use the `venv` in the root:
`const venvPython = path.join(projectRoot, "venv", "bin", "python3");` (See `Socializer-Admin/server/routes.ts`)

### Browser crashes in Flatpak/Container
If running in a container, Playwright might struggle with GPU acceleration or Wayland. Run the app natively or use `headless: true`.

---
*Last updated: January 2026*
