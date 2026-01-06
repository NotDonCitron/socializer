# Socializer Project

This project aims to... (Existing content of README.md)

## Development Setup and Workflow

### Code Formatting and Linting

To ensure consistent code style and organize imports, we use Ruff and isort for Python, and Prettier for other languages.

Before committing, please format your code by running the following script:

\`\`\`bash
./scripts/format_code.sh
\`\`\`

This script will:
- Run Ruff for linting and auto-formatting Python files.
- Sort Python imports using isort.
- Format JavaScript, TypeScript, JSON, Markdown, and Astro files using Prettier.

Ensure you have Node.js and npm installed for Prettier to function correctly. Ruff and isort are dependencies managed through pip.