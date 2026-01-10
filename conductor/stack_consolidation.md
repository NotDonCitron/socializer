# Stack Consolidation Plan

Goal: move to a single automation stack to reduce maintenance and drift.
Current state mixes Playwright (radar/) and Selenium/undetected-chromedriver (upload_instagram_stealth.py + requirements.txt).

## Recommendation
- Default to Playwright-only for all new automation.
- Treat Selenium scripts as legacy and gradually retire them.

## Current Mixed Stack Files
- Playwright: radar/browser.py, radar/instagram.py, radar/tiktok.py, tests/.
- Selenium/UC: upload_instagram_stealth.py, requirements.txt.

## Migration Steps
1. Mark `upload_instagram_stealth.py` as legacy in README or docs.
2. Port any missing features into Playwright flows.
3. Remove Selenium dependencies from default install once parity is reached.
4. Keep a separate optional dependency group if legacy support is still required.

## Risks
- Platform UI changes can break either stack; keep robust selectors and fallbacks.
- Feature parity must be validated via tests and manual runs.

## Validation
- Run `python -m pytest tests/ -v`.
- Run manual upload flows for TikTok and Instagram.
