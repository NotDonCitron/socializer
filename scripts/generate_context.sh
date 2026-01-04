#!/usr/bin/env bash
set -euo pipefail

# Define paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
GIT_REPO="$PROJECT_ROOT/socializer"

# Move to repo
cd "$GIT_REPO" || cd "$PROJECT_ROOT"

# Output file
OUTPUT="$PROJECT_ROOT/prompt_for_chatgpt.txt"

{
  echo "You are the PLANNER. Read the project status below."
  echo "Output a short step-by-step fix plan."
  echo "Rules:"
  echo "- Small PR-sized changes."
  echo "- Always name files to edit."
  echo "- Include exact commands to run."
  echo "- Format the plan in Markdown."
  echo
  echo "Status:"
  echo "## git status"
  git status --porcelain || true
  echo
  echo "## git diff (stat)"
  git diff --stat || true
  echo
  echo "## failing command output"
  # Try to find and run pytest
  if [[ -x .venv/bin/pytest ]]; then
      .venv/bin/pytest --maxfail=1 --tb=short 2>&1 || true
  elif [[ -x ../.venv/bin/pytest ]]; then
      ../.venv/bin/pytest --maxfail=1 --tb=short 2>&1 || true
  else
      # echo "Skipping pytest (not found)"
      true
  fi
} > "$OUTPUT"

echo "✅ Context generated!"
echo "1. Open: $OUTPUT"
echo "2. Copy ALL text."
echo "3. Paste into your ChatGPT browser tab."
echo "4. Copy ChatGPT's response."
echo "5. Paste it into: $PROJECT_ROOT/plan.md"
