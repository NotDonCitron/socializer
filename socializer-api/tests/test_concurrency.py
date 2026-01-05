import os
import sys
import concurrent.futures
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from socializer_api import db

def make_client(tmp_path: Path) -> TestClient:
    db_path = str(tmp_path / "concurrency.sqlite")
    os.environ["SOCIALIZER_DB"] = db_path
    from socializer_api import app as app_module
    app_module.db.init_db(db_path)
    return TestClient(app_module.app)

def test_concurrent_metrics_ingestion(tmp_path):
    client = make_client(tmp_path)
    db_path = os.environ["SOCIALIZER_DB"]
    
    # Setup job
    pack_id = db.insert_content_pack(lane="concurrency", format="script", status="approved", db_path=db_path)
    job_id = db.insert_post_job(
        content_pack_id=pack_id,
        platform="instagram_reels",
        slot_utc="13:00",
        scheduled_for_utc="2024-01-01T13:00:00+0000",
        db_path=db_path,
    )

    payload = {"window": "60m", "views": 500, "likes": 20, "comments": 5, "shares": 10, "saves": 15}
    
    # Simulate 5 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(client.post, f"/jobs/{job_id}/metrics", json=payload) for _ in range(5)]
        results = [f.result() for f in futures]

    # Exactly one should have been a success (new insert) and the others "already_exists"
    successes = [r for r in results if r.status_code == 200 and r.json().get("status") != "already_exists"]
    already_exists = [r for r in results if r.status_code == 200 and r.json().get("status") == "already_exists"]
    
    assert len(successes) == 1
    assert len(already_exists) == 4
    
    # Verify slot stats updated exactly once
    stats = db.list_slot_stats("instagram_reels", db_path=db_path)
    assert stats["13:00"]["samples"] == 1
    assert stats["13:00"]["reward_mean"] == 500.0
