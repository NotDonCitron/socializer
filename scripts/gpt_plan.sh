#!/usr/bin/env bash
# This script is called by the /loop command.
# It simply reads the manual plan provided by the user.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PLAN_FILE="$PROJECT_ROOT/plan.md"

if [[ ! -f "$PLAN_FILE" ]]; then
    echo "ERROR: Plan file not found at $PLAN_FILE"
    echo "Please run './scripts/generate_context.sh', get a plan from ChatGPT, and save it to 'plan.md'."
    exit 1
fi

cat "$PLAN_FILE"
