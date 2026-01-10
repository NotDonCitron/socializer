# Gemini CLI Execution Plan

This plan is a structured sequence for using Gemini CLI to implement the agreed improvements.
Each step includes a suggested prompt and a concrete output to expect.

## Phase 1: Repo Hygiene and Documentation

Goals:
- Align documentation with the actual folder layout.
- Remove non-ASCII garbled text from docs and configs.
- Ignore local session artifacts and temp clones.

Suggested Gemini prompt:
"Audit and fix repo hygiene: update DOCUMENTATION.md and admin-panel-temp/README.md to match current folder names, clean garbled characters to ASCII, and update .gitignore to include ig_session/, ig_session_data/, test_ud_dir/, debug_shots/, and temp_* panel clones. Keep edits minimal and consistent with existing docs."

Expected changes:
- DOCUMENTATION.md
- admin-panel-temp/README.md
- .gitignore
- (optional) AGENTS.md for ASCII quotes

## Phase 2: Automation Stability and Logging

Goals:
- Use shared configuration for Instagram debugging and timeouts.
- Remove garbled print characters in config/session utilities.
- Standardize debug artifacts under a single directory.

Suggested Gemini prompt:
"Refactor radar/instagram.py to use IG_DEBUG_DIR, IG_DEBUG_SCREENSHOTS, IG_LOGIN_TIMEOUT, and IG_UPLOAD_TIMEOUT from radar/ig_config.py. Replace hard-coded debug_shots references. Also replace garbled characters in radar/ig_config.py and radar/session_manager.py with ASCII text."

Expected changes:
- radar/instagram.py
- radar/ig_config.py
- radar/session_manager.py

## Phase 3: Architecture and Workflow Plan

Goals:
- Add a lightweight architecture plan that separates API, worker, and panel.
- Define a job queue path (APScheduler for local or RQ/Celery for scale).

Suggested Gemini prompt:
"Create a short architecture plan in conductor/architecture_plan.md describing how to separate admin-panel-temp, socializer-api, and radar worker processes, and propose a job queue (APScheduler for local, RQ/Celery for scale). Keep it concise and actionable."

Expected changes:
- conductor/architecture_plan.md

## Phase 4: Open-Source Landscape and Mapping

Goals:
- Document candidate OSS projects and where they fit.

Suggested Gemini prompt:
"Create conductor/open_source.md listing relevant open-source projects (patchright, rebrowser-patches, Botright, Postiz, Mixpost, InstaPy, GramAddict) and map each to a Socializer module or feature."

Expected changes:
- conductor/open_source.md

## Phase 5: Stack Consolidation Decision

Goals:
- Decide on Playwright-only vs Selenium-only and document migration steps.

Suggested Gemini prompt:
"Draft a short migration note in conductor/stack_consolidation.md that recommends a single automation stack (Playwright-only by default), lists current mixed stack files, and outlines a staged migration plan."

Expected changes:
- conductor/stack_consolidation.md

## Suggested Commands
- Run Python tests: `python -m pytest tests/ -v`
- (Optional) Panel tests/build: `cd admin-panel-temp && npm run check`

## Notes
- Keep all text ASCII.
- Prefer minimal, well-scoped edits.
- Avoid touching generated directories or session data.
