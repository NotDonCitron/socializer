# Contributing to Socializer

Thanks for helping make Socializer more polished. This document covers the workflow we expect contributors to follow.

## Getting started

1. Create a Python 3.11+ virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # use `.venv\Scripts\activate` on Windows
   ```
2. Install the local packages in editable mode:
   ```bash
   pip install -e socializer/ -e socializer-api/
   pip install -r requirements.txt
   ```
3. Install Playwright browsers for automation:
   ```bash
   playwright install chromium
   ```
4. Optionally, install session helpers:
   ```bash
   pip install undetected-chromedriver selenium
   ```
5. Activate the pre-commit hooks so formatting and linting run before commits:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Coding conventions

- Follow the formatting enforced by `black --line-length=100` and `isort` with the `black` profile.
- Use `snake_case` for functions/variables and `PascalCase` for classes.
- Keep imports grouped as: standard library, third-party, local.
- Document modules and functions using docstrings that explain the "why" of the logic.
- Avoid committing generated artifacts (see `.gitignore`).

## Testing

- Run targeted tests with `python -m pytest tests/ -v`.
- Add markers for slow or browser-dependent flows so the suite remains stable.
- Include fixtures for shared setup to reduce duplication.
- When modifying selectors or upload behavior, add a regression test covering the new flow.
- For CI coverage, run `pytest --cov`.

## Workflow

1. Branch from `master`.
2. Work in small, self-contained commits (`type(scope): summary`).
3. Run `pre-commit run --all-files` before pushing.
4. Push to your fork and open a PR targeting `master`.
5. Link related issues or `conductor/` docs if relevant.
6. Update this file if you add new development prerequisites.

## Support

If you are unsure about where to start, gather more context in `PROJECT_STATUS.md` or ask in the issue tracker for guidance before submitting work.
