import os
import asyncio
import typer
from rich import print
from typing import Optional
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
from radar.db import engine, Account, Proxy, create_db_and_tables
from sqlmodel import Session, select

app = typer.Typer()
account_app = typer.Typer()
proxy_app = typer.Typer()
app.add_typer(account_app, name="account", help="Manage social accounts")
app.add_typer(proxy_app, name="proxy", help="Manage proxies")

def get_llm():
    provider = os.getenv("LLM_PROVIDER", "mock")
    if provider == "gemini":
        return GeminiLLM(api_key=os.getenv("GEMINI_API_KEY", ""))
    return MockLLM()

@app.command()
def init():
    """Initialize database tables."""
    create_db_and_tables()
    print("[green]Database initialized.[/green]")

@account_app.command("add")
def account_add(platform: str, username: str, password: str, proxy_id: Optional[int] = None):
    """Add a new social media account."""
    with Session(engine) as session:
        acc = Account(platform=platform, username=username, password=password, proxy_id=proxy_id)
        session.add(acc)
        session.commit()
        print(f"[green]Account @{username} added to {platform}[/green]")

@account_app.command("list")
def account_list():
    """List all accounts."""
    with Session(engine) as session:
        accounts = session.exec(select(Account)).all()
        for a in accounts:
            p_str = f"Proxy: {a.proxy.host}:{a.proxy.port}" if a.proxy else "No Proxy"
            print(f"ID: {a.id} | [bold]{a.platform}[/bold] | @{a.username} | {p_str} | Status: {a.status}")

@proxy_app.command("add")
def proxy_add(host: str, port: int, user: Optional[str] = None, password: Optional[str] = None, protocol: str = "http"):
    """Add a new proxy."""
    with Session(engine) as session:
        p = Proxy(host=host, port=port, username=user, password=password, protocol=protocol)
        session.add(p)
        session.commit()
        print(f"[green]Proxy {host}:{port} added. ID: {p.id}[/green]")

@app.command()
def version():
    """Print version."""
    print("0.1.0")

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
