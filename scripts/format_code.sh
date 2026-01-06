#!/bin/bash
set -e

# Install dependencies if needed
# pip install ruff isort
# npm install -g prettier

echo "Formatting Python code with Ruff and isort..."
# Fix linting issues and format Python files
ruff check --fix .
ruff format .

# Sort Python imports
isort .

echo "Formatting JavaScript/TypeScript/Markdown/JSON with Prettier..."
# Format JS, TS, JSON, Markdown, etc.
npx prettier --write "**/*.{js,ts,json,md,astro,html}"

echo "Code formatting complete."
