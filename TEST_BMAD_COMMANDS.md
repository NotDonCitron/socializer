# BMAD mit Gemini CLI - Befehle verstehen

## ✅ Alle BMAD-Befehle sind installiert!

Sie haben **25 BMAD-Befehle** in `.gemini/commands/` installiert.

---

## ⚠️ WICHTIG: Befehl-Format

### Problem: `/bmad:agents:bmm:analyst` funktioniert nicht

Das liegt daran, dass **Gemini CLI ein anderes Befehl-System** verwendet.

---

## 🎯 Wie BMAD mit Gemini funktioniert

### Theorie 1: Dateiname = Befehl

In `.gemini/commands/` sind Dateien wie:
- `bmad-agent-bmm-analyst.toml`
- `bmad-workflow-core-brainstorming.toml`

**Mögliche Befehle:**
```bash
# Versuch 1: Nur Dateiname (ohne Präfix)
analyst

# Versuch 2: Mit bmad-Präfix
bmad:analyst

# Versuch 3: Mit Doppelpunkt als Trennzeichen
bmad.agents.bmm.analyst
```

### Theorie 2: BMAD ist Extension

Möglich, dass BMAD als **Extension** installiert werden muss:

```bash
gemini extensions install <pfad>
```

---

## 🧪 Testen Sie jetzt!

### Testen Sie diese Befehle in Gemini:

```bash
# Starten Sie Gemini:
gemini

# Dann testen Sie EINEN dieser Befehle:

# Versuch 1:
analyst

# Versuch 2:
bmad:analyst

# Versuch 3:
/bmad-analyst

# Versuch 4:
bmad-agent-analyst
```

### Was passiert:

Gemini sollte:
1. Nach Dateinamen suchen
2. Wenn es findet, die `.toml` laden
3. Die `prompt`-Anweisungen ausführen
4. Analyst-Agent aktivieren

---

## 📋 Alternative: OpenCode nutzen

Wenn Gemini-Befehle nicht klappen, nutzen Sie **OpenCode**:

```bash
# 1. Starten Sie OpenCode
opencode

# 2. Öffnen Sie den Analyst-Agenten
# File → Open → .opencode/agent/bmad-agent-bmm-analyst.md

# 3. Agent lädt automatisch
# Menü erscheint
```

---

## 📚 Dokumentation prüfen

Ich kann für Sie prüfen:

1. **Gemini CLI Dokumentation** online
2. **BMAD-Dokumentation** für Gemini-Integration
3. **OpenCode** als Alternative

---

## ❓ Was passiert, wenn Sie testen?

**Bitte prüfen Sie:**

1. ✅ **Analyst lädt?** → Dann funktioniert es!
2. ❌ **"Unknown command"?** → Dann müssen wir herausfinden, wie es funktioniert
3. 📝 **Fehler?** → Sagen Sie mir die genaue Fehlermeldung

**Geben Sie mir Ihr Ergebnis mit:** 🧪
