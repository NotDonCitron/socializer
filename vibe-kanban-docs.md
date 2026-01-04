# Vibe Kanban Integration Guide für dein Astro-Projekt

## TL;DR - Die schnelle Lösung

```bash
# Terminal 1: Starte Vibe Kanban (läuft auf http://localhost:3000)
npx vibe-kanban

# Terminal 2: Dein Astro-Projekt (läuft auf http://localhost:3000 oder anderem Port)
npm run dev
```

Fertig! Vibe Kanban läuft **komplett isoliert** von deinem Astro-Build.

---

## Setup 1: Standalone Vibe Kanban (EMPFOHLEN)

### Installation & Start

```bash
# Einmalig: npx cacht es, danach super schnell
npx vibe-kanban

# Die App öffnet sich automatisch im Browser
# Standard: http://localhost:3000
```

### Konfiguration (Environment Variables)

Wenn du custom Ports brauchst, setze vor `npx vibe-kanban`:

```bash
# Custom Ports setzen
export BACKEND_PORT=5000      # Backend läuft hier
export FRONTEND_PORT=3001     # Frontend öffnet auf Port 3001
export HOST=127.0.0.1         # Oder 0.0.0.0 für Remote-Zugriff

npx vibe-kanban
```

Auf **Windows** (PowerShell):

```powershell
$env:BACKEND_PORT="5000"
$env:FRONTEND_PORT="3001"
npx vibe-kanban
```

### Git Worktrees & AI-Agenten Integration

Das ist die **Kernfunktion** von Vibe Kanban:

1. **Projekt hinzufügen:**
   - "Add Project" → Wähle ein git repository
   - Z.B. dein `socializersocializersite` Projekt

2. **Task erstellen:**
   - "Create Task" → Title + Description eingeben
   - Z.B.: "Fix i is not defined build error"

3. **AI-Agent ausführen:**
   - Wähle Agent: Claude Code, Amp, Gemini, Cursor Agent
   - Jede Ausführung läuft in **isoliertem git worktree** (sichere Sandboxing!)
   - Keine Verschmutzung deines main branch

4. **Code-Review & Merge:**
   - Sehe alle Changes als Diff
   - Merge zurück zu main wenn OK
   - Oder gebe Follow-up Instructions für Iteration

### Konfiguration für deine Agents

Vibe Kanban liest deine **bestehenden MCP-Configs**:

```bash
# Beispiel: Claude Code Config
~/.config/claude-code/claude_desktop_config.json

# Oder Cursor Agent Config
~/.cursor/mcp.json

# Oder Gemini Config
~/.config/gemini-cli/config.json
```

Vibe Kanban integriert sich automatisch!

---

## Setup 2: Hybrid Integration (Astro + Vibe Kanban)

### Wenn du Vibe Kanban im Astro-Projekt embedden möchtest

**Option A: Iframe-Link** (einfach, sauber)

```astro
---
// src/pages/kanban.astro
const vibeKanbanUrl = import.meta.env.DEV 
  ? "http://localhost:3000"
  : "https://kanban.yourdom.com"
---

<html>
  <head>
    <title>Task Management</title>
  </head>
  <body>
    <h1>Vibe Kanban Manager</h1>
    
    <!-- Externe App öffnen -->
    <a href={vibeKanbanUrl} target="_blank" class="btn-large">
      Open Vibe Kanban in New Tab →
    </a>

    <!-- ODER Embedded Iframe (nur wenn Same-Origin oder CORS gelöst) -->
    <iframe 
      src={vibeKanbanUrl}
      style="width: 100%; height: 100vh; border: none;"
      title="Vibe Kanban"
    />
  </body>
</html>
```

**Option B: Proxy über Astro API Routes** (fortgeschritten)

```astro
---
// src/pages/api/kanban/[...path].ts
import type { APIRoute } from 'astro';

export const GET: APIRoute = async ({ params }) => {
  const path = params.path || '';
  const response = await fetch(`http://localhost:3000/api/${path}`);
  
  return new Response(response.body, {
    status: response.status,
    headers: {
      'Content-Type': response.headers.get('content-type') || 'application/json',
      'Access-Control-Allow-Origin': '*',
    }
  });
}
```

**Option C: REST API Integration** (für Custom Dashboard)

```typescript
// src/lib/vibe-kanban-client.ts
export async function getKanbanTasks() {
  const response = await fetch('http://localhost:3000/api/tasks');
  return response.json();
}

export async function getKanbanProjects() {
  const response = await fetch('http://localhost:3000/api/projects');
  return response.json();
}

export async function updateTaskStatus(taskId: string, status: string) {
  const response = await fetch(`http://localhost:3000/api/tasks/${taskId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status })
  });
  return response.json();
}
```

Danach in deinem Astro-Component:

```astro
---
import { getKanbanTasks } from '../lib/vibe-kanban-client';

const tasks = await getKanbanTasks();
---

<ul>
  {tasks.map(task => (
    <li>
      <strong>{task.title}</strong> - {task.status}
    </li>
  ))}
</ul>
```

---

## Multi-Terminal Setup für Entwicklung

Das ist mein **empfohlenes Workflow-Setup** für dich:

### Terminal 1: Vibe Kanban

```bash
cd ~/projects/any-git-repo  # Oder einfach irgendwo

# Custom Ports um Konflikt zu vermeiden
FRONTEND_PORT=3001 npx vibe-kanban
```

Browser öffnet: `http://localhost:3001`

### Terminal 2: Dein Astro-Dev-Server

```bash
cd ~/kek/socializer/socializersite

npm run dev
# Läuft auf http://localhost:3000 (oder Astro-Default)
```

Browser öffnet: `http://localhost:3000`

### Terminal 3: Optional - AI-Agent CLI

```bash
# Wenn du Claude Code CLI nutzen möchtest
claude-code --project ~/kek/socializer/socializersite

# Oder Cursor Agent
cursor-agent start
```

So hast du **parallele Workflows:**

- Vibe Kanban orchestriert Task für dein `socializersocializersite`
- Du siehst die Website live in Terminal 2
- Claude/Amp startet Agents auf dein Repo via Vibe Kanban
- Alles läuft **isoliert** mit git worktrees

---

## Environment Variables Summary

| Variable | Default | Use Case |
|----------|---------|----------|
| `FRONTEND_PORT` | `3000` | Webseite-Port |
| `BACKEND_PORT` | `0` (auto) | API-Port (merk dir welcher!) |
| `HOST` | `127.0.0.1` | `0.0.0.0` für Remote-Zugriff |
| `GITHUB_CLIENT_ID` | Bloop AI Default | Nur wenn Self-Hosted |
| `POSTHOG_API_KEY` | (empty) | Analytics (optional) |

**Beispiel für dich:**

```bash
export FRONTEND_PORT=3001
export BACKEND_PORT=3002
export HOST=127.0.0.1

npx vibe-kanban
# Frontend: http://localhost:3001
# Backend API: http://localhost:3002
```

---

## API Endpoints (wenn du REST integration brauchst)

Vibe Kanban exponiert folgende Endpoints:

```bash
# Projekte
GET   http://localhost:3000/api/projects
POST  http://localhost:3000/api/projects
GET   http://localhost:3000/api/projects/:id
PATCH http://localhost:3000/api/projects/:id

# Tasks
GET   http://localhost:3000/api/tasks
POST  http://localhost:3000/api/tasks
GET   http://localhost:3000/api/tasks/:id
PATCH http://localhost:3000/api/tasks/:id

# Task-Attempts (AI-Agenten Ausführungen)
GET   http://localhost:3000/api/tasks/:taskId/attempts
POST  http://localhost:3000/api/tasks/:taskId/attempts

# Diffs (Git Changes)
GET   http://localhost:3000/api/tasks/:taskId/attempts/:attemptId/diff
```

---

## Workflow für dein socializer-site Projekt

### Scenario 1: Fix den Build Error mit Vibe Kanban

```
1. Terminal 1: npx vibe-kanban
2. Terminal 2: npm run dev (dein Astro-Dev-Server)
3. Im Vibe Kanban UI:
   - Add Project: /home/kek/socializer/socializersite
   - Create Task: "Remove vibe-kanban-web-companion and fix build"
   - Description: "Delete import of vibe-kanban-web-companion from src/pages/index.astro"
   - Execute with Claude Code
   - Claude macht die Änderung in isoliertem Worktree
   - Review diff
   - Merge back to main
4. Terminal 2: npm run build → SOLLTE JETZT PASSEN! ✅
```

### Scenario 2: Vibe Kanban für Feature-Development

```
Task: "Add dark mode toggle to portfolio"

1. Vibe Kanban erstellt isoliertes Worktree
2. Claude Code entwickelt Feature
3. Du reviewst Changes im UI
4. Merge successful → main branch hat Feature
5. Dein Astro dev-server hot-reloaded
```

---

## Troubleshooting

### Problem: "Port 3000 already in use"

```bash
# Nutze andere Ports:
FRONTEND_PORT=3001 BACKEND_PORT=3002 npx vibe-kanban
```

### Problem: "Git worktree creation failed"

```bash
# Stelle sicher, dass git im Repo initialisiert ist:
cd ~/kek/socializer/socializersite
git status  # Sollte funktionieren

# Cleanup alte Worktrees:
git worktree list
git worktree prune
```

### Problem: "Claude Code nicht erkannt"

```bash
# Stelle sicher Claude Code installiert ist:
which claude-code

# Oder Cursor Agent:
which cursor-agent

# Falls nicht, install via:
npm install -g @anthropic-ai/claude-code
```

### Problem: Vibe Kanban speichert Daten nicht

```bash
# Vibe Kanban nutzt lokale SQLite DB:
~/.vibe-kanban/db.sqlite

# Du kannst manuell löschen, wenn was kaputt ist:
rm ~/.vibe-kanban/db.sqlite
# Beim nächsten Start wird neue DB erstellt
```

---

## Recommendations für dein Setup

Basierend auf deinem Tech-Stack (Python-Dev, Black Desert Online Automation, Linux + CachyOS):

✅ **DO:**

- Nutze `npx vibe-kanban` als separate App (wie ne VSCode-Instanz)
- Lass dein `socializersocializersite` Astro-Projekt clean
- Verwende Vibe Kanban zur **AI-Agent Orchestration**, nicht als Web-Component
- 3-Terminal-Setup: Vibe Kanban + Astro Dev + optional AI-CLI

❌ **DON'T:**

- Versuche nicht, `vibe-kanban-web-companion` in Astro zu integrieren (das ist das Problem!)
- Patch-iere nicht tiefer in `node_modules` (fontkit, htm, babel)
- Nutze nicht `--force` bei npm install, außer wenn wirklich nötig

---

## Nächste Schritte

1. **Sofort:** Entferne `vibe-kanban-web-companion` aus `src/pages/index.astro`

   ```bash
   cd ~/kek/socializer/socializersite
   npm uninstall vibe-kanban-web-companion
   npm run build  # Sollte jetzt passen
   ```

2. **Danach:** Installiere vibe-kanban standalone

   ```bash
   npx vibe-kanban  # Probier's aus!
   ```

3. **Optional:** Integriere über Iframe oder REST API in dein Astro-Projekt

   ```
   (Siehe "Setup 2: Hybrid Integration" oben)
   ```

Alles klar? Brauchst du noch Details zu irgendeinem Setup?
