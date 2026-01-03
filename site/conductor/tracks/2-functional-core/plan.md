# Track 2: Functional Core & Automation

## Objective
Build the functional backbone for content aggregation and public transparency, utilizing the Vibe Kanban API and establishing a smart AI strategy for content generation.

## Tasks
- [x] **Public Roadmap Integration**:
    - [x] Create a TypeScript client (`src/lib/vibe.ts`) to fetch tasks from the local Vibe Kanban API.
    - [x] Build a server-side rendered `roadmap` page that lists tasks by status (Todo/In Progress/Done).
- [x] **AI Strategy Deep Research**:
    - [x] Analyze `CopilotKit` vs. custom LLM scripts (Result: Serverless Webhooks + Human-in-the-Loop).
    - [x] Define the "Smartest Approach" architecture (GitHub Webhook -> API -> Vibe Kanban -> Copilot Refine).
- [x] **News Aggregator Prototype**:
    - [x] Create a script/loader (`src/lib/automation.ts`) to fetch releases from GitHub.
    - [x] Create an API endpoint (`/api/scan`) to trigger the scan.
    - [x] Add a UI button on the Roadmap page to run the scan.
    - [x] **Added `fastapi`** to the tracked repositories.

## Progress
- [x] Track initialized.
- [x] Roadmap feature implemented.
- [x] Automation prototype built and verified via code review (runtime requires manual start of `vibe-kanban`).
