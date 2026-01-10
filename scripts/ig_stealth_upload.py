"""
Minimal stealth uploader scaffold:
- Uses undetected-chromedriver
- Injects cookies from ig_session/cookies.json (or --cookies)
- Confirms login and prints status
- Stops before upload flow (safe to extend)

Usage:
    python scripts/ig_stealth_upload.py --file /path/to/video.mp4 --caption "Your caption"
    # Optional: --cookies ig_session/cookies.json --headless
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def load_cookies(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Cookies file not found: {path}")
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError("Cookies file must contain a list of cookie dicts")
    return data


def inject_cookies(driver, cookies: list[dict], domain=".instagram.com"):
    driver.get("https://www.instagram.com/")
    time.sleep(3)
    for c in cookies:
        name = c.get("name")
        value = c.get("value")
        if not name or value is None:
            continue
        cookie = {
            "name": name,
            "value": value,
            "domain": c.get("domain", domain),
            "path": c.get("path", "/"),
        }
        if c.get("expiry"):
            cookie["expiry"] = c["expiry"]
        if c.get("secure") is not None:
            cookie["secure"] = bool(c["secure"])
        driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(3)


def is_logged_in(driver) -> bool:
    # If still on login page -> not logged in
    if "accounts/login" in driver.current_url:
        return False
    # Look for the search box or profile menu as a proxy for logged-in state
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search'] | //input[@placeholder='Suchen'] | //a[contains(@href, '/direct/inbox/')]"))
        )
        return True
    except Exception:
        return False


def click_any(driver, selectors: list[str], timeout: int = 15) -> bool:
    """Try a list of XPath selectors and click the first clickable match."""
    for sel in selectors:
        try:
            el = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, sel))
            )
            driver.execute_script("arguments[0].click();", el)
            return True
        except Exception:
            continue
    return False


def wait_for_any(driver, selectors: list[str], timeout: int = 15):
    """Return the first element that appears from selectors, or None."""
    for sel in selectors:
        try:
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, sel))
            )
        except Exception:
            continue
    return None


def log_step(driver, log_dir: Path, name: str):
    """Save a screenshot per step for later debugging."""
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        driver.save_screenshot(str(log_dir / f"{ts}_{name}.png"))
    except Exception:
        pass


def handle_popups(driver):
    # Dismiss notifications prompt / cookie nags if they appear
    click_any(
        driver,
        [
            "//button[contains(text(), 'Not Now')]",
            "//button[contains(text(), 'Jetzt nicht')]",
            "//button[contains(text(), 'Allow all cookies')]",
            "//button[contains(text(), 'Alle zulassen')]",
            "//button[text()='OK' and contains(., 'messaging') or text()='OK']",  # new messenger UI prompt
            "//div[@role='dialog']//button[text()='OK']",
            "//div[@role='dialog']//button[contains(text(),'Got it')]",
        ],
        timeout=5,
    )


def upload_reel(driver, media_path: Path, caption: str, log_dir: Path) -> bool:
    """Attempt a simple web upload flow for a Reel/post."""
    log_step(driver, log_dir, "start_home")
    handle_popups(driver)
    print("▶️ Öffne Upload-Dialog...")
    if not click_any(
        driver,
        [
            "//svg[@aria-label='New post']/ancestor::button",
            "//svg[@aria-label='Neuer Beitrag']/ancestor::button",
            "//svg[@aria-label='Erstellen']/ancestor::button",
            "//svg[@aria-label='New post']/ancestor::a",
            "//svg[@aria-label='Neuer Beitrag']/ancestor::a",
            "//svg[@aria-label='Erstellen']/ancestor::a",
            "//a[.//svg[@aria-label='New post']]",
            "//div[@role='menuitem' and .//span[contains(text(),'Create')]]",
            "//span[contains(text(),'Create')]/ancestor::button",
            "//span[contains(text(),'Erstellen')]/ancestor::button",
            "//span[contains(text(),'Create')]/ancestor::a",
            "//nav//span[text()='Create']/ancestor::*[self::button or self::a or self::div]",
            "//nav//span[text()='Erstellen']/ancestor::*[self::button or self::a or self::div]",
            "//button[@aria-label='Create']",
            "//button[@aria-label='Erstellen']",
            "//div[@role='button' and .//span[text()='Create']]",
            "//div[@role='button' and .//span[text()='Erstellen']]",
            "//a[@href='/create/select/']",
        ],
        timeout=15,
    ):
        print("⚠️ Konnte den 'Create/New post'-Button nicht finden, versuche Direkt-URL...")
        try:
            driver.get("https://www.instagram.com/create/select/")
            time.sleep(3)
        except Exception:
            pass
        log_step(driver, log_dir, "create_fallback")

    file_input = wait_for_any(
        driver,
        [
            "//input[@type='file' and contains(@accept,'video')]",
            "//input[@type='file' and contains(@accept,'image')]",
            "//input[@type='file']",
        ],
        timeout=25,
    )
    if not file_input:
        print("❌ Kein Datei-Upload-Feld gefunden.")
        log_step(driver, log_dir, "no_file_input")
        return False

    file_input.send_keys(str(media_path))
    print(f"📤 Datei gewählt: {media_path}")
    log_step(driver, log_dir, "file_selected")

    # Zwei mal Weiter/Next (Trim, Details)
    for step in ["Weiter/Next 1", "Weiter/Next 2"]:
        if not click_any(
            driver,
            [
                "//div[text()='Next']/parent::button",
                "//span[text()='Next']/ancestor::button",
                "//div[text()='Weiter']/parent::button",
                "//span[text()='Weiter']/ancestor::button",
            ],
            timeout=20,
        ):
            print(f"⚠️ {step}: kein Next-Button gefunden, versuche weiter.")
        else:
            print(f"✅ {step} geklickt.")
        log_step(driver, log_dir, f"after_{step.replace(' ', '_').lower()}")
        time.sleep(2)

    # Caption setzen
    caption_box = wait_for_any(
        driver,
        [
            "//textarea[@aria-label='Write a caption...']",
            "//textarea[@aria-label='Schreibe eine Bildunterschrift...']",
            "//label//textarea",
        ],
        timeout=15,
    )
    if caption_box:
        caption_box.clear()
        caption_box.send_keys(caption)
        print(f"📝 Caption gesetzt ({len(caption)} Zeichen).")
    else:
        print("⚠️ Caption-Feld nicht gefunden, fahre fort ohne Caption.")
    log_step(driver, log_dir, "after_caption")

    # Teilen/Share
    if not click_any(
        driver,
        [
            "//div[text()='Share']/parent::button",
            "//span[text()='Share']/ancestor::button",
            "//div[text()='Teilen']/parent::button",
            "//span[text()='Teilen']/ancestor::button",
            "//button[@type='submit' and .//div[contains(text(),'Share')]]",
        ],
        timeout=15,
    ):
        print("❌ Share/Teilen-Button nicht gefunden.")
        log_step(driver, log_dir, "no_share")
        return False
    print("🚀 Share geklickt, warte auf Bestätigung...")
    log_step(driver, log_dir, "after_share_click")

    # Bestätigung abwarten
    success_el = wait_for_any(
        driver,
        [
            "//span[contains(text(),'shared')]",
            "//span[contains(text(),'geteilt')]",
            "//div[contains(text(),'Your reel has been shared')]",
            "//div[contains(text(),'wurde geteilt')]",
            "//span[contains(text(),'posted')]",
            "//span[contains(text(),'gepostet')]",
        ],
        timeout=45,
    )
    if success_el:
        print("✅ Upload laut UI abgeschlossen.")
        return True
    print("⚠️ Keine Bestätigungs-Meldung erkannt; prüfe manuell.")
    log_step(driver, log_dir, "no_success")
    return True


def main():
    parser = argparse.ArgumentParser(description="Stealth IG uploader (login via cookies)")
    parser.add_argument("--file", required=True, help="Path to video/image file")
    parser.add_argument("--caption", default="", help="Caption text")
    parser.add_argument("--cookies", default="ig_session/cookies.json", help="Path to cookies.json")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    args = parser.parse_args()

    media_path = Path(args.file).resolve()
    if not media_path.exists():
        print(f"❌ File not found: {media_path}")
        sys.exit(1)

    cookies_path = Path(args.cookies)
    try:
        cookies = load_cookies(cookies_path)
    except Exception as e:
        print(f"❌ Failed to load cookies: {e}")
        sys.exit(1)

    opts = uc.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    if args.headless:
        opts.add_argument("--headless=new")
    driver = uc.Chrome(options=opts)
    driver.maximize_window()

    try:
        inject_cookies(driver, cookies)
        handle_popups(driver)
        if not is_logged_in(driver):
            print("❌ Login failed (still on login page). Cookies may be invalid.")
            sys.exit(1)
        print("✅ Login confirmed via cookies.")
        print(f"📄 Upload-Datei: {media_path}")
        print(f"📝 Caption (len={len(args.caption)}): {args.caption}")
        log_dir = Path(os.getenv("IG_UPLOAD_LOG_DIR", "/tmp/ig_upload_logs"))
        ok = upload_reel(driver, media_path, args.caption, log_dir)
        if not ok:
            sys.exit(2)
        time.sleep(3)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
