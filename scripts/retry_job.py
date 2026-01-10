import os
import sys

# HACK: add socializer-api to path
sys.path.append(os.path.join(os.getcwd(), "socializer-api"))

from socializer_api import db

def retry():
    db_path = os.path.join(os.getcwd(), "socializer.sqlite")
    
    # Get all failed jobs
    jobs = db.list_jobs(status="failed", db_path=db_path)
    if not jobs:
        print("No failed jobs found.")
        return

    for job in jobs:
        jid = job['id']
        print(f"Retrying Job {jid}...")
        db.retry_job(jid, db_path=db_path)
    
    print("Done.")

if __name__ == "__main__":
    retry()
