# Track 4: Social Hub & Analytics

## Objective
Transition from a static content viewer to a dynamic "Social Hub" where AI-refined drafts can be published to a live feed, and project activity is visualized.

## Progress
- [x] Track initialized and completed.
- [x] Database & API (Backend): Updated PostDB, added stats endpoint, created default user.
- [x] Copilot "Publish" Action: Added `publishPost` to CopilotWrapper.
- [x] Live Feed (Frontend): Created LiveFeed component and integrated into index.
- [x] Impact Analytics: Installed recharts and built ImpactChart component.

## Tasks
- [x] **Database & API (Backend)**:
    - [x] Update `models.py` (if needed) to support "Published Posts" with metadata (source repo, impact score).
    - [x] Create `POST /api/posts/promote`: Endpoint to convert a draft (text) into a published post (Integrated in main POST /api/posts).
    - [x] Create `GET /api/stats/impact`: Endpoint to aggregate activity/mentions per project.
- [x] **Copilot "Publish" Action**:
    - [x] Add `publishPost` action to `CopilotWrapper`.
    - [x] Allow the AI to take a finalized draft and "send it to the live feed".
- [x] **Live Feed (Frontend)**:
    - [x] Create `src/components/LiveFeed.tsx` to fetch and display posts from the backend.
    - [x] Integrate `LiveFeed` into `src/pages/index.astro` (alongside static updates).
- [x] **Impact Analytics**:
    - [x] Install `recharts` (or similar lightweight chart lib).
    - [x] Build `src/components/ImpactChart.tsx` to visualize the "AI Impact" data.

