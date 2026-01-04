import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from socializer_api import db


def test_init_and_content_pack_roundtrip(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db.init_db(db_path)

    pack_id = db.insert_content_pack(
        lane="beginner",
        format="script",
        status="draft",
        hooks=["h1"],
        caption_text="cap",
        db_path=db_path,
    )
    packs = db.list_content_packs(db_path=db_path)
    assert len(packs) == 1
    assert packs[0]["id"] == pack_id

    ok = db.set_content_pack_status(pack_id, "approved", db_path=db_path)
    assert ok
    pack = db.get_content_pack(pack_id, db_path=db_path)
    assert pack["status"] == "approved"


def test_jobs_metrics_and_slot_stats(tmp_path):
    db_path = tmp_path / "test.sqlite"
    db.init_db(db_path)
    pack_id = db.insert_content_pack(lane="builder", format="script", status="approved", db_path=db_path)
    job_id = db.insert_post_job(
        content_pack_id=pack_id,
        platform="tiktok",
        slot_utc="13:00",
        scheduled_for_utc="2024-01-01T13:00:00+0000",
        db_path=db_path,
    )
    jobs = db.list_jobs(db_path=db_path)
    assert jobs[0]["id"] == job_id

    artifact_id = db.record_artifact(job_id, step="upload", log_json={"ok": True}, db_path=db_path)
    assert artifact_id

    metric_id = db.record_metrics(
        job_id=job_id,
        window="60m",
        views=100,
        likes=10,
        comments=1,
        shares=2,
        saves=3,
        reward=100.0,
        db_path=db_path,
    )
    assert metric_id
    db.update_slot_stats("tiktok", "13:00", 100.0, db_path=db_path)
    stats = db.list_slot_stats("tiktok", db_path=db_path)
    assert stats["13:00"]["samples"] == 1
    assert stats["13:00"]["reward_mean"] == 100.0
