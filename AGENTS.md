# Repository Guidelines

## Project Structure & Module Organization
- `radar/`: core Python automation library (Playwright, selectors, sessions, pipeline, CLI).
- `examples/`: runnable scripts for TikTok/Instagram flows (interactive and automated).
- `tests/`: pytest suite (`test_*.py`) for browser, stealth, and upload behavior.
- `site/`: Astro marketing site (`site/src/pages/index.astro`).
- `conductor/`: product specs, workflow docs, and language style guides.
- `data/`: local SQLite artifacts (e.g., `data/radar.sqlite`); treat as generated.
- `stack.yaml`: radar feed configuration.

## Build, Test, and Development Commands
- `pip install -e .`: install the Python package in editable mode.
- `playwright install chromium`: install browser dependencies for automation.
- `radar --help`: verify CLI entry point from `radar.cli`.
- `python examples/tiktok_interactive.py`: run the interactive TikTok upload flow.
- `python examples/instagram_interactive.py`: run the interactive Instagram upload flow.
- `python -m pytest tests/ -v`: run tests (see pytest addopts in `pytest.ini`).
- `cd site && npm install && npm run dev`: run the Astro site locally.

## Coding Style & Naming Conventions
- Python uses 4-space indentation, `snake_case` for functions/variables, `PascalCase` for classes.
- Line length is 100 (see `pyproject.toml` Ruff config).
- Follow `conductor/code_styleguides/python.md` for docstrings/imports.
- For `site/`, use the TypeScript/JavaScript style guides in `conductor/code_styleguides/`.

## Testing Guidelines
- Framework: `pytest` with tests in `tests/` named `test_*.py`.
- `pytest.ini` adds `--slowmo 1000` and `--screenshot only-on-failure`; keep new tests scoped to the smallest reproducible flow.
- Add coverage when changing selectors or upload behavior; prefer fixtures for shared setup.

## Commit & Pull Request Guidelines
- Commits use a conventional style: `type(scope): summary` or `type: summary` (e.g., `feat(ig): ...`, `fix: ...`).
- PRs should include a short description, commands run (or “not run”), and screenshots for `site/` changes.
- Link related issues or `conductor/` track docs when applicable.

## Architecture Overview
- `radar/` exposes the CLI (`radar.cli`) and core automation modules (`browser`, `tiktok`, `instagram`, `selectors`, `session_manager`).
- The `radar/pipeline/` package organizes feed processing stages (normalize, score, dedupe, render, generate, weekly).
- `radar/sources/` contains source adapters that plug into the pipeline.

## Security & Configuration Tips
- Session artifacts (e.g., `tiktok_session/`, `ig_session/`) are local; do not commit them.
- Update `stack.yaml` when adding or changing radar sources.
