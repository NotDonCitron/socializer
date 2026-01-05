# Track 1: Stabilization & Content Expansion

## Objective
Clean up the legacy build-breaking components and begin expanding the site content with GitHub projects.

## Tasks
- [x] **Dependency Cleanup**: Uninstall `vibe-kanban-web-companion` to remove unused, problematic code.
- [x] **Verify Build**: Run a final `npm run build` to ensure the project is production-ready.
- [x] **Content: GitHub Projects**: Research and add content for "more github projects" (Added V-bernommenKanban).
- [x] **Optional: Kanban Integration**: Explore embedding the Kanban board via Iframe or REST API (Added `/kanban` page).
- [x] **Fix Dead Links**: Created dynamic routes (`src/pages/[...slug].astro`) to render content detail pages.

## Progress
- [x] Re-establish workflow in `WORKFLOW.md`.
- [x] Resolve `ReferenceError: i is not defined` by removing the companion from the main page.
- [x] **COMPLETED**: The track is fully finished.