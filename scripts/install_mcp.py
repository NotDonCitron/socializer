import json
import os
import shutil
from pathlib import Path

# Paths
DB_PATH = "/home/kek/socializer/socializer/socializer.sqlite"
GITHUB_TOKEN = os.environ.get("github_token")

def update_config(filename):
    path = Path(os.path.expanduser(filename))
    
    # Create file if it doesn't exist
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"mcpServers": {}}
    else:
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding {path}, starting fresh.")
            data = {"mcpServers": {}}

    if "mcpServers" not in data or not isinstance(data["mcpServers"], dict):
        data["mcpServers"] = {}

    # 1. Add SQLite
    print(f"Adding SQLite MCP (DB: {DB_PATH})...")
    data["mcpServers"]["sqlite"] = {
        "command": "uvx",
        "args": ["mcp-server-sqlite", "--db-path", DB_PATH]
    }

    # 2. Add GitHub (if token exists)
    if GITHUB_TOKEN:
        print("Adding GitHub MCP...")
        data["mcpServers"]["github"] = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": GITHUB_TOKEN
            }
        }
    else:
        print("Skipping GitHub MCP: 'github_token' env var not found.")

    # Save
    backup_path = path.with_suffix('.json.bak_install')
    if path.exists():
        shutil.copy(path, backup_path)
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Successfully updated {path}")

def main():
    # Prefer ~/.gemini/settings.json
    config_path = "~/.gemini/settings.json"
    update_config(config_path)

if __name__ == "__main__":
    main()
