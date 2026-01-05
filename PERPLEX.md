<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# github.com/NotDonCitron/socializer bitte analysiere mein projekt und schlage verbesserungen vor

Perfekt! Jetzt habe ich genug Informationen für eine fundierte Analyse. Lasse mich ein strukturiertes Analyse-Dokument erstellen:

## 📊 **Analyse deines Socializer-Projekts**

Dein Projekt ist ein **Instagram Stealth Uploader** mit zukunftsorientierter Architektur für Multi-Platform-Automatisierung. Hier ist meine detaillierte Analyse mit Verbesserungsvorschlägen:

***

### **✅ Stärken**

1. **Intelligente Stealth-Technologie**
    - Nutzt undetected ChromeDriver für Bot-Detection-Umgehung
    - Cookie-basierte Authentifizierung statt direktem Login
    - Human-like Verhalten durch Zufallsverzögerungen
2. **Modulare Architektur**
    - Klare Separation: Backend (Automation) + Frontend (Admin Panel)
    - Erweiterbar für neue Plattformen (TikTok, YouTube etc.)
    - SQLite für Persistenz mit Upgrade-Möglichkeit zu PostgreSQL
3. **Gute Multi-Sprach-Unterstützung**
    - Deutsche + englische Selektoren für Instagram-Elemente
    - Mehrsprachige Caption-Generierung
4. **Auto-Caption-System**
    - Hashtag-Scraping aus Instagram-Suchergebnissen
    - Fallback-Mechanismen für Robustheit

***

### **🔴 Kritische Probleme**

#### **1. Sicherheitsrisiken (SEHR WICHTIG)**

```python
# ❌ PROBLEM: Hardcodierte Credentials im Source Code
manual_cookies = {
    "csrftoken": "F6aBaYkIGs0xPB5qkaAwdN",
    "sessionid": "78167308557%3AT0nfhYqfPFf11X%3A7%3AAYiCfHDQ1TP92tjmX6Yc5jX7TRxP8SM37gPzZDN2dQ"
}
```

**Verbesserung:**

```python
import os
from dotenv import load_dotenv

load_dotenv()

manual_cookies = {
    "csrftoken": os.getenv("IG_CSRF_TOKEN"),
    "sessionid": os.getenv("IG_SESSION_ID"),
    "ds_user_id": os.getenv("IG_USER_ID"),
    "datr": os.getenv("IG_DATR"),
    "ig_did": os.getenv("IG_DID"),
    "mid": os.getenv("IG_MID"),
    "rur": os.getenv("IG_RUR"),
}
```

**Für `.env.example` hinzufügen:**

```bash
IG_CSRF_TOKEN=your_csrf_token_here
IG_SESSION_ID=your_session_id_here
IG_USER_ID=your_user_id_here
IG_DATR=your_datr_here
IG_DID=your_ig_did_here
IG_MID=your_mid_here
IG_RUR=your_rur_here
```


#### **2. Code-Qualitätsprobleme**

**Problem A: Fehlende Exception-Handling-Struktur**

```python
# ❌ Too broad catch blocks
except:
    pass
    
# ✅ Better:
except TimeoutException:
    logger.warning(f"Element not found within timeout: {sel}")
except NoSuchElementException as e:
    logger.debug(f"Element selector not found: {sel}")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
```

**Problem B: Keine Logging-Struktur**

- Nutzt `print()` statt strukturiertes Logging
- Unmöglich zu debuggen bei Produktion

**Verbesserung:**

```python
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(f'logs/instagram_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Verwendung
logger.info(f"Navigating to Instagram...")
logger.warning(f"Cookie validation failed for: {name}")
logger.error(f"Upload failed: {e}", exc_info=True)
```


#### **3. Dependencies-Probleme**

```
# ❌ requirements.txt vs pyproject.toml Mismatch!
requirements.txt:
  - undetected-chromedriver>=3.5.0
  - selenium>=4.0.0
  - instagrapi>=2.0.0
  
pyproject.toml:
  - httpx, pydantic, playwright-stealth (völlig anders!)
```

**Verbesserung:** Konsolidiere zu **einer** `pyproject.toml`:

```toml
[project]
name = "socializer"
version = "0.2.0"
requires-python = ">=3.11"
dependencies = [
    "undetected-chromedriver>=3.5.0",
    "selenium>=4.0.0",
    "instagrapi>=2.0.0",
    "pycryptodome>=3.19.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.7.0",
    "PyYAML>=6.0.1",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.4.0",
    "mypy>=1.10.0",
    "pytest>=8.0.0",
    "pytest-mock>=3.14.0",
]

[tool.ruff]
line-length = 100
```


***

### **🟡 Architektur-Verbesserungen**

#### **1. Fehlende Modularisierung**

```python
# ❌ Alles in einer Datei: upload_instagram_stealth.py

# ✅ Besser: Struktur wie:
socializer/
├── core/
│   ├── browser_manager.py      # ChromeDriver & Cookie-Management
│   ├── element_finder.py       # Robuste Element-Lokalisierung
│   └── stealth_engine.py       # Anti-Detection Logik
├── instagram/
│   ├── auth.py                 # Cookie-Injection & Validation
│   ├── uploader.py             # Upload-Flow
│   ├── caption_generator.py    # Hashtag & Caption Logic
│   └── selectors.py            # I18n Element-Selektoren
├── tiktok/                     # Für zukünftige TikTok-Integration
├── utils/
│   ├── logger.py
│   ├── config.py
│   └── validators.py
└── main.py                     # CLI Entry Point
```


#### **2. Fehlende Tests**

```python
# tests/test_instagram_uploader.py
import pytest
from unittest.mock import Mock, patch, MagicMock
from socializer.instagram.uploader import InstagramUploader

@pytest.fixture
def mock_driver():
    return MagicMock()

def test_file_path_validation_success(mock_driver):
    uploader = InstagramUploader(mock_driver)
    assert uploader.validate_file_path("/path/to/image.jpg") is True

def test_file_path_validation_extension_fallback(mock_driver, tmp_path):
    # Test Auto-Detection feature
    img = tmp_path / "test.jpg"
    img.write_text("dummy")
    
    uploader = InstagramUploader(mock_driver)
    result = uploader.validate_file_path(str(tmp_path / "test.png"))
    assert result is True

@patch('socializer.instagram.caption_generator.InstagramAPI')
def test_hashtag_generation(mock_api):
    # Test Hashtag-Scraping
    pass
```


#### **3. Fehlende Konfigurationsmanagement**

```python
# socializer/utils/config.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Instagram Credentials
    ig_csrf_token: str
    ig_session_id: str
    ig_user_id: str
    
    # Browser Settings
    headless: bool = False
    chrome_binary_path: Optional[str] = None
    disable_notifications: bool = True
    
    # Upload Settings
    default_topic: str = "screenshot"
    max_hashtags: int = 15
    upload_timeout: int = 300  # 5 minutes
    
    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    
    class Config:
        env_file = ".env"
        env_prefix = "SOCIALIZER_"

settings = Settings()
```


***

### **🟠 Spezifische Code-Verbesserungen**

#### **Problem 1: Regex für Hashtags zu simpel**

```python
# ❌ Aktuell:
found_tags = re.findall(r"#\w+", caption_el.text)

# ✅ Besser (Unicode-Support für internationale Charaktere):
found_tags = re.findall(r"#[\w\u0080-\uFFFF]+", caption_el.text, re.UNICODE)

# ✅ Oder mit besserer Validierung:
def extract_hashtags(text: str, limit: int = 15) -> List[str]:
    """Extract and validate hashtags from text."""
    raw_tags = re.findall(r"#[\w\u0080-\uFFFF]{2,30}", text, re.UNICODE)
    # Filter invalid (too long, duplicates, etc)
    unique_tags = list(dict.fromkeys(raw_tags))
    return unique_tags[:limit]
```


#### **Problem 2: Hardcoded Waits statt Smart Waits**

```python
# ❌ Problem:
time.sleep(5)  # Zu rigide, spammt Browser unnötig

# ✅ Besser:
def wait_for_element_or_timeout(driver, locator, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        return element
    except TimeoutException:
        logger.error(f"Element not found: {locator}")
        return None

# Usage:
next_btn = wait_for_element_or_timeout(
    driver, 
    (By.XPATH, "//button[text()='Next']"),
    timeout=15
)
if next_btn:
    next_btn.click()
```


#### **Problem 3: String-Verkettung für Captions**

```python
# ❌ Aktuell:
caption = f"Here is a nice photo about {topic}! 📸\n\n" + " ".join(tags)

# ✅ Besser (mit Template System):
from jinja2 import Template

CAPTION_TEMPLATES = {
    "default": "Here is a nice photo about {{ topic }}! 📸\n\n{{ hashtags }}",
    "professional": "{{ hashtags }}\n\nSwipe to see more about {{ topic }}!",
    "casual": "Just sharing my {{ topic }} vibes 🔥\n{{ hashtags }}"
}

def generate_caption(topic: str, hashtags: List[str], style: str = "default") -> str:
    template = Template(CAPTION_TEMPLATES[style])
    return template.render(
        topic=topic,
        hashtags=" ".join(hashtags)
    )
```


***

### **🔵 Deployment \& DevOps**

#### **Fehlend: Docker-Setup**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Chromium
RUN apt-get update && apt-get install -y \
    chromium-browser \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY socializer/ ./socializer/

RUN pip install -e .

CMD ["python", "-m", "socializer.main"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  socializer-worker:
    build: .
    environment:
      - SOCIALIZER_IG_SESSION_ID=${IG_SESSION_ID}
      - SOCIALIZER_LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - socializer-net

  admin-panel:
    build: ./Socializer-Admin
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=sqlite:///./data/socializer.db
    networks:
      - socializer-net
    depends_on:
      - socializer-worker

networks:
  socializer-net:
```


#### **Fehlend: CI/CD Pipeline**

```yaml
# .github/workflows/test.yml
name: Tests & Linting

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Lint with Ruff
        run: ruff check socializer/
      
      - name: Type check with mypy
        run: mypy socializer/
      
      - name: Run tests
        run: pytest tests/ --cov=socializer/
```


***

### **📋 Action Items - Priorität**

| Priorität | Item | Effort | Impact |
| :-- | :-- | :-- | :-- |
| 🔴 CRITICAL | Credentials aus Code entfernen → `.env` | 30min | HOCH |
| 🔴 CRITICAL | Exception-Handling überall | 1h | HOCH |
| 🟠 HIGH | Logging-System implementieren | 1.5h | HOCH |
| 🟠 HIGH | Dependencies konsolidieren (pyproject.toml) | 30min | MITTEL |
| 🟠 HIGH | Code in Module aufteilen | 3h | HOCH |
| 🟡 MEDIUM | Tests schreiben (pytest) | 2h | MITTEL |
| 🟡 MEDIUM | Docker \& Docker-Compose | 1h | MITTEL |
| 🟡 MEDIUM | CI/CD Pipeline (.github/workflows) | 1h | MITTEL |
| 🔵 LOW | Regex für Unicode-Hashtags | 30min | LOW |
| 🔵 LOW | Smart Wait-System | 1.5h | MITTEL |


***

### **📈 Nächste Architektur-Schritte**

1. **Phase 1 (diese Woche)**: Credentials → Env, Logging, Exception-Handling
2. **Phase 2**: Code-Modularisierung + Docker
3. **Phase 3**: Tests + CI/CD
4. **Phase 4**: TikTok-Integration + API-Layer für Admin-Panel

Möchtest du, dass ich ein **refaktoriertes Beispiel** für einen bestimmten Bereich erstelle? Z.B. eine neue `browser_manager.py` oder die `config.py`-Struktur?

---

# 🔧 Copy-Paste Prompts für LLM-Integration

Hier sind **production-ready Prompts**, die du direkt in Claude/ChatGPT/Qwen einphasen kannst. Jeder ist optimiert zum direkten Copy-Paste mit klaren Code-Outputs.

***

## **1. 🔐 Credentials \& Environment Management**

```
Du bist ein Python Security Expert. Refaktoriere folgenden Code, um hardcodierte Credentials zu entfernen und .env-Dateimanagement zu implementieren.

AKTUELLER CODE:
```python
manual_cookies = {
    "csrftoken": "F6aBaYkIGs0xPB5qkaAwdN",
    "datr": "qXRbadgtyvS6GGM_N00U7Wmi",
    "dpr": "2",
    "ds_user_id": "78167308557",
    "ig_did": "7F6BE45A-A1BD-4F63-BAF0-6F48F75FDC41",
    "mid": "aVt0qQAEAAE2pEO2OEHqv51J4qBK",
    "rur": "\"LDC\\05478167308557\\0541799137993:01fe9741d51b0b47d9e3738c365ace4b281dfa1294a4805ceddcc728b8f3bdf28cd86530\"",
    "sessionid": "78167308557%3AT0nfhYqfPFf11X%3A7%3AAYiCfHDQ1TP92tjmX6Yc5jX7TRxP8SM37gPzZDN2dQ"
}
```

ANFORDERUNGEN:

- Verwende python-dotenv für .env-Management
- Erstelle eine Config-Klasse mit Pydantic V2
- Implementiere Validation für fehlende Keys
- Erstelle .env.example mit Beispielwerten
- Füge Error-Handling für ungültige Tokens hinzu
- Output: 3 separate Files (config.py, .env.example, usage_example.py)

```

***

## **2. 📝 Logging System Implementation**

```

Du bist ein Python Logging Expert. Konvertiere alle print() Statements in ein strukturiertes Logging-System.

KONTEXT:

- Project: Instagram Automation Tool (Selenium/undetected-chromedriver)
- Current logging: print(f"Message...") überall
- Target: Strukturiertes Logging mit File + Console Output
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

ANFORDERUNGEN:

1. Erstelle logger.py mit:
    - Colored console output (mit rich oder colorlog)
    - File-based logging in ./logs/{date}.log
    - Rotating file handler (max 5 files, 10MB each)
    - Structured format: [TIMESTAMP] LEVEL - MODULE: MESSAGE
2. Ersetze folgende print-Beispiele:

```python
print(f"Generating hashtags for topic: {seed_word}...")
print("ERROR: Still on login page. Cookies might be invalid or browser flagged.")
except Exception as e:
    print(f"Critical Automation Error: {e}")
```

3. Best practices:
    - exc_info=True für Exception stacktraces
    - Masking von sensitive data (Session IDs)
    - Performance logging für Timings

OUTPUT: logger.py + refactored_upload_example.py mit neuem Logging

```

***

## **3. 🛡️ Exception Handling Framework**

```

Du bist ein Python Error Handling Expert. Erstelle ein robustes Exception-Handling-System für Selenium automation.

PROBLEME IM AKTUELLEN CODE:

```python
except:
    pass
    
except Exception as e:
    print(f"Critical Automation Error: {e}")
    
# Sehr breite error catching ohne Kontext
```

ANFORDERUNGEN:

1. Erstelle custom exceptions.py mit:
    - InstagramAuthError (Cookie validation failed)
    - ElementNotFoundError (Selector nicht verfügbar)
    - UploadTimeoutError (Zu lange Upload-Zeit)
    - CaptionGenerationError (Hashtag scraping failed)
2. Refaktoriere diese Funktionen mit spezifischem Handling:

```python
def get_hashtags(driver, seed_word):
    try:
        # ... code ...
    except:  # ❌ TOO BROAD
        pass

def inject_cookies(driver, cookies):
    for name, value in cookies.items():
        driver.add_cookie(...)  # Kann fehlschlagen

def find_create_button(driver):
    # Mehrere Selektoren, alle können fehlschlagen
    for sel in selectors:
        try:
            # ...
        except:  # ❌ TOO BROAD
            continue
```

3. Implementiere Retry-Logik für flaky operations:
    - Exponential backoff
    - Max retry count
    - Specifische Retry-bedingungen pro Exception

OUTPUT: exceptions.py + refactored_functions.py mit proper exception handling

```

***

## **4. 📦 Dependencies Konsolidierung**

```

Du bist ein Python Packaging Expert. Konsolidiere inconsistente dependency definitions.

PROBLEM:

- requirements.txt existiert mit: undetected-chromedriver, selenium, instagrapi, pycryptodome
- pyproject.toml existiert mit: httpx, pydantic, playwright-stealth (völlig anders!)

ANFORDERUNGEN:

1. Erstelle pyproject.toml mit:
    - Alle Dependencies aus requirements.txt
    - Dev dependencies (pytest, ruff, mypy, black)
    - Optional dependencies für verschiedene use-cases
    - Version pinning strategy (>=X.Y.0, <X.Z.0)
2. Struktur muss sein:
    - [project] section mit name, version, description
    - [project.dependencies] für production
    - [project.optional-dependencies] mit dev, test, docs
    - [tool.ruff], [tool.mypy], [tool.pytest] Konfiguration
3. Erstelle requirements.txt nur für legacy-Support (referenziert pyproject.toml)
4. Berücksichtige:
    - Python 3.11+ Requirement
    - Playwright vs Selenium (nutze nur Selenium!)
    - ChromeDriver Kompatibilität

OUTPUT: pyproject.toml + requirements.txt + MIGRATION.md (wie alte requirements.txt deprecieren)

```

***

## **5. 🏗️ Code Modularisierung**

```

Du bist ein Python Architecture Expert. Refaktoriere ein monolithisches 400-Zeilen-Script in modulare, testbare Komponenten.

AKTUELLER AUFBAU:

- Datei: upload_instagram_stealth.py (12.2KB)
- Inhalt: Alles in main() function
    - Cookie injection
    - Hashtag generation
    - Element finding (mit Fallbacks)
    - File upload flow
    - Caption generation

ZIELARCHITEKTUR:

```
socializer/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── browser_manager.py       # ChromeDriver + Cookie Management
│   ├── element_locator.py       # Robuste Element-Lokalisierung mit Selectors
│   └── wait_helpers.py          # Smart Waits statt time.sleep()
├── instagram/
│   ├── __init__.py
│   ├── auth.py                  # Cookie validation + injection
│   ├── uploader.py              # Upload flow + file handling
│   ├── caption_gen.py           # Hashtag scraping + caption templates
│   ├── selectors.py             # I18n Element Selectors (DE/EN)
│   └── exceptions.py            # Instagram-specific exceptions
├── config.py                    # Pydantic settings
├── logger.py                    # Logging setup
└── main.py                      # CLI entry point
```

ANFORDERUNGEN:

1. BrowserManager class:
    - __init__(headless, user_data_dir)
    - inject_cookies(cookie_dict)
    - validate_login()
    - close()
2. InstagramUploader class:
    - upload_file(file_path, caption)
    - find_create_button() (mit allen Selektoren)
    - click_next() (robust für Crop/Filter steps)
3. CaptionGenerator class:
    - generate_hashtags(topic)
    - scrape_hashtags_from_search(seed_word)
    - scrape_hashtags_from_post()
    - generate_caption(topic, hashtags)
4. ElementSelector class:
    - Zentralisierte Selektoren für DE/EN
    - Fallback-kette pro Element
    - Returns (By, locator) tuple

OUTPUT: Alle 8 Module mit vollständigen Implementierungen + type hints + docstrings

```

***

## **6. ✅ Unit Tests (pytest)**

```

Du bist ein Python Test Expert mit pytest Spezialität. Schreibe comprehensive unit tests.

ANFORDERUNGEN:

1. Test file structure:

```
tests/
├── __init__.py
├── conftest.py              # Fixtures
├── test_browser_manager.py
├── test_instagram_auth.py
├── test_caption_generator.py
├── test_element_locator.py
└── test_uploader_integration.py
```

2. conftest.py muss haben:
    - @pytest.fixture mock_driver (MagicMock selenium webdriver)
    - @pytest.fixture instagram_config (Sample credentials)
    - @pytest.fixture temp_image (PIL Image in tmpdir)
    - @pytest.fixture caplog (für Logger testing)
3. Test-Beispiele zum Schreiben:
    - test_inject_cookies_success()
    - test_inject_cookies_with_url_encoded_values()
    - test_validate_login_checks_current_url()
    - test_find_create_button_with_multiple_fallbacks()
    - test_extract_hashtags_with_unicode()
    - test_caption_generation_with_templates()
    - test_upload_file_not_found_fallback() \# Der smart extension check
    - test_element_wait_timeout()
4. Nutze:
    - @pytest.mark.parametrize für multiple inputs
    - unittest.mock.patch für external calls
    - pytest-mock für bessere mocks
    - fixtures für setup/teardown

OUTPUT: Alle Test-Files mit 80%+ code coverage

```

***

## **7. 🐳 Docker & Docker-Compose**

```

Du bist ein DevOps Expert. Erstelle Production-Ready Docker Setup.

ANFORDERUNGEN:

1. Dockerfile für Main App:
    - Base: python:3.11-slim
    - Installiere system deps für Chromium
    - Copy pyproject.toml + source code
    - Health check for running worker
    - Non-root user
    - Multi-stage build wenn möglich
2. docker-compose.yml mit:
    - socializer-worker service (Main automation)
    - admin-panel service (aus Socializer-Admin folder)
    - postgres service (für Zukunft, statt SQLite)
    - Environment variables aus .env
    - Volume mounts für logs, data, uploads
    - Health checks
    - Networking
3. .dockerignore:
    - venv, __pycache__, .pytest_cache
    - .git, .env (Secrets!)
    - logs, data (runtime volumes)
4. Production-ready features:
    - Resource limits (memory, CPU)
    - Restart policy
    - Logging driver
    - Healthchecks

OUTPUT: Dockerfile + docker-compose.yml + .dockerignore + docker-compose.prod.yml

```

***

## **8. 🚀 GitHub Actions CI/CD Pipeline**

```

Du bist ein CI/CD Expert. Erstelle GitHub Actions Workflows für automatisierte Testing + Linting.

ANFORDERUNGEN:

1. .github/workflows/test.yml:
    - Trigger: on [push, pull_request]
    - Matrix: Python 3.11, 3.12
    - Steps:
a) Checkout code
b) Setup Python
c) Install deps (mit caching!)
d) Ruff linting (check + format)
e) mypy type checking
f) pytest mit --cov
g) Upload coverage zu codecov
h) Comment PR mit coverage report
2. .github/workflows/build.yml:
    - Build Docker image
    - Tag with git SHA
    - Push zu Docker Hub/GHCR
    - Nur wenn tests pass
3. .github/workflows/security.yml:
    - Trivy image scan
    - Bandit für code security
    - Dependency check (pip-audit)
    - Secret scanning
4. .github/workflows/deploy.yml:
    - Triggered by release tags
    - Build + push Docker image
    - Deploy zu... (Cloud Provider?)
    - Health check nach deploy

OUTPUT: 4 Workflow files mit besten Practices

```

***

## **9. 🎯 Regex für Unicode Hashtags**

```

Du bist ein Regex Expert. Verbessere das Hashtag-Extraction für internationalisierung.

AKTUELLER CODE:

```python
found_tags = re.findall(r"#\w+", caption_el.text)
```

PROBLEME:

- \w matched nur ASCII [a-zA-Z0-9_]
- Keine deutschen Umlaute (ä, ö, ü)
- Keine andere Sprachen (kyrillisch, CJK, etc)
- Keine Längenbeschränkung

ANFORDERUNGEN:

1. Erstelle Funktion extract_hashtags() mit:
    - Unicode-support (international characters)
    - Min length: 2 chars (zu kurz = nicht valide)
    - Max length: 30 chars (Instagram limit)
    - Keine Duplicates
    - Limit zu 15 tags
    - Type hints + docstring
2. Test-Fälle die du abdecken musst:
    - "\#python" -> ["\#python"]
    - "\#café \#naïve \#über" -> ["\#café", "\#naïve", "\#über"]
    - "\#привет \#مرحبا" -> Kyrillisch + Arabisch
    - "\# no space" -> [] (skip invalid)
    - "\#a \#ab \#abc" -> ["\#ab", "\#abc"] (min 2)
    - "\#thisisaverylonghashtag12345678901" -> truncate to 30
    - "duptest \#tag \#tag \#tag" -> ["\#tag"] (unique)
3. Bonus: Erstelle HashtagValidator class:
    - validate_single_tag(tag: str) -> bool
    - extract_and_validate(text: str) -> List[str]
    - stats about extracted tags

OUTPUT: utils/hashtag_extractor.py + test_hashtag_extractor.py

```

***

## **10. ⏱️ Smart Wait System (ersetze time.sleep)**

```

Du bist ein Selenium Expert. Erstelle ein Smart Wait System das robuster ist als time.sleep().

PROBLEM:

```python
time.sleep(5)  # Was wenn Element nach 2s ready ist? Unnötige 3s Wartezeit!
time.sleep(10) # Was wenn Network langsam ist und es dauert 12s? Timeout!
```

ANFORDERUNGEN:

1. WaitManager class mit:
    - wait_for_element(locator, timeout=15) -> WebElement or None
    - wait_for_clickable(locator, timeout=10) -> WebElement or None
    - wait_for_url_change(old_url, timeout=15) -> bool
    - wait_for_element_invisible(locator, timeout=10) -> bool
    - smart_delay(action_type) -> None (z.B. nach Click 100-500ms statt fixe 5s)
2. Smart delays basierend auf action:
    - After file input: 2-3s (Browser muss file processor starten)
    - After click button: 0.5-1.5s (Standard animation)
    - After text input: 0.3-0.8s (Minimal)
    - After page load: 3-5s (Content rendering)
    - Between requests: 500ms - 2s (Anti-detection)
3. Implementiere:
    - Exponential backoff für retries
    - Jitter für anti-detection
    - Adaptive waits basierend auf past timing
    - Logging von actual wait times
4. Usage Beispiel:

```python
waiter = WaitManager(driver, logger)
next_btn = waiter.wait_for_clickable((By.XPATH, "//button[text()='Next']"))
if next_btn:
    next_btn.click()
    waiter.smart_delay("button_click")
```


OUTPUT: core/wait_helpers.py + test_wait_helpers.py

```

***

## **🎬 Verwendungsanleitung:**

1. **Kopiere einen Prompt komplett** (alles von ``` bis ```)
2. **Paste in Claude/ChatGPT/Qwen**
3. **Output kopieren** und in dein Project speichern
4. **Testen** mit `pytest` oder `python -m`

**Empfelte Reihenfolge:**
1. Prompts #1 + #2 (Security + Logging) - **diese Woche**
2. Prompts #3 + #4 (Exception Handling + Dependencies) - **parallel**
3. Prompts #5 + #6 (Modularisierung + Tests)
4. Prompts #7 + #8 (Docker + CI/CD)
5. Prompts #9 + #10 (Optional optimizations)

Brauchst du noch **spezifischere Prompts** für dein Setup?```

