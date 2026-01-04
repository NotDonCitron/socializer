"""
SQLite data layer for Socializer content packs, jobs, artifacts, metrics, and scheduling.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .settings import get_settings

ISO_FMT = "%Y-%m-%dT%H:%M:%S%z"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FMT)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a SQLite connection with reliability-focused pragmas."""
    db_file = Path(db_path or get_settings().db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    # timeout helps when multiple requests hit SQLite concurrently
    conn = sqlite3.connect(db_file, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    # wait a bit instead of failing immediately with SQLITE_BUSY
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Create tables if they do not exist."""
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS source_items (
            id TEXT PRIMARY KEY,
            source_type TEXT,
            canonical_url TEXT UNIQUE,
            title TEXT,
            publisher TEXT,
            published_at TEXT,
            raw_content TEXT,
            raw_hash TEXT,
            fetched_at TEXT,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS extracts (
            id TEXT PRIMARY KEY,
            source_item_id TEXT REFERENCES source_items(id),
            key_facts_json TEXT,
            quotes_json TEXT,
            breaking_changes_json TEXT,
            who_is_affected_json TEXT,
            confidence REAL,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS content_packs (
            id TEXT PRIMARY KEY,
            source_item_id TEXT REFERENCES source_items(id),
            lane TEXT,
            format TEXT,
            hooks_json TEXT,
            script_text TEXT,
            carousel_json TEXT,
            caption_text TEXT,
            hashtags_json TEXT,
            template_asset_text TEXT,
            sources_block_text TEXT,
            risk_flags_json TEXT,
            status TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS post_jobs (
            id TEXT PRIMARY KEY,
            content_pack_id TEXT REFERENCES content_packs(id),
            platform TEXT,
            slot_utc TEXT,
            scheduled_for_utc TEXT,
            status TEXT,
            attempts INTEGER,
            last_error TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS run_artifacts (
            id TEXT PRIMARY KEY,
            post_job_id TEXT REFERENCES post_jobs(id),
            step TEXT,
            log_json TEXT,
            screenshot_path TEXT,
            html_path TEXT,
            console_path TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS metrics (
            id TEXT PRIMARY KEY,
            post_job_id TEXT REFERENCES post_jobs(id),
            collected_at TEXT,
            window TEXT,
            views INTEGER,
            likes INTEGER,
            comments INTEGER,
            shares INTEGER,
            saves INTEGER,
            reward REAL
        );
        CREATE TABLE IF NOT EXISTS schedule_policy (
            id TEXT PRIMARY KEY,
            bootstrap_weeks INTEGER DEFAULT 2,
            epsilon REAL DEFAULT 0.20,
            jitter_min INTEGER DEFAULT 7,
            jitter_max INTEGER DEFAULT 12,
            min_gap_hours INTEGER DEFAULT 18,
            slots_json TEXT DEFAULT '["13:00","19:00"]',
            enable_optional_slot INTEGER DEFAULT 0
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_schedule_policy_id ON schedule_policy(id);
        CREATE TABLE IF NOT EXISTS slot_stats (
            id TEXT PRIMARY KEY,
            platform TEXT,
            slot_utc TEXT,
            samples INTEGER DEFAULT 0,
            reward_sum REAL DEFAULT 0.0,
            reward_mean REAL DEFAULT 0.0,
            last_updated TEXT,
            UNIQUE(platform, slot_utc)
        );
        """
    )
    # ---- metrics hardening / migration-ish steps ----
    # 1) Deduplicate rows per (post_job_id, window), keep latest collected_at
    cur.execute(
        """
        DELETE FROM metrics
        WHERE rowid NOT IN (
          SELECT MIN(rowid)
          FROM metrics m
          JOIN (
            SELECT post_job_id, window, MAX(collected_at) AS max_collected
            FROM metrics
            GROUP BY post_job_id, window
          ) k
          ON m.post_job_id = k.post_job_id AND m.window = k.window AND m.collected_at = k.max_collected
          GROUP BY m.post_job_id, m.window
        )
        """
    )
    # 2) Make metric IDs deterministic so "INSERT OR IGNORE" can return the real ID
    cur.execute("UPDATE metrics SET id = post_job_id || ':' || window")
    # 3) Enforce uniqueness at DB-level (conflict target)
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_metrics_job_window ON metrics(post_job_id, window)"
    )
    conn.commit()
    conn.close()


def _rows_to_dicts(rows: Iterable[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]


# Content packs
def list_content_packs(
    status: Optional[str] = None, limit: int = 100, offset: int = 0, db_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    if status:
        cur.execute(
            "SELECT * FROM content_packs WHERE status=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (status, limit, offset),
        )
    else:
        cur.execute(
            "SELECT * FROM content_packs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
    rows = cur.fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def get_content_pack(content_pack_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM content_packs WHERE id=?", (content_pack_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def set_content_pack_status(content_pack_id: str, status: str, db_path: Optional[str] = None) -> bool:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE content_packs SET status=? WHERE id=?", (status, content_pack_id))
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated


# Jobs
def list_jobs(
    status: Optional[str] = None,
    platform: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    query = "SELECT * FROM post_jobs WHERE 1=1"
    params: List[Any] = []
    if status:
        query += " AND status=?"
        params.append(status)
    if platform:
        query += " AND platform=?"
        params.append(platform)
    query += " ORDER BY scheduled_for_utc ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def get_job(job_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM post_jobs WHERE id=?", (job_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_job_status(job_id: str, status: str, last_error: Optional[str] = None, db_path: Optional[str] = None) -> bool:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        "UPDATE post_jobs SET status=?, last_error=? WHERE id=?",
        (status, last_error, job_id),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated


def retry_job(job_id: str, db_path: Optional[str] = None) -> bool:
    """
    Move a job back to queued. Increments attempts to reflect another try.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        "UPDATE post_jobs SET status='queued', last_error=NULL, attempts=COALESCE(attempts,0)+1 WHERE id=?",
        (job_id,),
    )
    conn.commit()
    updated = cur.rowcount > 0
    conn.close()
    return updated


def record_artifact(
    job_id: str,
    step: str,
    log_json: Optional[Dict[str, Any]] = None,
    screenshot_path: Optional[str] = None,
    html_path: Optional[str] = None,
    console_path: Optional[str] = None,
    db_path: Optional[str] = None,
) -> str:
    conn = get_connection(db_path)
    cur = conn.cursor()
    artifact_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO run_artifacts (id, post_job_id, step, log_json, screenshot_path, html_path, console_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            artifact_id,
            job_id,
            step,
            json.dumps(log_json or {}),
            screenshot_path,
            html_path,
            console_path,
            utc_now_iso(),
        ),
    )
    conn.commit()
    conn.close()
    return artifact_id


def record_metrics(
    job_id: str,
    window: str,
    views: int,
    likes: int,
    comments: int,
    shares: int,
    saves: int,
    reward: float,
    db_path: Optional[str] = None,
) -> tuple[str, bool]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    metrics_id = f"{job_id}:{window}"
    cur.execute(
        """
        INSERT OR IGNORE INTO metrics (id, post_job_id, collected_at, window, views, likes, comments, shares, saves, reward)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            metrics_id,
            job_id,
            utc_now_iso(),
            window,
            views,
            likes,
            comments,
            shares,
            saves,
            reward,
        ),
    )
    inserted = (cur.rowcount == 1)
    conn.commit()
    conn.close()
    return metrics_id, inserted


def insert_content_pack(
    lane: str,
    format: str,
    status: str = "draft",
    source_item_id: Optional[str] = None,
    hooks: Optional[List[str]] = None,
    script_text: Optional[str] = None,
    carousel: Optional[List[str]] = None,
    caption_text: Optional[str] = None,
    hashtags: Optional[List[str]] = None,
    template_asset_text: Optional[str] = None,
    sources_block_text: Optional[str] = None,
    risk_flags: Optional[List[str]] = None,
    db_path: Optional[str] = None,
) -> str:
    conn = get_connection(db_path)
    cur = conn.cursor()
    pack_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO content_packs (
            id, source_item_id, lane, format, hooks_json, script_text, carousel_json,
            caption_text, hashtags_json, template_asset_text, sources_block_text,
            risk_flags_json, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pack_id,
            source_item_id,
            lane,
            format,
            json.dumps(hooks or []),
            script_text,
            json.dumps(carousel or []),
            caption_text,
            json.dumps(hashtags or []),
            template_asset_text,
            sources_block_text,
            json.dumps(risk_flags or []),
            status,
            utc_now_iso(),
        ),
    )
    conn.commit()
    conn.close()
    return pack_id


def insert_post_job(
    content_pack_id: str,
    platform: str,
    slot_utc: str,
    scheduled_for_utc: str,
    status: str = "queued",
    attempts: int = 0,
    db_path: Optional[str] = None,
) -> str:
    conn = get_connection(db_path)
    cur = conn.cursor()
    job_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO post_jobs (id, content_pack_id, platform, slot_utc, scheduled_for_utc, status, attempts, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            content_pack_id,
            platform,
            slot_utc,
            scheduled_for_utc,
            status,
            attempts,
            utc_now_iso(),
        ),
    )
    conn.commit()
    conn.close()
    return job_id


def list_approved_packs_without_jobs(platform: str, limit: int = 10, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return approved content packs not yet linked to a job.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT cp.* FROM content_packs cp
        WHERE cp.status='approved'
        AND cp.id NOT IN (SELECT content_pack_id FROM post_jobs WHERE platform=?)
        ORDER BY cp.created_at ASC
        LIMIT ?
        """,
        (platform, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def get_recent_jobs_with_lanes(platform: str, limit: int = 10, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pj.*, cp.lane FROM post_jobs pj
        LEFT JOIN content_packs cp ON cp.id = pj.content_pack_id
        WHERE pj.platform=?
        ORDER BY pj.scheduled_for_utc DESC
        LIMIT ?
        """,
        (platform, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def get_last_job_time(platform: str, db_path: Optional[str] = None) -> Optional[str]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT scheduled_for_utc FROM post_jobs WHERE platform=? ORDER BY scheduled_for_utc DESC LIMIT 1",
        (platform,),
    )
    row = cur.fetchone()
    conn.close()
    return row["scheduled_for_utc"] if row else None


def get_jobs_on_date_count(platform: str, date_iso: str, db_path: Optional[str] = None) -> int:
    """
    Count jobs for a platform on a given ISO date (YYYY-MM-DD).
    """
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) as cnt FROM post_jobs
        WHERE platform=? AND date(scheduled_for_utc)=?
        """,
        (platform, date_iso),
    )
    row = cur.fetchone()
    conn.close()
    return row["cnt"] if row else 0


def get_platform_slot_counts(platform: str, db_path: Optional[str] = None) -> Dict[str, int]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT slot_utc, COUNT(*) as cnt FROM post_jobs
        WHERE platform=?
        GROUP BY slot_utc
        """,
        (platform,),
    )
    rows = cur.fetchall()
    conn.close()
    return {row["slot_utc"]: row["cnt"] for row in rows}


# Schedule policy + stats
DEFAULT_SLOTS = ["13:00", "19:00"]


def get_schedule_policy(db_path: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM schedule_policy LIMIT 1")
    row = cur.fetchone()
    if not row:
        cur.execute(
            """
            INSERT INTO schedule_policy (id, bootstrap_weeks, epsilon, jitter_min, jitter_max, min_gap_hours, slots_json, enable_optional_slot)
            VALUES ('policy', 2, 0.20, 7, 12, 18, ?, 0)
            """,
            (json.dumps(DEFAULT_SLOTS),),
        )
        conn.commit()
        cur.execute("SELECT * FROM schedule_policy LIMIT 1")
        row = cur.fetchone()
    conn.close()
    data = dict(row)
    data["slots"] = json.loads(data.pop("slots_json") or json.dumps(DEFAULT_SLOTS))
    data["enable_optional_slot"] = bool(data.get("enable_optional_slot"))
    return data


def upsert_schedule_policy(
    *,
    bootstrap_weeks: Optional[int] = None,
    epsilon: Optional[float] = None,
    jitter_min: Optional[int] = None,
    jitter_max: Optional[int] = None,
    min_gap_hours: Optional[int] = None,
    slots: Optional[List[str]] = None,
    enable_optional_slot: Optional[bool] = None,
    db_path: Optional[str] = None,
) -> None:
    existing = get_schedule_policy(db_path)
    payload = {
        "bootstrap_weeks": bootstrap_weeks if bootstrap_weeks is not None else existing["bootstrap_weeks"],
        "epsilon": epsilon if epsilon is not None else existing["epsilon"],
        "jitter_min": jitter_min if jitter_min is not None else existing["jitter_min"],
        "jitter_max": jitter_max if jitter_max is not None else existing["jitter_max"],
        "min_gap_hours": min_gap_hours if min_gap_hours is not None else existing["min_gap_hours"],
        "slots": slots if slots is not None else existing["slots"],
        "enable_optional_slot": existing["enable_optional_slot"] if enable_optional_slot is None else enable_optional_slot,
    }
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO schedule_policy (id, bootstrap_weeks, epsilon, jitter_min, jitter_max, min_gap_hours, slots_json, enable_optional_slot)
        VALUES ('policy', ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            bootstrap_weeks=excluded.bootstrap_weeks,
            epsilon=excluded.epsilon,
            jitter_min=excluded.jitter_min,
            jitter_max=excluded.jitter_max,
            min_gap_hours=excluded.min_gap_hours,
            slots_json=excluded.slots_json,
            enable_optional_slot=excluded.enable_optional_slot
        """,
        (
            payload["bootstrap_weeks"],
            payload["epsilon"],
            payload["jitter_min"],
            payload["jitter_max"],
            payload["min_gap_hours"],
            json.dumps(payload["slots"]),
            1 if payload["enable_optional_slot"] else 0,
        ),
    )
    conn.commit()
    conn.close()


def list_slot_stats(platform: str, db_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM slot_stats WHERE platform=?",
        (platform,),
    )
    rows = cur.fetchall()
    conn.close()
    return {row["slot_utc"]: dict(row) for row in rows}


def update_slot_stats(platform: str, slot_utc: str, reward: float, db_path: Optional[str] = None) -> None:
    conn = get_connection(db_path)
    cur = conn.cursor()
    now = utc_now_iso()
    cur.execute(
        """
        INSERT INTO slot_stats (id, platform, slot_utc, samples, reward_sum, reward_mean, last_updated)
        VALUES (?, ?, ?, 1, ?, ?, ?)
        ON CONFLICT(platform, slot_utc) DO UPDATE SET
            samples = slot_stats.samples + 1,
            reward_sum = slot_stats.reward_sum + excluded.reward_sum,
            reward_mean = (slot_stats.reward_sum + excluded.reward_sum) / (slot_stats.samples + 1),
            last_updated = excluded.last_updated
        """,
        (str(uuid.uuid4()), platform, slot_utc, reward, reward, now),
    )
    conn.commit()
    conn.close()

