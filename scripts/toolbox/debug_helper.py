import os
import glob
from datetime import datetime

def list_recent_errors(limit=5):
    # Search for files matching the pattern in the project root
    error_files = glob.glob("error_upload_debug_*.png")
    # Also check socializer/
    error_files += glob.glob("socializer/error_upload_debug_*.png")
    
    if not error_files:
        print("No error screenshots found.")
        return

    # Sort by modification time
    error_files.sort(key=os.path.getmtime, reverse=True)

    print(f"--- Recent Playwright Errors (Last {limit}) ---")
    for f in error_files[:limit]:
        mtime = datetime.fromtimestamp(os.path.getmtime(f))
        size = os.path.getsize(f) / 1024
        print(f"[{mtime}] {f} ({size:.1f} KB)")

if __name__ == "__main__":
    list_recent_errors()
