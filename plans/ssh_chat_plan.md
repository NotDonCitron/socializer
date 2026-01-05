# SSH-Chat Projekt Plan

## Ziel
Ein terminal-basiertes Chat-System, das SSH nutzt, damit zwei Laptops direkt kommunizieren können.

## Anforderungen
- Beide Laptops haben Internet und können sich direkt erreichen (Port 22)
- Rein terminal-basierte Oberfläche (wie `write`/`talk`, aber moderner)
- Direkte SSH-Verbindung zwischen den Geräten

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    SSH-CHAT SYSTEM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   LAPTOP A                              LAPTOP B                │
│   ┌──────────────────┐                  ┌──────────────────┐    │
│   │  ssh-chat.py     │ ◄──────────────► │  ssh-chat.py     │    │
│   │  ├── client()    │    SSH Tunnel    │  ├── client()    │    │
│   │  └── server()    │                  │  └── server()    │    │
│   └──────────────────┘                  └──────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Technischer Ansatz

### Option 1: SSH + Named Pipes (einfach)
```
┌──────────────┐         SSH-Tunnel          ┌──────────────┐
│ Laptop A     │◄──────────────────────────►│ Laptop B     │
│ chat-client  │                           │ chat-client  │
│              │    ssh user@host -L        │              │
│              │    5000:localhost:5000     │              │
└──────────────┘                           └──────────────┘
       │                                         │
       └───────── Named Pipe / WebSocket ────────┘
```

### Option 2: SSH + Python sockets (flexibler)
- SSH-Tunnel für sichere Verbindung
- Python-Socket-Server auf beiden Seiten
- Bidirektionale Kommunikation über den Tunnel

## Implementierungsschritte

### Phase 1: SSH-Einrichtung
1. SSH-Schlüssel auf beiden Laptops generieren
2. Öffentliche Schlüssel austauschen und in `authorized_keys` eintragen
3. SSH-Verbindung ohne Passwort testen
4. Lokalen Port-Forward einrichten

### Phase 2: Chat-Server
1. Python-Socket-Server erstellen (Port 5000)
2. Verbindung akzeptieren und Nachrichten empfangen
3. Nachrichten an anderen Laptop via SSH-Tunnel weiterleiten
4. Lokale Anzeige der empfangenen Nachrichten

### Phase 3: Chat-Client
1. Terminal-Interface mit `curses` oder `rich`
2. Nachrichten-Eingabe mit Timestamp
3. Automatische Verbindung via SSH-Tunnel
4. parallele Eingabe und Anzeige

### Phase 4: Features
- Nachrichtenverlauf speichern
- Farbige Ausgabe (mit `rich` library)
- Datei-Transfer optional
- Verbindungstest und Reconnect-Logik

## Dateistruktur
```
ssh-chat/
├── ssh_chat/
│   ├── __init__.py
│   ├── server.py      # Socket-Server
│   ├── client.py      # Socket-Client
│   ├── ui.py          # Terminal-Interface
│   └── tunnel.py      # SSH-Tunnel-Management
├── config.yaml        # Konfiguration
├── requirements.txt
└── README.md
```

## Dependencies
- `paramiko` (SSH-Client)
- `rich` (Terminal-UI)
- `pyyaml` (Konfiguration)

## Nächste Schritte
1. **SSH-Schlüssel-Austausch** - Beide Laptops können sich per SSH verbinden
2. **Port-Forwarding testen** - `ssh -L 5000:localhost:5000 user@host`
3. **Socket-Server** - Python-Server, der Nachrichten empfängt
4. **Terminal-UI** - Curses oder Rich-basierte Oberfläche
5. **Integration** - Alles zusammenfügen
