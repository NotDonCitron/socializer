# Track 3: AI Content Engine

## Objective
Transform raw GitHub data into ready-to-publish social media content using LLMs and provide an interactive UI for refining these drafts.

## Progress
- [x] LLM Integration (Backend) completed: AI logic moved to Python FastAPI backend.
- [x] Configurable Sources completed: Repositories moved to `sources.json`.
- [x] Interactive Refinement (CopilotKit) completed: Added updateTask action and readable state to Copilot.

## Tasks
- [x] **LLM Integration (Backend)**:
    - [x] Add `openai` or `anthropic` SDK.
    - [x] Create a `summarizeRelease` function to generate a TL;DR and a Social Media Hook.
    - [x] Update the automation logic to include these AI-generated drafts in the Vibe Kanban task description.
- [x] **Interactive Refinement (CopilotKit)**:
    - [x] Install `@copilotkit/react-core` and `@copilotkit/react-ui`.
    - [x] Build a "Refinement UI" where you can chat with the content to tweak the generated posts.
- [x] **Configurable Sources**:
    - [x] Move the repository list from `scan.ts` to a dedicated `src/config/sources.json`.
    - [x] Add a few more high-impact AI repos (e.g., `openai/openai-python`, `anthropics/anthropic-sdk-python`).
