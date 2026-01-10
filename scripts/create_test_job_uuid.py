import os
import sys

# HACK: add socializer-api to path
sys.path.append(os.path.join(os.getcwd(), "socializer-api"))

from socializer_api import db

def create_job():
    db_path = os.path.join(os.getcwd(), "socializer.sqlite")
    
    # 1. Get an approved content pack
    packs = db.list_content_packs(status="approved", db_path=db_path)
    if not packs:
        print("No approved content packs found. Run worker once to ingest.")
        return

    pack_id = packs[0]['id']
    
    # 2. Insert job
    job_id = db.insert_post_job(
        content_pack_id=pack_id,
        platform="instagram",
        slot_utc="12:00",
        scheduled_for_utc=db.utc_now_iso(),
        status="queued",
        db_path=db_path
    )
    print(f"Created Job {job_id} for Content Pack {pack_id}")

if __name__ == "__main__":
    create_job()
