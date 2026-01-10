import os
import sys
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.append(os.path.join(os.getcwd(), "socializer-api"))

from app.models import PostJob, JobStatus, ContentPack, Platform, PackStatus

# Set DB path correctly
db_path = os.path.join(os.getcwd(), "socializer.sqlite")
os.environ["SOCIALIZER_DB"] = db_path
DATABASE_URL = f"sqlite:///{db_path}"

from app.database import Base

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def queue_job():
    db = SessionLocal()
    try:
        # Get an approved content pack
        pack = db.query(ContentPack).filter(ContentPack.status == PackStatus.approved).first()
        if not pack:
            print("No approved content packs found! Run ingestion first.")
            return

        print(f"Queueing job for Content Pack ID {pack.id}...")
        
        job = PostJob(
            content_pack_id=pack.id,
            platform=Platform.instagram,
            status=JobStatus.queued,
            scheduled_for_utc=datetime.utcnow() - timedelta(minutes=1), # Ready now
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        print(f"Job {job.id} queued successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    queue_job()
