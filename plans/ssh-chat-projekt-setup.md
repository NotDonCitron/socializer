# SSH-Chat Projekt Setup - Wichtige Anforderungen

## Kritische Anforderungen

### 1. Code-mode MCP muss auf BEIDEN Laptops funktionieren
- Beide Laptops müssen MCP-Server ausführen können
- Gleiche MCP-Tools und Konfiguration
- Test: `radar --help` muss auf beiden funktionieren

### 2. Beide Laptops müssen gleichen Repo-Stand haben
```bash
# Laptop A (dein PC)
git add .
git commit -m "snapshot: chat-project-v1"
git push origin main

# Laptop B (Freund)
git pull origin main
```

### 3. Projekt muss auf beiden Laptops lauffähig sein
```bash
# Beide Laptops müssen das ausführen können:
pip install -e .
radar --help
python -m pytest tests/ -v
```

---

## Setup für beide Laptops

### Schritt 1: Repo klonen
```bash
cd ~/projects
git clone https://github.com/NotDonCitron/socializer.git
cd socializer
```

### Schritt 2: Dependencies installieren
```bash
pip install -e .
playwright install chromium
radar --help  # Testen
```

### Schritt 3: MCP konfigurieren
```bash
# Prüfen ob MCP funktioniert
echo "MCP Server testen..."
python -c "from mcp.server import Server; print('MCP OK')"
```

### Schritt 4: SSH einrichten (wie zuvor beschrieben)

---

## Sync-Strategie

### Immer vor dem Arbeiten:
```bash
git pull origin main
```

### Nach dem Arbeiten:
```bash
git add .
git commit -m "deine-aenderungen"
git push origin main
```

### Konflikte lösen:
```bash
git merge origin/main
# Konflikte manuell lösen
git add .
git commit -m "merge-konflikte-geloest"
```

---

## MCP-Server Start

### Automatisch bei Session-Start
Der MCP-Server sollte automatisch mit dem Code-mode starten.

### Manuell falls nötig:
```bash
# MCP-Server starten
python -m mcp.server.main &
```

### Testen:
```bash
curl http://localhost:3000/health
```

---

## Troubleshooting

### MCP funktioniert nicht:
1. Python-Pakete prüfen: `pip list | grep mcp`
2. Logs prüfen: `cat ~/.mcp/logs/*.log`
3. Neustart: `pkill -f mcp && python -m mcp.server &`

### Repo-Sync-Probleme:
1. Remote prüfen: `git remote -v`
2. Branch prüfen: `git branch -a`
3. Fetch: `git fetch --all`

### Projekt läuft nicht:
1. Virtualenv aktivieren: `source venv/bin/activate`
2. Reinstall: `pip install -e .`
3. Playwright: `playwright install chromium`
