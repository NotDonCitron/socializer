"""
Scheduling logic: pick slots, compute next times, and enqueue jobs.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from .. import db
from .policy import select_slot

PLATFORM_STAGGER_MINUTES = {
    "tiktok": (0, 10),
    "instagram_reels": (20, 40),
    "youtube_shorts": (40, 60),
}

ISO_FMT = "%Y-%m-%dT%H:%M:%S%z"


def parse_iso(ts: str) -> datetime:
    return datetime.strptime(ts, ISO_FMT)


def format_iso(dt: datetime) -> str:
    return dt.strftime(ISO_FMT)


def next_slot_time(now: datetime, slot_utc: str) -> datetime:
    """
    Return the next datetime on a weekday for the given slot (HH:MM, UTC).
    """
    hour, minute = map(int, slot_utc.split(":"))
    candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def next_scheduled_time(
    now_utc: datetime,
    slot_utc: str,
    platform: str,
    policy: Dict,
    rng: Optional[random.Random] = None,
    last_job_time: Optional[datetime] = None,
) -> datetime:
    rng = rng or random.Random()
    candidate = next_slot_time(now_utc, slot_utc)
    min_gap = timedelta(hours=policy.get("min_gap_hours", 18))

    if last_job_time:
        while candidate - last_job_time < min_gap:
            candidate = candidate + timedelta(days=1)
            while candidate.weekday() >= 5:
                candidate += timedelta(days=1)

    jitter = rng.randint(policy.get("jitter_min", 7), policy.get("jitter_max", 12))
    stagger_min, stagger_max = PLATFORM_STAGGER_MINUTES.get(platform, (0, 0))
    stagger = rng.randint(stagger_min, stagger_max)
    candidate = candidate + timedelta(minutes=jitter + stagger)
    return candidate


def _choose_pack_by_lane(packs: List[Dict], recent_lanes: List[str]) -> Optional[Dict]:
    if not packs:
        return None
    lane_counts = {"beginner": 0, "builder": 0}
    for lane in recent_lanes:
        if lane in lane_counts:
            lane_counts[lane] += 1
    targets = {"beginner": 0.6, "builder": 0.4}
    def score(lane: str) -> float:
        target = targets.get(lane, 0.5)
        current = lane_counts.get(lane, 0)
        total = max(1, len(recent_lanes))
        return (current / total) / target
    preferred = sorted(packs, key=lambda p: score(p.get("lane", "beginner")))[0]
    return preferred


def schedule_approved_content(
    platform: str,
    limit: int = 1,
    dry_run: bool = False,
    now_utc: Optional[datetime] = None,
    rng: Optional[random.Random] = None,
    db_path: Optional[str] = None,
) -> List[Dict]:
    rng = rng or random.Random()
    now_utc = now_utc or datetime.now(timezone.utc)
    db.init_db(db_path)
    policy = db.get_schedule_policy(db_path)
    slot_stats = db.list_slot_stats(platform, db_path)
    slot_counts = db.get_platform_slot_counts(platform, db_path)
    last_job_ts = db.get_last_job_time(platform, db_path)
    last_job_dt = parse_iso(last_job_ts) if last_job_ts else None
    packs = db.list_approved_packs_without_jobs(platform, limit=limit * 3, db_path=db_path)
    scheduled = []

    recent_jobs = db.get_recent_jobs_with_lanes(platform, db_path=db_path)
    recent_lanes = [j.get("lane") for j in recent_jobs if j.get("lane")]

    for _ in range(limit):
        if not packs:
            break
        slot = select_slot(platform, now_utc, policy, slot_stats, slot_counts, rng)
        candidate = next_scheduled_time(now_utc, slot, platform, policy, rng, last_job_dt)

        while db.get_jobs_on_date_count(platform, candidate.date().isoformat(), db_path) > 0:
            candidate = next_scheduled_time(candidate + timedelta(days=1), slot, platform, policy, rng, last_job_dt)

        pack = _choose_pack_by_lane(packs, recent_lanes) or packs[0]
        iso_ts = format_iso(candidate)
        if dry_run:
            scheduled.append({"content_pack_id": pack["id"], "slot_utc": slot, "scheduled_for_utc": iso_ts})
        else:
            job_id = db.insert_post_job(
                content_pack_id=pack["id"],
                platform=platform,
                slot_utc=slot,
                scheduled_for_utc=iso_ts,
                db_path=db_path,
            )
            scheduled.append({"id": job_id, "content_pack_id": pack["id"], "slot_utc": slot, "scheduled_for_utc": iso_ts})
            slot_counts[slot] = slot_counts.get(slot, 0) + 1
            last_job_dt = candidate
            recent_lanes.append(pack.get("lane"))
        packs = [p for p in packs if p["id"] != pack["id"]]

    return scheduled
