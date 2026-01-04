# Socializer

A Python-based automation framework for TikTok and Instagram using Playwright with advanced anti-detection measures.

## Project Structure

- `socializer/`: Core source code and package.
- `scripts/`: Helper scripts for maintenance and execution.
- `socializer-api/`: API components.
- `vibe-kanban-docs.md`: Documentation for Vibe Kanban integration.

## Installation

```bash
# Activate virtual environment
source .venv/bin/activate

# Install the package
pip install -e socializer/

# Install Playwright browsers
playwright install chromium
```

## Quick Start

### Interactive Uploads

```bash
# TikTok
python socializer/examples/tiktok_interactive.py

# Instagram
python socializer/examples/instagram_interactive.py
```

## Documentation

For more detailed information about the inner workings, see [socializer/README.md](socializer/README.md) and [socializer/AGENTS.md](socializer/AGENTS.md).

## Features

- 🎭 **Stealth Mode**: Anti-detection browser flags, randomized viewport/UA
- 🖱️ **Human-like Behavior**: Bezier mouse movement, variable typing delays
- 🔄 **Retry Logic**: Exponential backoff on failures
- 💾 **Session Management**: SQLite persistence, health checks

## License

[License Information]
