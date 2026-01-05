# PC-Workflow für Socializer

## 📊 Status nach Synchronisierung (2026-01-05)

✅ **Repository erfolgreich synchronisiert!**
- GitHub: https://github.com/NotDonCitron/socializer
- Branch: `master` (Haupt-Branch)
- Laptop-Branch `jules-1826452161482480206-14dec86f` wurde in `master` gemerged

## 🔐 WICHTIG: Sicherheitswarnung

**KRITISCH**: Die folgenden API-Keys wurden aus der Git-Historie entfernt, sind aber bereits kompromittiert und MÜSSEN widerrufen werden:

1. **GitHub Personal Access Token**: `github_pat_11BTXHGAI0wmSCQpwYZ5X4_...`
   - Widerrufen unter: https://github.com/settings/tokens

2. **OpenAI API Key**: `sk-proj-nUIblaxLfAlF3ZlD-VxhiTIZBgy_...`
   - Widerrufen unter: https://platform.openai.com/api-keys

**Bitte SOFORT neue Keys erstellen und in `.env` speichern (wird durch `.gitignore` ignoriert)!**

## 🚀 Täglicher Workflow

### Erste Einrichtung auf neuem PC

```bash
# Repository klonen
git clone https://github.com/NotDonCitron/socializer.git
cd socializer

# Virtual Environment aktivieren
source .venv/bin/activate

# Dependencies installieren
pip install -e socializer/
pip install -e socializer-api/
playwright install chromium

# .env Datei erstellen (nie committen!)
cp .env.example .env
# .env mit deinen API-Keys bearbeiten
```

### Tägliche Nutzung

```bash
cd ~/socializer

# Aktiviere Virtual Environment
source .venv/bin/activate

# Starte API Server (optional)
uvicorn socializer_api.main:app --reload --port 8002

# Instagram Upload (Stealth Mode)
./run_upload.sh stealth "/pfad/zu/bild.jpg"

# Instagram Upload (Playwright Mode)
python socializer/examples/instagram_interactive.py

# TikTok Upload
python socializer/examples/tiktok_interactive.py
```

### Bei Änderungen

```bash
# Hole neueste Änderungen vom GitHub
git pull

# Deine Änderungen machen
# ... Code bearbeiten ...

# Änderungen committen
git add .
git commit -m "Beschreibung der Änderungen

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Zu GitHub pushen
git push
```

## 📁 Projekt-Struktur

```
socializer/
├── socializer/              # Core Automation Package
│   ├── radar/              # AI Agent Radar Module
│   ├── examples/           # Beispiel-Scripts
│   └── pyproject.toml
├── socializer-api/         # FastAPI Backend
│   ├── socializer_api/     # API Source Code
│   └── pyproject.toml
├── _bmad/                  # BMAD Methodology
├── content/                # Generierter Content (ignoriert)
├── scripts/                # Helper Scripts
├── .env                    # Environment Variables (NICHT committen!)
├── .gitignore              # Git Ignore Regeln
└── README.md               # Hauptdokumentation
```

## 🔧 Wichtige Befehle

### API Management
```bash
# API starten
uvicorn socializer_api.main:app --reload --port 8002

# API Status prüfen
curl http://127.0.0.1:8002/health
```

### Datenbank
```bash
# Datenbank-Status prüfen
python socializer/check_db.py

# Datenbank leeren (Vorsicht!)
python socializer/clear_db.py
```

### Testing
```bash
# Tests ausführen
pytest

# Tests mit Details
pytest -v
```

## 🌐 GitHub Workflow

### Branches
- `master`: Haupt-Branch (PC + Laptop kombiniert)
- `jules-1826452161482480206-14dec86f`: Alter Laptop-Branch (gemerged in master)

### Pull Requests
Pull Requests erstellen über: https://github.com/NotDonCitron/socializer/pulls

## 🛡️ Sicherheits-Best-Practices

1. **Niemals Credentials committen**
   - Alle Secrets in `.env` speichern
   - `.env` ist in `.gitignore` ausgeschlossen

2. **Session-Daten schützen**
   - `ig_session/` und `tiktok_session/` sind ignoriert
   - Niemals Session-Cookies public machen

3. **API-Keys rotieren**
   - Regelmäßig neue Keys erstellen
   - Alte Keys widerrufen

4. **Niemals force-push zu main**
   - Außer bei Sicherheitsproblemen (wie heute)

## 📝 Wichtige Dateien

- **CLAUDE.md**: Projekt-Guidelines für Claude Code
- **README.md**: Haupt-Dokumentation
- **BMAD_QUICK_START.md**: BMAD Methodology Guide
- **.gitignore**: Definiert ignorierte Dateien

## 🔗 Nützliche Links

- GitHub Repo: https://github.com/NotDonCitron/socializer
- FastAPI Docs: http://127.0.0.1:8002/docs (wenn API läuft)
- OpenAPI Schema: http://127.0.0.1:8002/openapi.json

## 💡 Tipps

1. **Immer Virtual Environment aktivieren** bevor du arbeitest
2. **Git pull vor dem Arbeiten** um Konflikte zu vermeiden
3. **Regelmäßig committen** mit klaren Beschreibungen
4. **Browser headless=False beim Debuggen** für visuelle Kontrolle
5. **Screenshots bei Fehlern** automatisch in `debug_shots/`

---

**Letztes Update**: 2026-01-05
**Status**: ✅ Vollständig synchronisiert
