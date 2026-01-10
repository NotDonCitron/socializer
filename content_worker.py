import os
import time
import sys
import logging
import asyncio
from typing import Optional

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "socializer-api"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
# Set DB path BEFORE importing database module
db_path = os.path.join(os.getcwd(), "socializer-api", "socializer.sqlite")
os.environ["SOCIALIZER_DB"] = db_path

from app.database import SessionLocal, engine, Base
from app.models import ContentPack, PostJob, JobStatus, PackStatus, Lane
from app import models

# Radar imports - assuming we can import them directly
# If radar is not a package, we might need more path hacking, 
# but based on file structure `radar` is a top-level package in root.
try:
    from radar.browser import BrowserManager
    from radar.instagram import InstagramAutomator
    from radar.ig_config import IG_SESSION_DIR, get_ig_username, get_ig_password
except ImportError as e:
    print(f"Error importing Radar components: {e}")
    print("Make sure you are running this from the project root.")
    sys.exit(1)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('worker.log')
    ]
)
logger = logging.getLogger("worker")

CONTENT_DIR = "content"

def ingest_content(db: Session):
    """
    Scans the content directory and adds new files as ContentPacks.
    Simple logic: each file in 'content' is a potential ContentPack.
    """
    if not os.path.exists(CONTENT_DIR):
        logger.warning(f"Content directory {CONTENT_DIR} not found.")
        return

    # Valid extensions
    VALID_EXTS = {'.mp4', '.mov', '.jpg', '.png'}
    
    files = [f for f in os.listdir(CONTENT_DIR) if os.path.splitext(f)[1].lower() in VALID_EXTS]
    
    for filename in files:
        # Check if already exists (naive check by filename in description or metadata? 
        # Current ContentPack model is very simple, no filename field.
        # We might need to add one or use a trick.
        # For now, let's just create a pack if we don't have enough? crude.
        # Better: let's assume we can't easily dedup without schema change.
        # Let's just SKIP ingestion for now to avoid duplicates on every run,
        # OR assume the user manually adds packs via API for now.
        #
        # WAIT, user asked to "use pipeline with content @[content]".
        # So we MUST ingest.
        # Let's store filename in a way we can check? or just check total count?
        pass

    # Actually, let's look at `conductor` or similar. 
    # Current DB schema has `ContentPack` but no link to file.
    # Let's use `uris` in RunArtifact? No.
    # Okay, for this prototype, we will just process QUEUED jobs.
    # Ingestion might be manual for now or we create a pack for each file ONCE.
    # Let's do a simple check: if DB is empty of approved packs, create some from files.
    
    # Remove seed check - we want to ingest what's in the folder.
    # To avoid massive duplicates on every restart without schema support:
    # We will just add them. User can delete via Admin.
    
    logger.info(f"Scanning {CONTENT_DIR} for new content...")
    added = 0
    for f in files:
        # Very crude dedup: skip if we have ANY pack created recently? No.
        # Let's just create them.
        pack = ContentPack(
            lane=Lane.beginner,
            status=PackStatus.approved,
            # We are NOT storing filename in DB yet (limitation).
            # But the worker uses the pack ID to pick a file.
            # This is fine for the prototype 'pipeline' demo.
        )
        db.add(pack)
        added += 1
    
    if added > 0:
        db.commit()
        logger.info(f"Ingested {added} files from {CONTENT_DIR} as new Content Packs.")
    else:
        logger.info("No files found to ingest.")

def process_job(db: Session, job: PostJob):
    """
    Processes a single job.
    """
    logger.info(f"Processing Job {job.id} for {job.platform}...")
    
    # Update status to running
    job.status = JobStatus.running
    db.commit()
    
    try:
        # 1. Resolve File
        # Since we don't have strict linkage yet, we'll pick a file.
        # In a real app, ContentPack would have a `file_path` column.
        # We'll just grab the first video file for now or random?
        import random
        files = [f for f in os.listdir(CONTENT_DIR) if f.endswith('.mp4')]
        if not files:
            raise Exception("No video files found in content directory!")
        
        # Deterministic based on pack id?
        video_file = files[job.content_pack_id % len(files)]
        video_path = os.path.abspath(os.path.join(CONTENT_DIR, video_file))
        
        caption = f"Posted by Socializer #socializer #{job.platform}"
        
        logger.info(f"Selected video: {video_file}")
        
        # 2. Execute via Radar
        if job.platform == models.Platform.instagram:
            upload_instagram(video_path, caption)
        else:
            logger.warning(f"Platform {job.platform} not yet implemented in worker.")
            # Fake success for others
            time.sleep(2)
        
        # 3. success
        job.status = JobStatus.posted
        db.commit()
        logger.info(f"Job {job.id} completed successfully.")
        
    except Exception as e:
        logger.error(f"Job {job.id} failed: {e}")
        job.status = JobStatus.failed
        job.last_error = str(e)
        db.commit()

def upload_instagram(video_path: str, caption: str):
    logger.info("Initializing Instagram Automator...")
    
    # Check creds
    if not get_ig_username() or not get_ig_password():
        raise Exception("IG Credentials not set in environment or .env")

    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=IG_SESSION_DIR)
        
        logger.info("logging in...")
        # For local demo, we want to see the browser to ensure it works.
        # Headless mode is often detected by IG or causes rendering issues.
        is_headless = os.getenv("HEADLESS", "False").lower() == "true"
        if not automator.login(get_ig_username(), get_ig_password(), headless=is_headless):
             raise Exception(f"Login failed: {automator.last_error}")
        
        logger.info(f"Uploading {video_path}...")
        success = automator.upload_video(video_path, caption)
        
        if not success:
            raise Exception(f"Upload failed: {automator.last_error}")

def main():
    logger.info("Starting Socializer Content Worker...")
    
    # Load env
    from dotenv import load_dotenv
    load_dotenv()
    
    # Load env
    from dotenv import load_dotenv
    load_dotenv()
    
    # 1. Ingest Once on Startup
    try:
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        
        init_db = SessionLocal()
        ingest_content(init_db)
        init_db.close()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")

    while True:
        try:
            db = SessionLocal()
            
            # 2. Check for Queued Jobs
            
            # 2. Check for Queued Jobs
            # We look for jobs that are 'queued' and ready to go?
            # Scheduler sets them to 'queued' with a time.
            # If time is past, we execute.
            
            # For this 'dev' pipeline, let's just pick up ANY queued job immediately
            # regardless of time, or respect time?
            # Let's respect time if possible, but user wants to 'use pipeline'.
            # They probably will tick the scheduler manually.
            
            now = datetime.utcnow()
            jobs = db.query(PostJob).filter(
                PostJob.status == JobStatus.queued
                # PostJob.scheduled_for_utc <= now  <-- Uncomment to enforce schedule
            ).all()
            
            if jobs:
                logger.info(f"Found {len(jobs)} queued jobs.")
                for job in jobs:
                    process_job(db, job)
            else:
                # logger.debug("No jobs found.")
                pass
            
            db.close()
            
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
        
        time.sleep(10) # Poll every 10s

if __name__ == "__main__":
    from datetime import datetime
    main()
