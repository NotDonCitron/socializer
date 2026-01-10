# Spec: Basis-Automatisierungs-Framework

## Ziel
Ein robustes Fundament für die Browser-Automatisierung mit Playwright schaffen, das speziell auf Social-Media-Plattformen (Instagram, TikTok) ausgerichtet ist.

## Anforderungen
- **Umgebung:** Playwright muss installiert und konfiguriert sein.
- **Abstraktion:** Eine Basis-Klasse/Modul zur Kapselung von Playwright-Aktionen (z.B. `launch_browser`, `new_context_with_stealth`).
- **Session-Management:** Unterstützung für persistente Kontexte (Cookies/Sessions), um 2FA-Hürden zu minimieren.
- **Login-Logik:** Implementierung eines Beispiel-Logins für Instagram.
- **Robustheit:** Verwendung von `slowMo`, realistischen Viewports und User-Agents.
- **Testbarkeit:** Alle Kernkomponenten müssen Unit-Tests haben (TDD-Ansatz).

## Akzeptanzkriterien
- Playwright-Tests laufen erfolgreich durch.
- Ein Instagram-Login kann (simuliert oder real mit Test-Account) durchgeführt werden.
- Die Code-Abdeckung für die neuen Module liegt bei >80%.
