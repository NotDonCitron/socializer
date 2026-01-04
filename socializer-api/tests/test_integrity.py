import sys
import os
import sqlite3
import pytest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from socializer_api import db
from fastapi.testclient import TestClient

def make_client(tmp_path: Path) -> TestClient:
    os.environ["SOCIALIZER_DB"] = str(tmp_path / "api.sqlite")
    from socializer_api import app as app_module
    # We don't reload here to avoid issues if already imported, 
    # but init_db is called in the test
    app_module.db.init_db(os.environ["SOCIALIZER_DB"])
    return TestClient(app_module.app)

def test_metrics_idempotency(tmp_path):
    db_path = str(tmp_path / "metrics_idempotency.sqlite")
    os.environ["SOCIALIZER_DB"] = db_path
    from socializer_api import app as app_module
    app_module.db.init_db(db_path)
    client = TestClient(app_module.app)
    
    pack_id = db.insert_content_pack(lane="builder", format="script", status="approved", db_path=db_path)
    job_id = db.insert_post_job(
        content_pack_id=pack_id,
        platform="tiktok",
        slot_utc="19:00",
        scheduled_for_utc="2024-01-02T19:00:00+0000",
        db_path=db_path,
    )

    # First ingestion
    payload = {"window": "60m", "views": 100, "likes": 5, "comments": 1, "shares": 1, "saves": 1}
    res1 = client.post(f"/jobs/{job_id}/metrics", json=payload)
    assert res1.status_code == 200
    
    # Second ingestion (same window)
    res2 = client.post(f"/jobs/{job_id}/metrics", json=payload)
    assert res2.status_code == 200
    assert res2.json().get("status") == "already_exists"
    
    # Verify DB only has 1 record
    existing = [m for m in app_module.list_metrics(job_id, db_path=db_path) if m["window"] == "60m"]
    assert len(existing) == 1
    
    # Verify slot stats only updated once
    stats = db.list_slot_stats("tiktok", db_path=db_path)
    assert stats["19:00"]["samples"] == 1

def test_schedule_integrity_unique_index(tmp_path):
    db_path = tmp_path / "integrity.sqlite"
    db.init_db(db_path)
    pack_id = db.insert_content_pack(lane="beginner", format="script", status="approved", db_path=db_path)
    
    # Insert first job
    db.insert_post_job(pack_id, "tiktok", "13:00", "2024-01-01T13:00:00+0000", status="queued", db_path=db_path)
    
    # Try to insert second job for same pack/platform while first is queued
    with pytest.raises(sqlite3.IntegrityError):
        # We need to use a connection that has the index
        conn = db.get_connection(db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO post_jobs (id, content_pack_id, platform, status) VALUES ('job2', ?, 'tiktok', 'queued')",
            (pack_id,)
        )
        conn.commit()

def test_list_approved_packs_ignores_failed_jobs(tmp_path):
    db_path = tmp_path / "list_fail.sqlite"
    db.init_db(db_path)
    pack_id = db.insert_content_pack(lane="beginner", format="script", status="approved", db_path=db_path)
    
    # Initially pack is returned
    packs = db.list_approved_packs_without_jobs("tiktok", db_path=db_path)
    assert len(packs) == 1
    
    # Create a job that failed
    db.insert_post_job(pack_id, "tiktok", "13:00", "2024-01-01T13:00:00+0000", status="failed", db_path=db_path)
    
    # Pack should STILL be returned because only queued/running block it
    packs = db.list_approved_packs_without_jobs("tiktok", db_path=db_path)
    assert len(packs) == 1
    
    # Now create a queued job
    db.insert_post_job(pack_id, "tiktok", "19:00", "2024-01-01T19:00:00+0000", status="queued", db_path=db_path)
    
    # Now pack should be hidden
    packs = db.list_approved_packs_without_jobs("tiktok", db_path=db_path)
    assert len(packs) == 0
