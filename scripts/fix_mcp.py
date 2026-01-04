import json
import os
import shutil
from pathlib import Path

def fix_config(filename):
    path = Path(os.path.expanduser(filename))
    if not path.exists():
        print(f"File not found: {path}")
        return

    print(f"Checking {path}...")
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error decoding JSON in {path}")
        return

    changed = False
    
    # Check for context7 in various possible structures
    
    # 1. Structure: "mcpServers": { "context7": ... }
    if "mcpServers" in data and isinstance(data["mcpServers"], dict):
        if "context7" in data["mcpServers"]:
            print("Found 'context7' in mcpServers. Removing...")
            del data["mcpServers"]["context7"]
            changed = True
            
    # 2. Structure: "mcpServers": [ { "name": "context7", ... } ] (Array format)
    if "mcpServers" in data and isinstance(data["mcpServers"], list):
        original_len = len(data["mcpServers"])
        data["mcpServers"] = [s for s in data["mcpServers"] if s.get("name") != "context7" and "context7" not in s.get("command", "")]
        if len(data["mcpServers"]) < original_len:
            print("Found 'context7' in mcpServers list. Removing...")
            changed = True

    if changed:
        backup_path = path.with_suffix('.json.bak')
        shutil.copy(path, backup_path)
        print(f"Backed up to {backup_path}")
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully updated {path}")
    else:
        print(f"No 'context7' configuration found in {path}")

def main():
    # Common config locations for Gemini CLI / MCP
    configs = [
        "~/.gemini/settings.json",
        "~/.gemini/mcp.json",
        "~/.config/gemini/settings.json"
    ]
    
    found_any = False
    for config in configs:
        if os.path.exists(os.path.expanduser(config)):
            fix_config(config)
            found_any = True
            
    if not found_any:
        print("Could not find any Gemini configuration files in standard locations.")

if __name__ == "__main__":
    main()
