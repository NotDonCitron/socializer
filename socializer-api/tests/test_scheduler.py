import sys
from datetime import datetime, timezone
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from socializer_api.scheduler import policy
from socializer_api.scheduler.schedule import next_scheduled_time, schedule_approved_content
from socializer_api import db


def test_policy_rotation_and_bandit():
    rng = random.Random(0)
    policy_cfg = {"slots": ["13:00", "19:00"], "bootstrap_weeks": 2, "epsilon": 0.2}
    slot = policy.select_slot(
        "tiktok",
        datetime.now(timezone.utc),
        policy_cfg,
        slot_stats={},
        slot_counts={"13:00": 2, "19:00": 0},
        rng=rng,
    )
    assert slot == "19:00"
    slot = policy.select_slot(
        "tiktok",
        datetime.now(timezone.utc),
        {**policy_cfg, "bootstrap_weeks": 0, "epsilon": 0.0},
        slot_stats={"13:00": {"samples": 5, "reward_mean": 10}, "19:00": {"samples": 5, "reward_mean": 50}},
        slot_counts={"13:00": 20, "19:00": 20},
        rng=random.Random(1),
    )
    assert slot == "19:00"


def test_next_scheduled_time_respects_gap():
    now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    last = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    scheduled = next_scheduled_time(
        now,
        "13:00",
        "tiktok",
        {"min_gap_hours": 18, "jitter_min": 7, "jitter_max": 7},
        rng=random.Random(0),
        last_job_time=last,
    )
    assert scheduled.date().isoformat() == "2024-01-02"


def test_schedule_integration(tmp_path):
    db_path = tmp_path / "sched.sqlite"
    db.init_db(db_path)
    db.insert_content_pack(lane="beginner", format="script", status="approved", db_path=db_path)
    jobs = schedule_approved_content(
        platform="tiktok",
        limit=1,
        dry_run=False,
        now_utc=datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc),
        rng=random.Random(0),
        db_path=db_path,
    )
    assert len(jobs) == 1
    job = db.get_job(jobs[0]["id"], db_path=db_path)
    assert job["slot_utc"] in ["13:00", "19:00"]
    assert job["content_pack_id"]
