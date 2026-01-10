# Socializer

Socializer is a full-stack automation platform for managing Instagram and TikTok content workflows with a Python automation core, a web admin panel, and a lightweight API layer.

## Structure
- `radar/`: Python automation core (Playwright, selectors, sessions, CLI).
- `examples/`: runnable scripts for Instagram/TikTok flows.
- `admin-panel/`: React + Express admin panel.
- `socializer-api/`: FastAPI service for scheduling utilities.
- `conductor/`: specs and style guides.

## Quick start
### Python automation
```bash
pip install -e .
playwright install chromium
```

### Admin panel
```bash
cd admin-panel
npm install
npm run dev
```
The dashboard runs on `http://localhost:5501`.

### Windows PowerShell dev server
```powershell
cd admin-panel
$env:NODE_ENV="development"
npx tsx server/index.ts
```

## Instagram engagement (UI)
The admin panel includes an Instagram Engagement page that triggers a prefix-filtered follow/like/comment flow. Configure:
- Search query
- Username prefixes (comma-separated)
- Action toggles and hourly limits

See `examples/instagram_engage_prefixes.py` for the CLI runner.
