# Copy-Paste SSH-Chat Setup Befehle

## AUF BEIDEN LAPTOPS AUSFÜHREN

### Schritt 1: SSH-Schlüssel generieren
```bash
ssh-keygen -t ed25519 -C "$(whoami)@$(hostname)"
```
- Drücke ENTER um Standard-Speicherort zu akzeptieren
- Leere Passphrase oder你自己选

### Schritt 2: Deinen Schlüssel anzeigen
```bash
cat ~/.ssh/id_ed25519.pub
```
→ **Kopiere diese Ausgabe** und sende sie an deinen Freund

### Schritt 3: Freund's Schlüssel eintragen
```bash
echo "FRIENDS_KEY_HERE" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```
Ersetze `FRIENDS_KEY_HERE` mit dem Schlüssel deines Freundes!

---

## NUR AUF DEINEM LAPTOP

### IP-Adresse ermitteln
```bash
# Linux
ip addr show | grep 'inet ' | grep -v 127.0.0.1

# macOS
ipconfig getifaddr en0
```

### SSH-Verbindung testen
```bash
ssh freund@192.168.x.x
```
Ersetze `192.168.x.x` mit der IP deines Freundes!

---

## SSH-Dienst starten (falls nötig)

**Linux:**
```bash
sudo systemctl start sshd
sudo systemctl enable sshd
```

**macOS:**
```bash
sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist
```

---

## Chat testen (nach SSH funktioniert)

```bash
# Tunnel erstellen
ssh -L 5000:localhost:5000 freund@192.168.x.x -N

# Verbindung testen
nc localhost 5000
```

---

## Problembehandlung

### "Permission denied"
→ SSH-Schlüssel nicht richtig eingetragen
→ Nochmal Schritt 3 wiederholen

### "Connection refused"
→ SSH-Dienst läuft nicht
→ Siehe "SSH-Dienst starten" oben

### "Connection timeout"
→ Firewall blockiert Verbindung
→ Port 22 freigeben

---

## Zusammenfassung

| Laptop | Benutzer | IP | Schlüssel |
|--------|----------|-----|-----------|
| Dein PC | dein_user | deine.ip | dein_pubkey |
| Freund | freund | freund.ip | freund_pubkey |

**Wichtig:** Beide Laptops müssen im gleichen Netzwerk sein (z.B. gleiches WLAN)!
