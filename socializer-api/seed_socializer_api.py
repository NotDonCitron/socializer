"""
Seed script for the socializer_api SQLite database.

Creates a small set of content packs (approved + draft) and a couple of jobs
so the admin panel can show data immediately.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from socializer_api import db
from socializer_api.settings import get_settings


def _count_content_packs(db_path: str) -> int:
    conn = db.get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM content_packs")
    count = int(cur.fetchone()[0])
    conn.close()
    return count


def seed() -> None:
    db_path = os.getenv("SOCIALIZER_DB", get_settings().db_path)
    db.init_db(db_path)

    if _count_content_packs(db_path) > 0:
        print("Database already has content packs. Skipping seed.")
        return

    now = datetime.now(timezone.utc)
    pack_ids: list[str] = []

    for i in range(5):
        status = "approved" if i < 3 else "draft"
        caption = f"Instagram pack {i + 1}: launch-ready Reel idea."
        script_text = f"Short script for pack {i + 1}."
        hashtags = ["instagram", "reels", "socializer"]
        pack_id = db.insert_content_pack(
            lane="instagram",
            format="reel",
            status=status,
            caption_text=caption,
            script_text=script_text,
            hashtags=hashtags,
            db_path=db_path,
        )
        pack_ids.append(pack_id)

    # Create a couple of queued jobs for the first approved packs
    for offset, pack_id in enumerate(pack_ids[:2]):
        scheduled_for = now + timedelta(hours=2 + offset)
        slot_utc = scheduled_for.strftime("%H:%M")
        db.insert_post_job(
            content_pack_id=pack_id,
            platform="instagram_reels",
            slot_utc=slot_utc,
            scheduled_for_utc=scheduled_for.strftime(db.ISO_FMT),
            status="queued",
            attempts=0,
            db_path=db_path,
        )

    print("Seed complete: 5 content packs, 2 queued jobs.")


if __name__ == "__main__":
    seed()
