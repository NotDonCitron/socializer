# Radar CLI and Testing Documentation

## Overview

The Radar CLI (`radar/cli.py`) provides command-line access to the content aggregation and generation pipeline. This document covers the CLI architecture, testing patterns, and recent fixes.

## CLI Commands

### `radar run`

Runs the complete content pipeline:

```bash
# Use default stack.yaml configuration
radar run

# Use custom configuration file
radar run --stack-path custom-stack.yaml
```

**Pipeline execution:**
1. Load stack configuration (sources, languages, LLM settings)
2. Connect to SQLite database
3. Fetch data from configured sources (GitHub releases, web pages)
4. Store raw items and filter out unchanged content (hash-based)
5. Score items for impact and relevance
6. Generate social media posts using LLM (if there are changes)
7. Render posts as markdown files
8. Create weekly digest

### `radar version`

Prints the current version:

```bash
radar version
# Output: 0.1.0
```

## Configuration

Create a `stack.yaml` file:

```yaml
sources:
  - id: my-project
    type: github_releases
    repo: owner/repo

  - id: website-updates
    type: webpage_diff
    url: https://example.com/changelog
    selector: .content

languages:
  - en
  - de  # Optional: generate posts in multiple languages

llm:
  provider: gemini  # or "mock" for testing
```

## Environment Variables

```bash
# LLM Configuration
LLM_PROVIDER=gemini          # Default: mock
GEMINI_API_KEY=your_key      # Required if using Gemini

# Storage
SQLITE_PATH=data/radar.sqlite # Default: data/radar.sqlite

# Output
OUTPUT_DIR=content            # Default: content

# GitHub (optional)
GITHUB_TOKEN=your_token       # For higher API rate limits
```

## Architecture: Testable Wrapper Pattern

The CLI uses **module-level wrapper functions** to enable clean mocking in tests. This pattern was introduced to fix test isolation issues.

### Why Wrappers?

**Before (problematic):**
```python
# Direct imports in _main()
from radar.config import load_stack_config
from radar.sources.github import fetch_releases

async def _main():
    cfg = load_stack_config(stack_path)  # Hard to mock
    items = await fetch_releases(src)     # Hard to mock
```

**After (testable):**
```python
# Module-level wrappers
def load_stack_config(stack_path: str):
    return config.load_stack_config(stack_path)

async def fetch_releases(source, token=""):
    return await github.fetch_releases(source, token=token)

async def _main():
    cfg = load_stack_config(stack_path)  # Easy to mock
    items = await fetch_releases(src)     # Easy to mock
```

### All Wrapper Functions

```python
# Synchronous wrappers
def load_stack_config(stack_path: str)
def connect(sqlite_path: str)
def raw_exists_with_same_hash(con, source_id, kind, external_id, raw_hash)
def upsert_raw(con, item)
def get_latest_raw_item(con, source_id, kind)
def score_item(item, prev)
def upsert_post(con, post)
def render_posts(cfg, posts, output_dir="content")
def render_weekly(posts, output_dir="content", lang="en")

# Async wrappers (note the async keyword!)
async def fetch_releases(source, token="")
async def fetch_page(source)
async def generate_posts(cfg, scored, llm)
```

**Critical:** Async wrappers must be marked `async` and use `await`, otherwise you'll get:
```
TypeError: object list can't be used in 'await' expression
```

## Testing

### Running Tests

```bash
# All CLI tests
pytest tests/test_cli.py -v

# Specific test
pytest tests/test_cli.py::TestCLICommands::test_run_command -v

# Quick mode
pytest tests/test_cli.py -q

# With coverage
pytest tests/test_cli.py --cov=radar.cli --cov-report=html
```

### Test Structure

Tests use the **Typer CliRunner** and **unittest.mock.patch** to mock dependencies:

```python
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from radar.cli import app

class TestCLICommands:
    @patch("radar.cli.load_stack_config")
    @patch("radar.cli.fetch_releases")
    @patch("radar.cli.generate_posts")
    def test_run_command(self, mock_gen, mock_fetch, mock_config):
        runner = CliRunner()

        # Setup mocks
        mock_config.return_value = create_mock_config()
        mock_fetch.return_value = [create_mock_item()]
        mock_gen.return_value = [create_mock_post()]

        # Execute
        result = runner.invoke(app, ["run"])

        # Assert
        assert result.exit_code == 0
        assert "Generated 1 posts" in result.output
```

### Key Testing Patterns

#### 1. Patch at CLI Layer

```python
# ✅ GOOD: Patch the wrapper
@patch("radar.cli.fetch_releases")

# ❌ BAD: Patch the underlying module
@patch("radar.sources.github.fetch_releases")
```

#### 2. Async Mock Handling

pytest's `@patch` automatically converts async functions to `AsyncMock`:

```python
@patch("radar.cli.fetch_releases")  # Async function
def test_example(mock_fetch):
    # mock_fetch is automatically an AsyncMock
    mock_fetch.return_value = [item1, item2]
    # When awaited in CLI, it returns the list directly
```

#### 3. Mock Return Values vs Side Effects

```python
# Single return value
mock_fetch.return_value = [item]

# Multiple calls with different values
mock_score.side_effect = [scored1, scored2, scored3]
```

#### 4. Environment Variables

```python
@patch.dict(os.environ, {"OUTPUT_DIR": "custom/output"})
def test_custom_output(self):
    # Test uses custom output directory
```

### Test Coverage

Current test suite covers:

- ✅ Basic run command (happy path)
- ✅ Custom stack path
- ✅ Custom SQLite path
- ✅ Custom output directory
- ✅ Multiple sources (GitHub + webpage)
- ✅ Multiple languages
- ✅ No changes (all items filtered)
- ✅ Error handling (config load, DB connect)
- ✅ Empty source list
- ✅ Low-score filtering
- ✅ Version command

**Coverage: 21 tests, all passing** ✅

## Recent Fixes (2026-01-05)

### Problem 1: Async/Await Type Errors

**Error:**
```
TypeError: object list can't be used in 'await' expression
```

**Cause:** Wrapper functions weren't marked `async`, so they returned coroutines instead of awaitable values.

**Fix:** Made wrappers async:
```python
# Before
def fetch_releases(source, token=""):
    return github.fetch_releases(source, token=token)

# After
async def fetch_releases(source, token=""):
    return await github.fetch_releases(source, token=token)
```

**Files affected:**
- `fetch_releases()` - radar/cli.py:23
- `fetch_page()` - radar/cli.py:27
- `generate_posts()` - radar/cli.py:47

### Problem 2: Unnecessary Post Generation

**Issue:** `generate_posts()` was called even when `scored` list was empty (no changes to process).

**Fix:** Added conditional check:
```python
# Before
posts = await generate_posts(cfg, scored, llm)

# After
posts = []
if scored:
    posts = await generate_posts(cfg, scored, llm)
    for p in posts:
        upsert_post(con, p)
```

**Location:** radar/cli.py:118-123

### Problem 3: Early Crashes on Config/DB Errors

**Issue:** Errors during config load or DB connection crashed the CLI without helpful messages.

**Fix:** Added graceful error handling:
```python
try:
    cfg = load_stack_config(stack_path)
except Exception as exc:
    print(f"[red]Error loading config: {exc}[/red]")
    return

try:
    con = connect(sqlite_path)
except Exception as exc:
    print(f"[red]Error connecting to storage: {exc}[/red]")
    return
```

**Location:** radar/cli.py:77-87

## Best Practices

### CLI Development

1. **Always use wrapper functions** - Don't call modules directly in `_main()`
2. **Keep wrappers thin** - Just delegate to the actual implementation
3. **Match async signatures** - If underlying function is async, wrapper must be too
4. **Handle errors gracefully** - Catch and log, don't crash
5. **Conditional processing** - Skip expensive operations when there's no work

### Test Development

1. **Mock at CLI layer** - Patch `radar.cli.*` not the underlying modules
2. **Use descriptive test names** - `test_run_command_custom_output_dir`
3. **Test one thing** - Each test should verify a single behavior
4. **Mock external calls** - No real API/LLM/file access in tests
5. **Assert exit codes** - `assert result.exit_code == 0`
6. **Check output messages** - `assert "Generated" in result.output`
7. **Verify mock calls** - `mock_fetch.assert_called_once()`

### Common Pitfalls

❌ **Forgetting async on wrappers**
```python
def fetch_releases(source):  # Missing async!
    return github.fetch_releases(source)
```

❌ **Patching wrong module**
```python
@patch("radar.sources.github.fetch_releases")  # Should patch radar.cli
```

❌ **Not initializing return values**
```python
if scored:
    posts = await generate_posts()  # posts undefined if scored is empty!
```

❌ **Skipping error handling**
```python
cfg = load_stack_config(path)  # Crashes if file doesn't exist
```

## Debugging Tests

### Show test output
```bash
pytest tests/test_cli.py -v -s
```

### Run single test
```bash
pytest tests/test_cli.py::TestCLICommands::test_run_command -xvs
```

### Debug with pdb
```python
def test_example(self):
    import pdb; pdb.set_trace()
    result = runner.invoke(app, ["run"])
```

### Check mock calls
```python
print(mock_fetch.call_args_list)
print(mock_fetch.call_count)
```

## Future Improvements

- [ ] Add integration tests (real DB, no mocks)
- [ ] Test concurrent source fetching
- [ ] Add benchmark tests for large datasets
- [ ] Test CLI signal handling (SIGINT/SIGTERM)
- [ ] Add CLI progress bars for long operations
- [ ] Implement `--dry-run` flag
- [ ] Add `--verbose` flag for detailed logging
- [ ] Create `radar init` command for setup
- [ ] Add `radar status` to check configuration

## Related Documentation

- [radar/README.md](README.md) - Browser automation and Instagram
- [CLAUDE.md](../CLAUDE.md) - Project guidelines
- [AGENTS.md](../AGENTS.md) - BMAD agent workflows
- Stack configuration: `stack.yaml` example

---

**Last Updated:** 2026-01-05
**Test Status:** 21/21 passing ✅
**Maintainer:** Development team
