"""
Simple poller that reads queued jobs from the Socializer API (SQLite backend)
and invokes the stealth IG uploader for each job.

Assumptions:
- API base: http://localhost:8001 (override via API_BASE env)
- DB path: socializer.sqlite in repo root (override via SOCIALIZER_DB env)
- Media file: content/test_video.mp4 (override via MEDIA_FILE env)
- Cookies: ig_session/cookies.json (override via COOKIES_PATH env)
- Headless upload by default (set HEADLESS=false to watch the flow)

This does NOT fetch per-pack media; it uses a fallback media file for demo/testing.
Extend `select_media_for_job` if you want per-pack media mapping.
"""
from __future__ import annotations

import os
import time
import subprocess
import sys
import requests
from pathlib import Path
from datetime import datetime

# Optional: load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[1]

API_BASE = os.getenv("API_BASE", "http://localhost:8001")
DB_PATH = os.getenv("SOCIALIZER_DB", str(REPO_ROOT / "socializer.sqlite"))
MEDIA_FILE = Path(os.getenv("MEDIA_FILE", str(REPO_ROOT / "content" / "test_video.mp4")))
COOKIES_PATH = Path(os.getenv("COOKIES_PATH", str(REPO_ROOT / "ig_session" / "cookies.json")))
HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))
LOG_DIR = Path(os.getenv("IG_UPLOAD_LOG_DIR", "/tmp/ig_upload_logs"))

PYTHON_BIN = Path(sys.executable)
UPLOADER_SCRIPT = REPO_ROOT / "scripts" / "ig_autonomous_upload.py"

def fetch_jobs(status: str = "queued") -> list[dict]:
    try:
        resp = requests.get(f"{API_BASE}/jobs", params={"status": status}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[poller] Failed to fetch jobs: {e}")
        return []

def fetch_content_pack(content_pack_id: str) -> dict | None:
    try:
        resp = requests.get(f"{API_BASE}/content-packs/{content_pack_id}", timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[poller] Failed to fetch content pack {content_pack_id}: {e}")
        return None

def select_media_for_job(job: dict) -> Path:
    # TODO: map per-pack media; for now fallback to a known file
    if MEDIA_FILE.exists():
        return MEDIA_FILE
    raise FileNotFoundError(f"MEDIA_FILE not found: {MEDIA_FILE}")

def caption_for_job(job: dict, pack: dict | None) -> str:
    if pack:
        return pack.get("caption_text") or pack.get("script_text") or "Socializer post"
    return "Socializer post"

def run_uploader(file_path: Path, caption: str) -> tuple[bool, str]:
    cmd = [
        str(PYTHON_BIN),
        str(UPLOADER_SCRIPT),
        "--file",
        str(file_path),
        "--caption",
        caption,
        "--cookies",
        str(COOKIES_PATH),
    ]
    if HEADLESS:
        cmd.append("--headless")
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        log_file = LOG_DIR / f"{ts}_upload.log"
        with open(log_file, "w", encoding="utf-8") as f:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            f.write((proc.stdout or "") + "\n" + (proc.stderr or ""))
        ok = proc.returncode == 0
        output = (proc.stdout or "") + "\n" + (proc.stderr or "")
        return ok, (log_file.as_posix() + "\n" + output.strip())
    except Exception as e:
        return False, str(e)

def update_job_status(job_id: str, status: str, last_error: str | None = None):
    # Use the DB helper directly
    try:
        sys.path.append(str(REPO_ROOT / "socializer-api"))
        from socializer_api import db  # type: ignore
        db.update_job_status(job_id, status, last_error=last_error, db_path=DB_PATH)
    except Exception as e:
        print(f"[poller] Failed to update job {job_id} status to {status}: {e}")

def process_job(job: dict):
    job_id = job.get("id")
    pack_id = job.get("content_pack_id")
    print(f"[poller] Processing job {job_id} for {job.get('platform')}")
    update_job_status(job_id, "running")

    pack = fetch_content_pack(pack_id) if pack_id else None
    try:
        media_path = select_media_for_job(job)
        caption = caption_for_job(job, pack)
        ok, output = run_uploader(media_path, caption)
        if ok:
            update_job_status(job_id, "posted", None)
            print(f"[poller] Job {job_id} posted.")
        else:
            update_job_status(job_id, "failed", output[:500])
            print(f"[poller] Job {job_id} failed: {output[:200]}")
    except Exception as e:
        update_job_status(job_id, "failed", str(e))
        print(f"[poller] Job {job_id} exception: {e}")

def main():
    print(f"[poller] Starting IG poller | API={API_BASE} | DB={DB_PATH}")
    while True:
        jobs = fetch_jobs(status="queued")
        if jobs:
            print(f"[poller] Found {len(jobs)} queued jobs.")
            for job in jobs:
                process_job(job)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
