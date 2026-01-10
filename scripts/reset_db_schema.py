import os

def reset():
    db_path = os.path.join(os.getcwd(), "socializer.sqlite")
    if os.path.exists(db_path):
        print(f"Removing database file at {db_path}...")
        os.remove(db_path)
    
    # Also remove any WAL/SHM files
    for ext in ["-wal", "-shm"]:
        if os.path.exists(db_path + ext):
            os.remove(db_path + ext)
            
    print("Database cleared. It will be recreated on next run.")

if __name__ == "__main__":
    reset()
