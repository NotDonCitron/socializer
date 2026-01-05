# Contributing to Socializer

Thank you for your interest in contributing to Socializer! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic understanding of async Python and Playwright

### Setting Up Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/socializer.git
   cd socializer
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e socializer/
   pip install -e socializer-api/
   pip install black ruff pytest pytest-asyncio pytest-cov
   playwright install chromium
   ```

4. **Install pre-commit hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

### Code Style

We use automated tools to enforce code style:

- **Black** for code formatting (line length: 100)
- **isort** for import sorting
- **Ruff** for linting

Run these before committing:
```bash
black .
isort .
ruff check --fix .
```

Or let pre-commit handle it automatically:
```bash
pre-commit run --all-files
```

### Type Hints

All code should include type hints:

```python
from typing import Optional
from pathlib import Path

async def upload_video(video_path: Path, caption: str) -> bool:
    """Upload video with caption."""
    # Implementation
    return True
```

### Testing

Write tests for new features:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=socializer --cov=socializer_api

# Run specific test file
pytest tests/test_tiktok.py
```

### Making Changes

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation if needed

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Use conventional commit messages:
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation changes
   - `test:` adding or updating tests
   - `refactor:` code refactoring
   - `chore:` maintenance tasks

4. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Guidelines

- Fill out the PR template completely
- Ensure all tests pass
- Update documentation for new features
- Keep PRs focused on a single change
- Add screenshots for UI changes
- Reference related issues

## Code Review Process

1. Automated checks must pass (CI, linting, tests)
2. At least one maintainer review required
3. Address review feedback promptly
4. Squash commits if requested

## Reporting Bugs

Use the issue template and include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version)
- Relevant logs or screenshots

## Feature Requests

- Check if the feature already exists
- Provide clear use case and benefits
- Be open to discussion and alternative approaches

## Security

Report security vulnerabilities privately to the maintainers. Do not open public issues for security concerns.

## Questions?

- Open a discussion on GitHub
- Check existing issues and documentation
- Be respectful and patient

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Socializer!
