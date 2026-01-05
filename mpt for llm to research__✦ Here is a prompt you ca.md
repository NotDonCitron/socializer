# TikTok Automation Bot – Technischer Forschungsprompt (2025/2026)

## Kontext
Ich entwickle einen Python-basierten TikTok-Upload-Automation-Bot mit Playwright. Ziel: zuverlässige, stabile Uploads ohne Shadowban, mit erweiterbarer Architektur für Multi-Account-Management.

---

## 1. Anti-Bot-Detection & Evasion

### A) Browser Fingerprinting
- Fragen: Welche Browser-Attribute prüft TikTok 2025/2026 (Canvas/WebGL, navigator.webdriver, DevTools-/Automation-Checks, Timing/Performance-Muster)? Gibt es Private-Mode/Incognito-Erkennungen?
- Bedarf: Bewertung von `playwright-stealth` und ähnlichen Ansätzen; was scheitert gegen moderne Checks? Wie sollte Anti-Detect-Browser + Proxy (1 Proxy pro Account, sticky) aussehen?
- Gewünscht: Code-/Konfig-Beispiele für `playwright.launch()` mit Anti-Detection-Setup (User-Agent, Flags, Proxy), sowie TLS-/Header-Anpassung (JA3/JA4-orientiert, soweit machbar).

### B) Behavioral Pattern Recognition
- Fragen: Welche Upload-Verhaltensmuster werden geflaggt (Klick-Timing, Mausbewegungen, Keyboard-Timing bei Captions, Netzwerkfrequenz/WebSocket-Nutzung)?
- Bedarf: Konkrete Empfehlungen für menschliche Delays (Verteilungen, Jitter), Einsatz von `await page.wait_for_timeout(random_delay())`.
- Gewünscht: Tools/Ansätze, um Bot-Verhalten gegen Erkennungsmuster zu testen (Outlier-Detection, Demos, Metriken).

### C) Account-Sicherheit & Shadowban-Prävention
- Fragen: Welche Indikatoren führen zu Shadowban (Upload-Frequenz, Account-Alter vs. Timing, IP-/Proxy-Wechsel, MIME-/Metadaten-Anomalien)?
- Bedarf: Techniken zur Shadowban-Erkennung (Reichweitenabfall, spezifische Response-Codes, Rate-Limits).
- Gewünscht: Patterns für langfristig stabile Sessions/Accounts (z.B. 1 Proxy = 1 Device = 1 Account).

---

## 2. TikTok Studio Interface & DOM-Stabilität

### A) Studio Interface Updates
- Fragen: Wie oft ändert sich das `/tiktokstudio/upload`-UI (Post-Button, Caption-Feld, Preview/Progress)? Gibt es stabile `data-e2e` oder ARIA-Attribute?
- Bedarf: Empfehlung robuster Selektoren in Priorität: 1) `data-e2e`, 2) `aria-label`, 3) CSS-Teilmatching, 4) XPath-Fallback; Strategie DOM-Polling vs. `MutationObserver`.
- Codewunsch (Python/Playwright, Pseudocode ok):
```python
async def find_post_button(page):
    # 1) data-e2e
    # 2) aria-label
    # 3) CSS-Teilmatching
    # 4) XPath-Fallback
    return handle
```

### B) Video Processing & Timing
- Fragen: Woran erkenne ich zuverlässig "ready to post"? (Preview-Render-Zeit, Codec-/Format-Checks, Thumbnail-Signale)
- Bedarf: Relevante Network-Events/Endpoints (z.B. `/api/*upload*`) für Status; UI-/Network-Signale für Erfolg; typische Fehlercodes und Reaktionen.

---

## 3. Session & Cookie Management

### A) Langzeit-Session-Persistenz
- Fragen: Lebensdauer/TTL und Rotation von `tt_webid_v2`, `csrf_session_id`; Device-Binding-Mechanismen (Fingerprint + Cookie + IP).
- Bedarf: Best Practices für Cookie-Speicherung (JSON/SQLite), Expiry-Handling, Auto-Refresh/Re-Login, Multi-Account-Isolation.
- Empfehlung: Architektur "1 Browser-Context pro Account" in Playwright.

### B) Session-Validierung ohne teure Aktion
- Fragen: Health-Check-Endpoints für stille Session-Prüfung (Profil-/Dashboard-Fetch), typische Response-Patterns für "stale/invalid".
- Gewünscht: Konkreter Probe-Request (URL, Methode, erwarteter Status/Body), Fehlerbehandlung (Re-Login, Captcha-Flow), sinnvolle Prüfintervalle.

---

## 4. Sicherheit, CSP & Headless-Mode

### A) CSP & WebSockets
- Fragen: Beeinflussen CSP-Violations (z.B. `wss://im-ws.tiktok.com`) den Upload-Erfolg oder nur Telemetrie/Chat? Können geblockte WSS-Verbindungen Anti-Bot-Signale sein?
- Gewünscht: Playwright-Konfig (Pseudocode) mit Console-/CSP-Logging, WebSocket-Handling; Empfehlung, ob WSS blockieren oder erlauben.

### B) Headless vs. Headful
- Fragen: Unterschiede in Detection/Sicherheitschecks; wie wird `--headless=new` behandelt? Performance- vs. Detection-Tradeoffs.
- Gewünscht: Empirische/Community-Daten zu Upload-Success-Rates Headless vs. Headful; Empfehlung fürs Production-Setup; Tipps, Headless möglichst menschlich wirken zu lassen.

---

## 5. Zusätzliche Forschungsthemen
- Video-Format-Optimierung: Beste Codecs/Bitraten/Container 2025/2026, Metadaten-Stripping, Dateigrößen-Limits und Kompression.
- Multi-Account-Management: Rotationsstrategien, Proxy-Management (Residential/Mobile, 1:1 Mapping Account↔Proxy), typische Erkennungsmuster.
- Error Recovery & Resilience: Häufige Upload-Fehler (UI/Netzwerk/HTTP), Retry-Strategien (Backoff, Re-Upload), Rate-Limiting-Handling.

---

## 6. Deliverables erwünscht
Für jeden Bereich:
1. Technische Erklärung (2–3 Absätze, gern tiefgehend)
2. Code-Beispiele (Python/Playwright, optional JavaScript)
3. Best Practices
4. Fallstricke & Workarounds
5. Monitoring-/Testing-Strategien (Metriken, Log-Punkte, Tools)

---

## Zusätzlicher Kontext
- Zielwerte: Zuverlässigkeit > 95 %, Latenz < 2 Minuten pro Upload
- Skalierung: Jetzt Single-Account, später Multi-Account
- Risikoprofil: Moderates Risiko, Accounts sollen sicher bleiben
- Tech-Stack: Python 3.10+, Playwright (async), optional Anti-Detect-Browser/Proxies

---

## Nutzungsvorschläge
- Direkt: Kompletten Prompt in Claude/Gemini/Qwen einfügen für Detailreport.
- Iterativ: Nachricht 1 (Abschnitte 1–2), Nachricht 2 (3–4), Nachricht 3 (5–6).
- MCP/CLI: Prompt als Datei an dein Research-Tool übergeben (z.B. `@research "TikTok Automation 2025/2026" < prompt.md`).
