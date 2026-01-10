import os
import shutil
import asyncio
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import patch, AsyncMock
from radar.cli import app
from radar.models import RawItem

runner = CliRunner()

@patch("radar.cli.fetch_releases", new_callable=AsyncMock)
@patch("radar.cli.fetch_page", new_callable=AsyncMock)
def test_run(mock_page, mock_releases):
    print("Setting up paths...")
    site_content = Path("site/src/content")
    
    # Environment for valid checking
    os.environ["OUTPUT_DIR"] = str(site_content)
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["SQLITE_PATH"] = ":memory:"

    print("Setting up mocks...")
    mock_releases.return_value = [
        RawItem(
            source_id="langchain",
            kind="release",
            external_id="v0.1.0-beta", 
            title="LangChain v0.1.0 Beta",
            url="https://github.com/langchain-ai/langchain/releases/tag/v0.1.0-beta",
            raw_text="Release notes with BREAKING changes and tool calling improvements.",
            raw_hash="hash123",
            metadata={"tags": ["agents"]}
        )
    ]
    mock_page.return_value = RawItem(
            source_id="mcp-spec",
            kind="webpage",
            external_id="spec-2024-01-01",
            title="MCP Spec Update",
            url="https://modelcontextprotocol.io",
            raw_text="New protocol spec details with json schema updates and breaking deprecations.",
            raw_hash="hash456",
            metadata={"tags": ["mcp"]}
    )

    print("Running CLI with mocks...")
    # Based on observation, 'run' is treated as the main command (single command app behavior)
    result = runner.invoke(app, [])
    
    print("--- CLI OUTPUT ---")
    print(result.output)
    print("------------------")
    
    if result.exception:
        print("Exception:", result.exception)
    
    if result.exit_code != 0:
        print(f"CLI failed with exit code {result.exit_code}")
        exit(1)

    # Verify Output
    updates_en = site_content / "en" / "updates"
    
    if not updates_en.exists():
        print(f"FAILURE: {updates_en} does not exist.")
        exit(1)
        
    files = list(updates_en.glob("**/*.md"))
    print(f"Found {len(files)} generated markdown files in {updates_en}")
    
    if len(files) == 0:
         print("FAILURE: No markdown files generated.")
         exit(1)

    # Check content of one file for permalink
    sample = files[0]
    content = sample.read_text()
    if "permalink:" not in content:
        print(f"FAILURE: 'permalink' missing in frontmatter of {sample}")
        exit(1)
    
    if "slugify" in content: # Should correct slug be there? 
        # permalink: /updates/source_id/id_slug/
        pass

    # Check specific slug
    # v0.1.0-beta -> v0-1-0-beta
    if "v0-1-0-beta" not in sample.name and "spec-2024-01-01" not in sample.name:
        # spec-2024-01-01 is already slug-like
        print(f"WARNING: Filename {sample.name} might not be slugified correctly if expected.")
    
    print("SUCCESS: Verification passed.")

if __name__ == "__main__":
    test_run()
