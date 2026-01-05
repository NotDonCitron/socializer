import os
import asyncio
import logging
import typer
from rich import print
from radar import config
from radar import storage
from radar.sources import github, webpage_diff
from radar.pipeline import score, generate, render, weekly
from radar.llm.mock import MockLLM
from radar.llm.gemini_stub import GeminiLLM

# Configure logging
logger = logging.getLogger(__name__)

app = typer.Typer()

# Lightweight wrappers so tests can patch either radar.cli.* or the underlying modules.
def load_stack_config(stack_path: str):
    return config.load_stack_config(stack_path)


def connect(sqlite_path: str):
    return storage.connect(sqlite_path)


async def fetch_releases(source, token=""):
    return await github.fetch_releases(source, token=token)


async def fetch_page(source):
    return await webpage_diff.fetch_page(source)


def raw_exists_with_same_hash(con, source_id, kind, external_id, raw_hash):
    return storage.raw_exists_with_same_hash(con, source_id, kind, external_id, raw_hash)


def upsert_raw(con, item):
    return storage.upsert_raw(con, item)


def get_latest_raw_item(con, source_id, kind):
    return storage.get_latest_raw_item(con, source_id, kind)


def score_item(item, prev):
    return score.score_item(item, prev)


async def generate_posts(cfg, scored, llm):
    return await generate.generate_posts(cfg, scored, llm)


def upsert_post(con, post):
    return storage.upsert_post(con, post)


def render_posts(cfg, posts, output_dir="content"):
    return render.render_posts(cfg, posts, output_dir=output_dir)


def render_weekly(posts, output_dir="content", lang="en"):
    return weekly.render_weekly(posts, output_dir=output_dir, lang=lang)

def get_llm():
    provider = os.getenv("LLM_PROVIDER", "mock")
    if provider == "gemini":
        return GeminiLLM(api_key=os.getenv("GEMINI_API_KEY", ""))
    return MockLLM()

@app.command()
def version():
    """Print version."""
    print("0.1.0")

@app.command()
def run(stack_path: str = "stack.yaml"):
    """Fetch sources, score, generate posts, render markdown, write weekly digest."""
    sqlite_path = os.getenv("SQLITE_PATH", "data/radar.sqlite")
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

    llm = get_llm()
    token = os.getenv("GITHUB_TOKEN", "")

    async def _main():
        # Check for zero sources
        if not cfg.sources:
            logger.warning("No sources configured in stack.yaml")
            print("[yellow]No sources configured in stack.yaml[/yellow]")
            return

        raw_items = []
        for src in cfg.sources:
            try:
                if src.type == "github_releases":
                    raw_items.extend(await fetch_releases(src, token=token))
                elif src.type == "webpage_diff":
                    raw_items.append(await fetch_page(src))
            except Exception as e:
                logger.error(f"Error fetching {src.id}: {e}")
                print(f"[red]Error fetching {src.id}: {e}[/red]")

        # Log if no items were fetched
        if len(raw_items) == 0:
            logger.warning("No items fetched from any source. Check source configurations.")
            print("[yellow]No items fetched from any source. Check source configurations.[/yellow]")

        # store raw + skip unchanged
        changed = []
        for item in raw_items:
            if raw_exists_with_same_hash(con, item.source_id, item.kind, item.external_id, item.raw_hash):
                continue
            try:
                upsert_raw(con, item)
                changed.append(item)
            except Exception as e:
                logger.error(f"Error storing raw item {item.external_id}: {e}")
                print(f"[red]Error storing raw item {item.external_id}: {e}[/red]")

        print(f"[green]Fetched[/green] {len(raw_items)} items, [yellow]changed[/yellow] {len(changed)}")

        # Log if no changes detected
        if len(changed) == 0:
            logger.info("No changed items to score")

        scored = []
        for item in changed:
            prev = get_latest_raw_item(con, item.source_id, item.kind)
            scored.append(score_item(item, prev))

        # Only generate posts if there are scored items
        posts = []
        if scored:
            posts = await generate_posts(cfg, scored, llm)
            for p in posts:
                try:
                    upsert_post(con, p)
                except Exception as e:
                    logger.error(f"Error storing post: {e}")
                    print(f"[red]Error storing post: {e}[/red]")

        # Render posts with error handling
        try:
            render_posts(cfg, posts, output_dir=os.getenv("OUTPUT_DIR", "content"))
        except Exception as e:
            logger.error(f"Error rendering posts: {e}")
            print(f"[red]Error rendering posts: {e}[/red]")

        if posts:
            try:
                render_weekly(posts, output_dir=os.getenv("OUTPUT_DIR", "content"), lang="en")
            except Exception as e:
                logger.error(f"Error rendering weekly digest (en): {e}")
                print(f"[red]Error rendering weekly digest (en): {e}[/red]")

            if "de" in cfg.languages:
                try:
                    render_weekly([p for p in posts if "de" in p.languages], output_dir=os.getenv("OUTPUT_DIR", "content"), lang="de")
                except Exception as e:
                    logger.error(f"Error rendering weekly digest (de): {e}")
                    print(f"[red]Error rendering weekly digest (de): {e}[/red]")

        print(f"[cyan]Generated[/cyan] {len(posts)} posts")

    asyncio.run(_main())

if __name__ == "__main__":
    app()
