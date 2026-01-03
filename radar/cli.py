import os
import asyncio
import typer
from rich import print
from radar.config import load_stack_config
from radar.storage import connect, upsert_raw, raw_exists_with_same_hash, upsert_post, get_latest_raw_item
from radar.sources.github import fetch_releases
from radar.sources.webpage_diff import fetch_page
from radar.pipeline.score import score_item
from radar.pipeline.generate import generate_posts
from radar.pipeline.render import render_posts
from radar.pipeline.weekly import render_weekly
from radar.llm.mock import MockLLM
from radar.llm.gemini_stub import GeminiLLM

app = typer.Typer()

def get_llm():
    provider = os.getenv("LLM_PROVIDER", "mock")
    if provider == "gemini":
        return GeminiLLM(api_key=os.getenv("GEMINI_API_KEY", ""))
    return MockLLM()

@app.command()
def run(stack_path: str = "stack.yaml"):
    """Fetch sources, score, generate posts, render markdown, write weekly digest."""
    cfg = load_stack_config(stack_path)
    sqlite_path = os.getenv("SQLITE_PATH", "data/radar.sqlite")
    con = connect(sqlite_path)
    llm = get_llm()
    token = os.getenv("GITHUB_TOKEN", "")

    async def _main():
        raw_items = []
        for src in cfg.sources:
            try:
                if src.type == "github_releases":
                    raw_items.extend(await fetch_releases(src, token=token))
                elif src.type == "webpage_diff":
                    raw_items.append(await fetch_page(src))
            except Exception as e:
                print(f"[red]Error fetching {src.id}: {e}[/red]")

        # store raw + skip unchanged
        changed = []
        for item in raw_items:
            if raw_exists_with_same_hash(con, item.source_id, item.kind, item.external_id, item.raw_hash):
                continue
            upsert_raw(con, item)
            changed.append(item)

        print(f"[green]Fetched[/green] {len(raw_items)} items, [yellow]changed[/yellow] {len(changed)}")

        scored = []
        for item in changed:
            prev = get_latest_raw_item(con, item.source_id, item.kind)
            scored.append(score_item(item, prev))

        posts = await generate_posts(cfg, scored, llm)
        for p in posts:
            upsert_post(con, p)

        render_posts(cfg, posts, output_dir=os.getenv("OUTPUT_DIR", "content"))
        if posts:
            render_weekly(posts, output_dir=os.getenv("OUTPUT_DIR", "content"), lang="en")
            if "de" in cfg.languages:
                render_weekly([p for p in posts if "de" in p.languages], output_dir=os.getenv("OUTPUT_DIR", "content"), lang="de")

        print(f"[cyan]Generated[/cyan] {len(posts)} posts")

    asyncio.run(_main())

if __name__ == "__main__":
    app()
