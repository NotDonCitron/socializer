# Ongoing Project Workflow

## 1. Task Management
- **Centralize:** Use the project's task tracking system (via CLI `list_tasks`, `create_task`) as the source of truth.
- **Kanban:** Run `npx vibe-kanban` in a separate terminal to manage tasks visually.
  - *Note:* Do not use `VibeKanbanWebCompanion` inside the Astro app at this time, as it causes build failures (`ReferenceError: i is not defined`).

## 2. Development Cycle
- **Clean Dependencies:** We are currently running with standard, unpatched dependencies.
  - If weird build errors recur, try a clean reinstall: `rm -rf node_modules package-lock.json && npm install`.
- **Verification:**
  - **Frequent Builds:** Run `npm run build` often to ensure changes don't break the build pipeline.
  - **Type Checking:** Use `npx astro check` to validate types before committing.

## 3. Deployment
- **Target:** GitHub Pages (based on `astro.config.mjs`).
- **Process:** Ensure the `dist/` folder builds cleanly locally before pushing to the `main` branch.

## 4. Code Standards
- **Strict Mode:** Ensure all variables are properly declared (`let`, `const`, `var`).
- **Formatting:** Adhere to the existing project style (Prettier/ESLint if available).