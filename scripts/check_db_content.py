import os
import sqlite3
import sys

# Try to find the DB
db_path = os.path.join(os.getcwd(), "socializer.sqlite")
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    sys.exit(1)

print(f"Checking DB at: {db_path}")

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get content packs
try:
    cur.execute("SELECT id, status FROM content_packs")
    packs = cur.fetchall()
    print(f"Content Packs count: {len(packs)}")
except Exception as e:
    print(f"Error reading content_packs: {e}")

# Get jobs
try:
    cur.execute("SELECT id, platform, status, last_error FROM post_jobs")
    jobs = cur.fetchall()
    print(f"Post Jobs count: {len(jobs)}")

    for job in jobs:
        jid = job['id']
        short_id = jid[:8] if jid else "None"
        print(f"Job {short_id}...: {job['status']} ({job['platform']}) - Error: {job['last_error']}")
except Exception as e:
    print(f"Error reading post_jobs: {e}")

conn.close()
