# SSH-Chat Projekt - Vollständiger Step-by-Step Guide

## Übersicht
```
Laptop A (Dein PC) ◄───────────────────────► Laptop B (Freund)
  IP: ???                                      IP: ???
  User: dein_user                              User: freund_user
```

---

## SCHRITT 1: Projekt auf beiden Laptops einrichten

### AUF BEIDEN LAPTOPS:

```bash
# 1. Ins Projekt-Verzeichnis gehen oder klonen
cd ~/projects
git clone https://github.com/NotDonCitron/socializer.git
cd socializer

# 2. Dependencies installieren
pip install -e .

# 3. Playwright installieren
playwright install chromium

# 4. Testen ob alles funktioniert
radar --help
python -m pytest tests/ -v
```

**Erwartete Ausgabe:** `radar --help` zeigt CLI-Hilfe an

---

## SCHRITT 2: MCP auf beiden Laptops testen

### AUF BEIDEN LAPTOPS:

```bash
# MCP-Server testen
echo "Testing MCP..."
python -c "from mcp.server import Server; print('MCP OK')"

# Oder MCP-Server starten
python -m mcp.server &
```

✅ **Erfolg, wenn:** Keine Fehler, "MCP OK" wird angezeigt

---

## SCHRITT 3: Git Sync vorbereiten

### AUF BEIDEN LAPTOPS:

```bash
# Remote prüfen
git remote -v

# Branch prüfen
git branch -a

# Ersten Sync machen
git pull origin main
```

### BEVOR IHR ARBEITET (Regel):
```bash
git pull origin main  # Immer erst holen!
```

### NACHDEM IHR ÄNDERUNGEN GEMACHT HABT:
```bash
git add .
git commit -m "deine-aenderungen-beschreiben"
git push origin main
```

---

## SCHRITT 4: SSH-Schlüssel generieren

### AUF BEIDEN LAPTOPS:

```bash
# SSH-Schlüssel generieren
ssh-keygen -t ed25519 -C "$(whoami)@$(hostname)"

# Drücke ENTER für Standard-Speicherort (~/.ssh/id_ed25519)
# Leere Passphrase oder你自己选

# Öffentlichen Schlüssel anzeigen
cat ~/.ssh/id_ed25519.pub
```

**Output-Beispiel:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB dein_user@laptop
```

→ **Kopiere diese Zeile!** (Eine pro Person)

---

## SCHRITT 5: Schlüssel tauschen

### SCHRITT 5a: Du sendest an Freund
Per WhatsApp, E-Mail, Discord senden:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5... dein_user@laptop
```

### SCHRITT 5b: Freund sendet an dich
Du empfängst:
```
ssh-ed25519 BBBBB3NzaC1lZDI1NTE5... freund@laptop
```

---

## SCHRITT 6: Schlüssel eintragen

### AUF DEINEM LAPTOP:
```bash
# Freund's Schlüssel eintragen
echo "ssh-ed25519 BBBBB3NzaC1lZDI1NTE5... freund@laptop" >> ~/.ssh/authorized_keys

# Berechtigungen setzen
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### AUF FREUND'S LAPTOP:
```bash
# Deinen Schlüssel eintragen
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5... dein_user@laptop" >> ~/.ssh/authorized_keys

# Berechtigungen setzen
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

---

## SCHRITT 7: IP-Adressen ermitteln

### AUF DEINEM LAPTOP:
```bash
# Linux
ip addr show | grep 'inet ' | grep -v 127.0.0.1

# macOS
ipconfig getifaddr en0
```

**Output-Beispiel:**
```
inet 192.168.1.105/24 brd 192.168.1.255 scope global en0
```
→ **Deine IP:** 192.168.1.105

### AUF FREUND'S LAPTOP:
```bash
# Gleiche Befehle
ip addr show | grep 'inet ' | grep -v 127.0.0.1
```

→ **Freund's IP:** 192.168.1.XXX

---

## SCHRITT 8: SSH-Dienst starten

### AUF BEIDEN LAPTOPS:

**Linux:**
```bash
# SSH-Dienst starten
sudo systemctl start sshd

# Automatisch starten bei Boot
sudo systemctl enable sshd
```

**macOS:**
```bash
# SSH aktivieren (Systemeinstellungen → Sharing → Remote Login)
# Oder per Terminal:
sudo systemsetup -setremotelogin on
```

---

## SCHRITT 9: SSH-Verbindung testen

### AUF DEINEM LAPTOP → Teste Freund:
```bash
# Ersetze mit Freund's Benutzer und IP
ssh freund_user@192.168.1.XXX

# Wenn nach Passwort gefragt wird ❌ = Problem
# Wenn verbunden ohne Passwort ✅ = Erfolg!
```

### AUF FREUND'S LAPTOP → Teste dich:
```bash
ssh dein_user@192.168.1.105
```

✅ **Erfolg, wenn:** Kein Passwort nötig, Terminal wechselt zum anderen Laptop

**Beenden:**
```bash
exit
```

---

## SCHRITT 10: Chat testen (Port-Forwarding)

### AUF FREUND'S LAPTOP (Server):
```bash
# SSH-Tunnel erstellen
ssh -L 5000:localhost:5000 dein_user@192.168.1.105 -N

# Das hält den Tunnel offen
```

### AUF DEINEM LAPTOP (Client):
```bash
# Verbindung testen
nc localhost 5000

# Tippe etwas und sende (Enter)
# Freund sollte es sehen!
```

**Beenden:** `Ctrl+C` auf beiden Seiten

---

## PROBLEMLÖSUNG

### Problem: "Permission denied"
```bash
# Schlüssel prüfen
cat ~/.ssh/authorized_keys

# Berechtigungen prüfen
ls -la ~/.ssh/

# Sollte zeigen:
# drwx------ (700) ~/.ssh
# -rw------- (600) ~/.ssh/authorized_keys
```

### Problem: "Connection refused"
```bash
# SSH-Dienst prüfen
systemctl status sshd

# Falls nicht aktiv:
sudo systemctl start sshd
```

### Problem: "Connection timeout"
→ Firewall blockiert Port 22
→ Router-Einstellungen prüfen
→ Beide Laptops müssen im gleichen Netzwerk sein!

---

## CHECKLISTE - Vor dem Chat-Code

| Test | Dein Laptop | Freund's Laptop |
|------|-------------|-----------------|
| `radar --help` funktioniert | ☐ | ☐ |
| MCP-Server startet | ☐ | ☐ |
| `git pull origin main` | ☐ | ☐ |
| SSH-Schlüssel generiert | ☐ | ☐ |
| Schlüssel ausgetauscht | ☐ | ☐ |
| `ssh user@ip` funktioniert | ☐ | ☐ |

**Alle Häkchen gesetzt?** → Dann kann der Chat-Code geschrieben werden!

---

## NÄCHSTE SCHRITTE

1. SSH-Verbindung zwischen beiden Laptops bestätigen ✅
2. Chat-Server in Python schreiben
3. Chat-Client in Python schreiben
4. Terminal-UI mit `rich` hinzufügen
5. Bidirektionale Kommunikation testen

**Bereit für Schritt 2?** Sag Bescheid!
