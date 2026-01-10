import sqlite3
import os

db_path = os.path.join("socializer-api", "socializer.sqlite")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Tables ---")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
for row in cursor.fetchall():
    print(row[0])

print("\n--- Schema for content_packs ---")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='content_packs';")
print(cursor.fetchone()[0])

conn.close()
