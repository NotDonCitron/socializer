import subprocess
import sys

def run_git(args):
    try:
        result = subprocess.run(["git"] + args, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def get_summary():
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    status = run_git(["status", "--short"])
    last_commit = run_git(["log", "-1", "--oneline"])
    diff_stat = run_git(["diff", "--stat"])
    
    print(f"--- Git Summary ---")
    print(f"Branch: {branch}")
    print(f"Last Commit: {last_commit}")
    print(f"\n--- Status ---")
    print(status if status else "Clean")
    print(f"\n--- Diff Stat ---")
    print(diff_stat if diff_stat else "No changes")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        get_summary()
    else:
        # Default to showing summary
        get_summary()
