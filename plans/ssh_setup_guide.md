# SSH-Einrichtung für Laptop-zu-Laptop Chat

## Übersicht
Beide Laptops müssen sich per SSH ohne Passwort verbinden können.

## Schritt 1: SSH-Schlüssel generieren

### Auf Laptop A (Dein PC):
```bash
# 1. SSH-Schlüssel generieren
ssh-keygen -t ed25519 -C "deine@email.com"

# 2. Speicherort bestätigen (Standard: ~/.ssh/id_ed25519)
# 3. Passphrase eingeben (optional, aber sicherer)

# 4. Öffentlichen Schlüssel anzeigen und kopieren
cat ~/.ssh/id_ed25519.pub
# Output: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5... deine@email.com
```

### Auf Laptop B (Freund):
```bash
# Gleiche Schritte
ssh-keygen -t ed25519 -C "freund@email.com"
cat ~/.ssh/id_ed25519.pub
```

## Schritt 2: Schlüssel austauschen

### Laptop A tut dies:
```bash
# Freund's öffentlichen Schlüssel in authorized_keys eintragen
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5... freund@email.com" >> ~/.ssh/authorized_keys

# Berechtigungen setzen (wichtig!)
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Laptop B tut dies:
```bash
# Deinen öffentlichen Schlüssel eintragen
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5... deine@email.com" >> ~/.ssh/authorized_keys

chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

## Schritt 3: SSH-Verbindung testen

### Laptop A → Laptop B:
```bash
# SSH-Verbindung zu Freund's Laptop testen
# Ersetze username mit Freund's Benutzernamen und IP mit Freund's IP
ssh username@192.168.x.x

# Wenn es funktioniert:
exit
```

### Laptop B → Laptop A:
```bash
# Freund testet Verbindung zu deinem Laptop
ssh dein_username@deine.ip

# Wenn es funktioniert:
exit
```

## Schritt 4: Port-Forwarding für Chat testen

### Auf Laptop B (Freund startet Server):
```bash
# SSH-Tunnel erstellen
ssh -L 5000:localhost:5000 username@deine-ip -N

# Das hält den Tunnel offen
```

### Auf Laptop A:
```bash
# Verbindung testen
nc localhost 5000

# Wenn verbunden, kannst du tippen und Freund sieht es
```

## Netzwerk-Herausforderungen

### Problem: Keine direkte Verbindung (beide hinter Router/Firewall)
**Lösung 1: VPN**
- WireGuard oder Tailscale installieren
- Beide Laptops im gleichen VPN-Netzwerk

**Lösung 2: Relais-Server**
- Ein Server im Internet (z.B. $5/mo DigitalOcean)
- Beide verbinden sich zum Server

**Lösung 3: Ngrok (einfach, aber begrenzt)**
```bash
# Auf Laptop B
ngrok tcp 22  # SSH-Port weiterleiten
```

## Nächste Schritte
Nach erfolgreicher SSH-Verbindung:
1. Python-Chat-Server installieren
2. SSH-Tunnel für Port 5000 einrichten
3. Chat-Client starten
