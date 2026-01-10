# Open Source Landscape for Socializer

This note tracks open-source projects that can inform or extend Socializer.
It focuses on stealth automation, schedulers, and social media tooling.

## Stealth and Fingerprinting (Playwright)
- patchright (Playwright patches): https://github.com/Kaliiiiiiiiii-Vinyzu/patchright
- patchright-python (Python wrapper): https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python
- rebrowser-patches (Chromium/Playwright patches): https://github.com/rebrowser/rebrowser-patches
- Botright (stealth patterns + fingerprints): https://github.com/Vinyzu/Botright
- playwright-with-fingerprints (fingerprint injection): https://github.com/bablosoft/playwright-with-fingerprints

## Social Media Scheduling and Management
- Postiz (full scheduler, Buffer-like): https://github.com/gitroomhq/postiz-app
- Mixpost (scheduler and team workflows): https://github.com/inovector/mixpost
- Social Media Agent (LLM pipeline reference): https://github.com/langchain-ai/social-media-agent

## TikTok and Instagram Automation References
- TikTok Studio Uploader: https://github.com/wanghaisheng/tiktoka-studio-uploader
- InstaPy (Instagram automation): https://github.com/InstaPy/InstaPy
- GramAddict (Instagram automation framework): https://github.com/GramAddict/bot

## Potential Fit in Socializer
- Stealth patches: consider for `radar/browser.py` and Playwright contexts.
- Scheduler patterns: reference for a queue in `socializer-api/` or `admin-panel-temp/`.
- LLM agent flows: map to `radar/pipeline/` and `radar/llm/`.

## Notes
- Evaluate licenses before adoption.
- Prefer integration via optional modules to keep the core lightweight.
