# BMAD mit Gemini CLI - Richtig nutzen

## ✅ Alle BMAD-Befehle sind installiert!

Sie haben **25 BMAD-Befehle** in `.gemini/commands/` installiert.

---

## 🎯 RICHTIGE Befehle für Gemini CLI

### Aktuelle Version:
- **Gemini CLI**: v0.22.5 (oder höher)
- **BMAD-Format**: `/bmad:` namespace (Kleinbuchstaben!)

### Alle verfügbaren Befehle:

#### BMad Method Agents (9):
```bash
# Mit bmad-Präfix:
/bmad:agents:bmm:analyst
/bmad:agents:bmm:pm
/bmad:agents:bmm:architect
/bmad:agents:bmm:dev
/bmad:agents:bmm:sm
/bmad:agents:bmm:tech-writer
/bmad:agents:bmm:ux-designer
/bmad:agents:bmm:tea
/bmad:agents:bmm:quick-flow-solo-dev

# Oder OHNE bmad-Präfix (abhängig von Version):
/agents:bmm:analyst
/agents:bmm:pm
/agents:bmm:architect
# ... usw.
```

#### BMad Builder Agents (3):
```bash
/bmad:agents:bmb:agent-builder
/bmad:agents:bmb:workflow-builder
/bmad:agents:bmb:module-builder
```

#### Creative Intelligence Agents (5):
```bash
/bmad:agents:cis:brainstorming-coach
/bmad:agents:cis:creative-problem-solver
/bmad:agents:cis:design-thinking-coach
/bmad:agents:cis:innovation-strategist
/bmad:agents:cis:storyteller
```

#### Core Agents (1):
```bash
/bmad:agents:core:bmad-master
```

#### Workflows (7):
```bash
/bmad:workflows:core:brainstorming
/bmad:workflows:core:party-mode
/bmad:workflows:bmm:generate-project-context
/bmad:workflows:bmb:agent
/bmad:workflows:bmb:create-module
/bmad:workflows:bmb:module
/bmad:workflows:bmb:workflow
```

---

## 🚀 SOFORT STARTEN

### Schritt 1: Gemini starten
```bash
gemini
```

### Schritt 2: Analyst Agent aufrufen
```bash
# IN GEMINI EINGEBEN:
/bmad:agents:bmm:analyst
```

### Schritt 3: Workflow initialisieren
```bash
# Analyst Menüpunkt wählen:
*workflow-init
```

---

## 💡 Pro Tips

1. **Tab-Completion nutzen**:
   - Geben Sie `/bmad:` ein und drücken Sie Tab
   - Gemini zeigt alle verfügbaren BMAD-Befehle

2. **Case-Insensitive**:
   - Groß-/Kleinschreibung ist egal
   - `/bmad:AGENTS:BMM:ANALYST` funktioniert auch!

3. **Fuzzy Matching**:
   - Teilweise Übereinstimmung erlaubt
   - Auch `/agents:analyst` könnte funktionieren

4. **Kontext bewahren**:
   - BMAD-Agenten erinnern sich an den Gesprächskontext
   - Keine neuen Chat für jeden Befehl nötig

---

## 🎯 Empfohlener Start-Ablauf

### Für Neues Projekt:
```
1. /bmad:agents:bmm:analyst
2. *workflow-init
3. Empfehlung folgen (z.B. "BMad Method" Track)
4. Nächste Agenten laden (PM, Architect, etc.)
```

### Für Bestehenden Code analysieren:
```
/bmad:workflows:bmm:generate-project-context
```

### Für Brainstorming:
```
/bmad:agents:cis:brainstorming-coach
# Oder:
/bmad:workflows:core:brainstorming
```

---

## 📋 Verzeichnisübersicht

```
.gemini/commands/
├── bmad-agent-bmm-analyst.toml         # Analyst
├── bmad-agent-bmm-pm.toml               # Projektmanager
├── bmad-agent-bmm-architect.toml         # Architekt
├── bmad-agent-bmm-dev.toml              # Entwickler
├── bmad-agent-bmm-sm.toml                # Scrum Master
├── bmad-agent-bmm-tech-writer.toml        # Tech Writer
├── bmad-agent-bmm-ux-designer.toml      # UX Designer
├── bmad-agent-bmm-tea.toml               # Meeting-Moderation
├── bmad-agent-bmm-quick-flow-solo-dev.toml  # Schnelle Entwicklung
├── bmad-workflow-*.toml              # Workflows
├── loop.toml                           # Ihr bestehender Befehl (erhalten)
└── loop.toml.backup                    # Backup
```

---

## ❓ Noch Fragen?

- **Schlägt es noch auf "Unknown command"?**
  → Testen Sie: `/agents:bmm:analyst` (ohne bmad-Präfix)
  
- **Agent wird nicht geladen?**
  → Lassen Sie mich die genaue Fehlermeldung wissen

- **Sie möchten OpenCode nutzen?**
  → Ich zeige Ihnen wie man OpenCode damit startet

---

**Viel Erfolg bei Ihrer BMAD-Analyse! 🚀**
