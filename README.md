# Socializer - TikTok & Instagram Automation

A Python-based automation framework for TikTok and Instagram using Playwright with advanced anti-detection measures.

## Features

- 🎭 **Stealth Mode**: Anti-detection browser flags, randomized viewport/UA
- 🖱️ **Human-like Behavior**: Bezier mouse movement, variable typing delays
- 🔄 **Retry Logic**: Exponential backoff on failures
- 💾 **Session Management**: SQLite persistence, health checks
- 🎯 **Multi-Strategy Selectors**: Fallback chains for UI changes

## Installation

```bash
cd /home/kek/socializer/socializer
pip install -e .
playwright install chromium
```

## Quick Start

### TikTok Upload

```bash
cd /home/kek/socializer
source .venv/bin/activate
python socializer/examples/tiktok_interactive.py
```

### Instagram Upload

```bash
python socializer/examples/instagram_interactive.py
```

### Features

- 📌 Hashtag presets (select by number)
- ✏️ Custom captions
- 🔄 Step-by-step prompts
- 💾 Session persistence

## Project Structure

```
socializer/
├── radar/
│   ├── browser.py          # Browser manager with stealth
│   ├── tiktok.py            # TikTok automation
│   ├── instagram.py         # Instagram automation
│   ├── human_behavior.py    # Natural interaction patterns
│   ├── selectors.py         # Multi-strategy selectors
│   └── session_manager.py   # Session persistence
├── examples/
│   ├── tiktok_interactive.py  # Interactive upload
│   ├── tiktok_post.py         # Automated upload
│   └── instagram_post.py      # Instagram upload
└── tests/
    └── *.py                   # Unit tests
```

## First-Time Login

1. Run with `headless=False`
2. Log in manually (handle CAPTCHA)
3. Session saves to `tiktok_session/` folder
4. Future runs use saved session

## Running Tests

```bash
cd /home/kek/socializer/socializer
python -m pytest tests/ -v
```

## ⚠️ Disclaimer

This tool is for educational purposes. Automated posting may violate platform ToS. Use responsibly with test accounts.
