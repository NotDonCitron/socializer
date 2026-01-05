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
from radar.engagement_models import EngagementAction, EngagementActionType, EngagementPlatform, EngagementBatch
from radar.engagement import EngagementManager
from radar.browser import BrowserManager

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

# Engagement commands
engage_app = typer.Typer()
app.add_typer(engage_app, name="engage", help="Social media engagement commands")

@engage_app.command()
def instagram_like(
    url: str = typer.Argument(..., help="Instagram post URL"),
    headless: bool = typer.Option(True, help="Run in headless mode")
):
    """Like an Instagram post."""
    try:
        with BrowserManager() as manager:
            engagement_manager = EngagementManager()
            if not engagement_manager.initialize_instagram(manager, "ig_session"):
                print("[red]Failed to initialize Instagram automator[/red]")
                return

            # Login first
            print("Logging in to Instagram...")
            if not engagement_manager.instagram_automator.login("username", "password", headless=headless):
                print(f"[red]Login failed: {engagement_manager.instagram_automator.last_error}[/red]")
                return

            print(f"Liking post: {url}")
            result = engagement_manager.instagram_automator.like_post(url)

            if result.success:
                print(f"[green] Success: {result.message}[/green]")
            else:
                print(f"[red] Failed: {result.message}[/red]")

    except Exception as e:
        print(f"[red]Error: {e}[/red]")

@engage_app.command()
def instagram_follow(
    username: str = typer.Argument(..., help="Instagram username"),
    headless: bool = typer.Option(True, help="Run in headless mode")
):
    """Follow an Instagram user."""
    try:
        with BrowserManager() as manager:
            engagement_manager = EngagementManager()
            if not engagement_manager.initialize_instagram(manager, "ig_session"):
                print("[red]Failed to initialize Instagram automator[/red]")
                return

            # Login first
            print("Logging in to Instagram...")
            if not engagement_manager.instagram_automator.login("username", "password", headless=headless):
                print(f"[red]Login failed: {engagement_manager.instagram_automator.last_error}[/red]")
                return

            print(f"Following user: {username}")
            result = engagement_manager.instagram_automator.follow_user(username)

            if result.success:
                print(f"[green] Success: {result.message}[/green]")
            else:
                print(f"[red] Failed: {result.message}[/red]")

    except Exception as e:
        print(f"[red]Error: {e}[/red]")

@engage_app.command()
def instagram_comment(
    url: str = typer.Argument(..., help="Instagram post URL"),
    text: str = typer.Argument(..., help="Comment text"),
    headless: bool = typer.Option(True, help="Run in headless mode")
):
    """Comment on an Instagram post."""
    try:
        with BrowserManager() as manager:
            engagement_manager = EngagementManager()
            if not engagement_manager.initialize_instagram(manager, "ig_session"):
                print("[red]Failed to initialize Instagram automator[/red]")
                return

            # Login first
            print("Logging in to Instagram...")
            if not engagement_manager.instagram_automator.login("username", "password", headless=headless):
                print(f"[red]Login failed: {engagement_manager.instagram_automator.last_error}[/red]")
                return

            print(f"Commenting on post: {url}")
            result = engagement_manager.instagram_automator.comment_on_post(url, text)

            if result.success:
                print(f"[green] Success: {result.message}[/green]")
            else:
                print(f"[red] Failed: {result.message}[/red]")

    except Exception as e:
        print(f"[red]Error: {e}[/red]")

@engage_app.command()
def tiktok_like(
    url: str = typer.Argument(..., help="TikTok video URL"),
    headless: bool = typer.Option(True, help="Run in headless mode")
):
    """Like a TikTok video."""
    try:
        with BrowserManager() as manager:
            engagement_manager = EngagementManager()
            if not engagement_manager.initialize_tiktok(manager, "tiktok_session"):
                print("[red]Failed to initialize TikTok automator[/red]")
                return

            # Login first
            print("Logging in to TikTok...")
            if not engagement_manager.tiktok_automator.login(headless=headless):
                print(f"[red]Login failed: {engagement_manager.tiktok_automator.last_error}[/red]")
                return

            print(f"Liking video: {url}")
            result = engagement_manager.tiktok_automator.like_video(url)

            if result.success:
                print(f"[green] Success: {result.message}[/green]")
            else:
                print(f"[red] Failed: {result.message}[/red]")

    except Exception as e:
        print(f"[red]Error: {e}[/red]")

@engage_app.command()
def tiktok_follow(
    username: str = typer.Argument(..., help="TikTok username"),
    headless: bool = typer.Option(True, help="Run in headless mode")
):
    """Follow a TikTok creator."""
    try:
        with BrowserManager() as manager:
            engagement_manager = EngagementManager()
            if not engagement_manager.initialize_tiktok(manager, "tiktok_session"):
                print("[red]Failed to initialize TikTok automator[/red]")
                return

            # Login first
            print("Logging in to TikTok...")
            if not engagement_manager.tiktok_automator.login(headless=headless):
                print(f"[red]Login failed: {engagement_manager.tiktok_automator.last_error}[/red]")
                return

            print(f"Following creator: {username}")
            result = engagement_manager.tiktok_automator.follow_creator(username)

            if result.success:
                print(f"[green] Success: {result.message}[/green]")
            else:
                print(f"[red] Failed: {result.message}[/red]")

    except Exception as e:
        print(f"[red]Error: {e}[/red]")

@engage_app.command()
def tiktok_comment(
    url: str = typer.Argument(..., help="TikTok video URL"),
    text: str = typer.Argument(..., help="Comment text"),
    headless: bool = typer.Option(True, help="Run in headless mode")
):
    """Comment on a TikTok video."""
    try:
        with BrowserManager() as manager:
            engagement_manager = EngagementManager()
            if not engagement_manager.initialize_tiktok(manager, "tiktok_session"):
                print("[red]Failed to initialize TikTok automator[/red]")
                return

            # Login first
            print("Logging in to TikTok...")
            if not engagement_manager.tiktok_automator.login(headless=headless):
                print(f"[red]Login failed: {engagement_manager.tiktok_automator.last_error}[/red]")
                return

            print(f"Commenting on video: {url}")
            result = engagement_manager.tiktok_automator.comment_on_video(url, text)

            if result.success:
                print(f"[green] Success: {result.message}[/green]")
            else:
                print(f"[red] Failed: {result.message}[/red]")

    except Exception as e:
        print(f"[red]Error: {e}[/red]")

@engage_app.command()
def batch(
    config: str = typer.Argument(..., help="Batch configuration file (JSON)"),
    headless: bool = typer.Option(True, help="Run in headless mode")
):
    """Execute a batch of engagement actions from a configuration file."""
    try:
        import json
        from radar.engagement_models import EngagementBatch

        # Load batch configuration
        with open(config, 'r') as f:
            batch_config = json.load(f)

        # Create engagement manager
        engagement_manager = EngagementManager()

        # Initialize appropriate automator based on platform
        platform = batch_config.get('platform', 'instagram')
        with BrowserManager() as manager:
            if platform == 'instagram':
                if not engagement_manager.initialize_instagram(manager, "ig_session"):
                    print("[red]Failed to initialize Instagram automator[/red]")
                    return
                # Login
                if not engagement_manager.instagram_automator.login("username", "password", headless=headless):
                    print(f"[red]Login failed: {engagement_manager.instagram_automator.last_error}[/red]")
                    return
            elif platform == 'tiktok':
                if not engagement_manager.initialize_tiktok(manager, "tiktok_session"):
                    print("[red]Failed to initialize TikTok automator[/red]")
                    return
                # Login
                if not engagement_manager.tiktok_automator.login(headless=headless):
                    print(f"[red]Login failed: {engagement_manager.tiktok_automator.last_error}[/red]")
                    return
            else:
                print(f"[red]Unsupported platform: {platform}[/red]")
                return

            # Create batch
            actions = []
            for action_config in batch_config.get('actions', []):
                action_type = EngagementActionType[action_config['type'].upper()]
                platform_enum = EngagementPlatform[platform.upper()]

                action = EngagementAction(
                    action_type=action_type,
                    platform=platform_enum,
                    target_identifier=action_config['target'],
                    metadata=action_config.get('metadata', {})
                )
                actions.append(action)

            batch = EngagementBatch(
                actions=actions,
                platform=EngagementPlatform[platform.upper()],
                settings=batch_config.get('settings', {})
            )

            # Execute batch
            print(f"Executing batch with {len(batch.actions)} actions...")
            results = engagement_manager.execute_batch(batch)

            # Print summary
            successful = sum(1 for r in results if r.success)
            print(f"\n[bold]Batch Results:[/bold] {successful}/{len(results)} successful")

            for i, result in enumerate(results, 1):
                status = "[green][/green]" if result.success else "[red][/green]"
                print(f"{status} Action {i}: {result.action.action_type.value} on {result.action.target_identifier}")
                if not result.success:
                    print(f"   Error: {result.message}")

    except Exception as e:
        print(f"[red]Error: {e}[/red]")

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