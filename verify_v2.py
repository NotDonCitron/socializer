import os
from typer.testing import CliRunner
from radar.cli import app
from pathlib import Path
import shutil

runner = CliRunner()

def test_run():
    # Setup paths
    site_content = Path("site/src/content")
    if site_content.exists():
        # Clean up previous run if needed, or just let it overwrite?
        # Better to clean up to verify generation
        pass 
        # shutil.rmtree(site_content) # dangerous if user has other stuff

    # Environment for valid checking
    os.environ["OUTPUT_DIR"] = str(site_content)
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["SQLITE_PATH"] = ":memory:" # Use in-memory DB for verification to not pollute real DB? 
    # But cli.py default to data/radar.sqlite. 
    # If I use :memory:, it won't have history, so everything changes. That's good for generating posts.

    print("Running CLI...")
    result = runner.invoke(app, ["run"])
    
    print(result.stdout)
    
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
        
    print("SUCCESS: Verification passed.")

if __name__ == "__main__":
    test_run()
