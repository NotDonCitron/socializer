import os
import sys
from importlib import reload
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from socializer_api import db  # noqa: E402


def make_client(tmp_path: Path) -> TestClient:
    os.environ["SOCIALIZER_DB"] = str(tmp_path / "api.sqlite")
    reload(db)
    from socializer_api import app as app_module  # type: ignore

    db.init_db(os.environ["SOCIALIZER_DB"])
    reload(app_module)
    app_module.db.init_db(os.environ["SOCIALIZER_DB"])
    client = TestClient(app_module.app)
    app_module.db.init_db(os.environ["SOCIALIZER_DB"])
    return client


def test_approve_and_retry_flow(tmp_path):
    client = make_client(tmp_path)
    db_path = os.environ["SOCIALIZER_DB"]
    pack_id = db.insert_content_pack(lane="beginner", format="script", status="draft", db_path=db_path)

    res = client.post(f"/content-packs/{pack_id}/approve")
    assert res.status_code == 200
    assert db.get_content_pack(pack_id, db_path=db_path)["status"] == "approved"

    job_id = db.insert_post_job(
        content_pack_id=pack_id,
        platform="tiktok",
        slot_utc="13:00",
        scheduled_for_utc="2024-01-01T13:00:00+0000",
        db_path=db_path,
    )
    res = client.post(f"/jobs/{job_id}/retry")
    assert res.status_code == 200
    assert db.get_job(job_id, db_path=db_path)["status"] == "queued"


def test_metrics_updates_slot_stats(tmp_path):
    client = make_client(tmp_path)
    db_path = os.environ["SOCIALIZER_DB"]
    pack_id = db.insert_content_pack(lane="builder", format="script", status="approved", db_path=db_path)
    job_id = db.insert_post_job(
        content_pack_id=pack_id,
        platform="tiktok",
        slot_utc="19:00",
        scheduled_for_utc="2024-01-02T19:00:00+0000",
        db_path=db_path,
    )

    res = client.post(
        f"/jobs/{job_id}/metrics",
        json={"window": "60m", "views": 120, "likes": 5, "comments": 1, "shares": 2, "saves": 3},
    )
    assert res.status_code == 200
    stats = db.list_slot_stats("tiktok", db_path=db_path)
    assert stats["19:00"]["samples"] >= 1
    assert stats["19:00"]["reward_mean"] == 120.0
