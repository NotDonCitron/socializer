# 🚀 Socializer Dev Workflow

Dies ist dein persönlicher Guide für das Remote-Setup. Hier steht alles, was du wissen musst, um von überall zu arbeiten.

## 🔗 Verbindung aufbauen

### 1. Terminal (Der "Controller")
Egal ob Mac oder Laptop, tippe einfach:
```bash
pc       # Verbindet dich mit dem PC (in eine sichere Tmux-Session)
laptop   # Verbindet dich mit dem Laptop
```
*Tipp:* Wenn du die Verbindung verlierst, einfach nochmal tippen. Du landest exakt dort, wo du warst.

### 2. Zed (Die IDE)
1. Drücke `Cmd + Shift + P` (oder `Ctrl + Shift + P`).
2. Tippe: `remote`.
3. Wähle: `remote projects: open`.
4. Wähle: `pc`.
5. Ordner: `/home/kek/socializer`.

---

## 💾 Git (Easy Mode)

Wir nutzen Aliase, um Git einfacher zu machen. Diese Befehle funktionieren im Terminal (auf dem PC):

| Befehl | Was er macht | Wann nutzen? |
| :--- | :--- | :--- |
| `save` | `add` + `commit` + `push` | Wenn du Pause machst oder das Gerät wechselst. |
| `load` | `git pull` | Wenn du an einem neuen Gerät startest. |

---

## 🛠️ Projekt-Struktur (Socializer)

*   **`radar/`**: Hier liegt die Kernlogik (Browser-Steuerung, Proxies).
*   **`examples/`**: Test-Skripte (z. B. `proxy_providers_demo.py`).
*   **Ignorierte Ordner:**
    *   `ig_session/`, `tiktok_session/` (Browser-Daten, nicht löschen, aber nicht in Git).
    *   `external_repos/` (Andere Tools, die du reinkopiert hast).

---

## ⚡ Troubleshooting

*   **Verbindung hängt?**
    *   Im Terminal: Drücke `Enter` -> `~` -> `.` (Das beendet eine tote SSH-Session).
    *   Oder schließe das Fenster einfach.
*   **Zed findet `pc` nicht?**
    *   Prüfe, ob Tailscale an ist.
    *   Versuche im Terminal `ssh pc`. Wenn das geht, starte Zed neu.

---
*Erstellt vom Gemini Agent - 06.01.2026*
