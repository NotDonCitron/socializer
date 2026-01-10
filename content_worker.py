import os
import time
import sys
import logging
from datetime import datetime, timezone
from typing import Optional

# Set DB path BEFORE importing database module
db_path = os.path.join(os.getcwd(), "socializer.sqlite")
os.environ["SOCIALIZER_DB"] = db_path

# Add project root and socializer-api to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "socializer-api"))

# From socializer_api (raw SQL layer)
from socializer_api import db
from dotenv import load_dotenv

# Load .env at module level
load_dotenv()

# Radar imports
try:
    from radar.browser import BrowserManager
    from radar.instagram import InstagramAutomator
    from radar.ig_config import IG_SESSION_DIR, get_ig_username, get_ig_password
except ImportError as e:
    print(f"Error importing Radar components: {e}")
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

def ingest_content():
    """
    Scans the content directory and adds new files as ContentPacks using API logic.
    """
    if not os.path.exists(CONTENT_DIR):
        logger.warning(f"Content directory {CONTENT_DIR} not found.")
        return

    VALID_EXTS = {'.mp4', '.mov', '.jpg', '.png'}
    files = [f for f in os.listdir(CONTENT_DIR) if os.path.splitext(f)[1].lower() in VALID_EXTS]
    
    logger.info(f"Scanning {CONTENT_DIR} for new content...")
    added = 0
    for f in files:
        # We use the API's insert function which handles UUIDs and schema
        db.insert_content_pack(
            lane="beginner",
            format="video" if f.endswith(('.mp4', '.mov')) else "image",
            status="approved",
            db_path=db_path
        )
        added += 1
    
    if added > 0:
        logger.info(f"Ingested {added} files from {CONTENT_DIR} as new Content Packs.")
    else:
        logger.info("No files found to ingest.")

def process_job(job: dict):
    """
    Processes a single job using API schema.
    """
    job_id = job['id']
    logger.info(f"Processing Job {job_id} for {job['platform']}...")
    
    # Update status to running
    db.update_job_status(job_id, "running", db_path=db_path)
    
    try:
        # 1. Resolve File (Simplified logic for prototype)
        files = [f for f in os.listdir(CONTENT_DIR) if f.endswith('.mp4')]
        if not files:
            raise Exception("No video files found in content directory!")
        
        # Consistent mapping for test purposes
        # hash(job_id) to pick a file
        idx = hash(job_id) % len(files)
        video_file = files[idx]
        video_path = os.path.abspath(os.path.join(CONTENT_DIR, video_file))
        
        caption = f"Posted by Socializer #socializer #{job['platform']}"
        logger.info(f"Selected video: {video_file}")
        
        # 2. Execute via Radar
        if job['platform'] in ["instagram", "instagram_reels"]:
            upload_instagram(video_path, caption)
        else:
            logger.warning(f"Platform {job['platform']} not yet implemented in worker.")
            time.sleep(2)
        
        # 3. success
        db.update_job_status(job_id, "posted", db_path=db_path)
        logger.info(f"Job {job_id} completed successfully.")
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        db.update_job_status(job_id, "failed", last_error=str(e), db_path=db_path)

def upload_instagram(video_path: str, caption: str):
    logger.info("Initializing Instagram Automator...")
    if not get_ig_username() or not get_ig_password():
        raise Exception("IG Credentials not set in environment or .env")

    with BrowserManager() as manager:
        automator = InstagramAutomator(manager, user_data_dir=IG_SESSION_DIR)
        automator.debug = True # Force debug for troubleshooting
        is_headless = os.getenv("HEADLESS", "False").lower() == "true"
        logger.info(f"Headless mode: {is_headless}")
        
        if not automator.login(get_ig_username(), get_ig_password(), headless=is_headless):
             raise Exception(f"Login failed: {automator.last_error}")
        
        logger.info(f"Uploading {video_path}...")
        success = automator.upload_video(video_path, caption)
        if not success:
            raise Exception(f"Upload failed: {automator.last_error}")

def main():
    logger.info("Starting Socializer Content Worker (Unified)...")
    
    # Ensure tables exist using API logic
    db.init_db(db_path)
    
    # 1. Ingest once
    try:
        ingest_content()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")

    while True:
        try:
            # 2. Check for Queued Jobs using API logic
            jobs = db.list_jobs(status="queued", db_path=db_path)
            
            if jobs:
                logger.info(f"Found {len(jobs)} queued jobs.")
                for job in jobs:
                    process_job(job)
            
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
        
        time.sleep(10)

if __name__ == "__main__":
    main()
