from huggingface_hub import HfApi, login
import os

token = os.environ.get("HF_TOKEN") or os.environ.get("HF_HUB_TOKEN")
if not token:
    raise EnvironmentError("HF_TOKEN or HF_HUB_TOKEN is required to deploy")

login(token=token)

api = HfApi()
repo_id = "PHhTTPS/socializer"

# Already exists, just making sure
api.create_repo(repo_id=repo_id, repo_type="space", space_sdk="docker", exist_ok=True)

# Aggressive ignore list to avoid the 266k file hashing nightmare
ignore = [
    "socializer", "node_modules", ".git", ".venv", ".hf_deploy_venv",
    "admin-panel-temp", "content", "debug_shots", "scripts", "tests",
    "site", "conductor", "data", "radar", "examples", "ig_session",
    "export", "external_repos", "tiktok_session", "*.log", "*.mp4",
    "*.exe", "*.zip", "*.pyc", "__pycache__"
]

print("Starting large folder upload...")
api.upload_large_folder(
    folder_path=".",
    repo_id=repo_id,
    repo_type="space",
    ignore_patterns=ignore
)
print(f"Done! https://huggingface.co/spaces/{repo_id}")
