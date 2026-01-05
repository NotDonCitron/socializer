# SSH Chat - Terminal Chat über SSH

Ein einfaches, terminal-basiertes Chat-System für die Kommunikation zwischen zwei Laptops über SSH.

## 🚀 Schnellstart

### 1. SSH einrichten (siehe [`plans/ssh-chat-step-by-step.md`](plans/ssh-chat-step-by-step.md))

### 2. Chat starten

**Auf Laptop A (Server):**
```bash
python ssh_chat.py server
```

**Auf Laptop B (Client mit SSH-Tunnel):**
```bash
python ssh_chat.py tunnel-client --remote-host IP_VON_A --remote-user USER_VON_A
```

### 3. Chatten!

Beide können jetzt Nachrichten tippen und sehen sie in Echtzeit.

## 📋 Modi

### `server`
Startet Chat-Server auf localhost:5000
```bash
python ssh_chat.py server
```

### `client`
Verbindet mit Server
```bash
python ssh_chat.py client --host localhost --port 5000
```

### `tunnel-client` (Empfohlen)
Erstellt SSH-Tunnel und verbindet automatisch
```bash
python ssh_chat.py tunnel-client --remote-host 192.168.1.100 --remote-user kek
```

### `both`
Server + SSH-Tunnel-Client für bidirektionale Kommunikation
```bash
python ssh_chat.py both --remote-host 192.168.1.100 --remote-user freund
```

## 🔧 Technik

- **Server:** Socket-Server lauscht auf Port 5000
- **Client:** Verbindet mit Server und sendet/empfängt Nachrichten
- **SSH-Tunnel:** Sichere Verbindung über SSH (-L Port-Forwarding)
- **Threading:** Parallele Nachrichtenverarbeitung

## 📁 Dateien

```
ssh_chat/
├── __init__.py      # Paket-Init
├── server.py        # Chat-Server
└── client.py        # Chat-Client

ssh_chat.py          # Haupt-Script mit allen Modi
```

## 🎯 Features

- ✅ Terminal-basiert (wie `write`/`talk`)
- ✅ SSH-gesichert
- ✅ Echtzeit-Kommunikation
- ✅ Mehrere Clients gleichzeitig
- ✅ Zeitstempel
- ✅ Sauberes Beenden (Ctrl+C)

## 🐛 Troubleshooting

### "Connection refused"
- Server läuft nicht → `python ssh_chat.py server`
- SSH-Tunnel fehlt → `tunnel-client` Modus verwenden

### "Permission denied"
- SSH-Schlüssel nicht ausgetauscht
- `~/.ssh/authorized_keys` prüfen

### Keine Nachrichten
- Beide im gleichen Netzwerk?
- Firewall blockiert Port 22?

## 🔄 Workflow

1. **SSH-Setup:** Schlüssel generieren und austauschen
2. **Server starten:** Ein Laptop startet Server
3. **Client verbinden:** Anderer Laptop verbindet über SSH-Tunnel
4. **Chatten:** Nachrichten werden bidirektional übertragen

## 🎉 Erfolg!

SSH-Chat ist bereit für Team-Koordination! 🚀