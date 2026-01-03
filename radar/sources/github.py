from __future__ import annotations
import httpx, hashlib
from datetime import datetime
from radar.models import RawItem, SourceConfig

GITHUB_API = "https://api.github.com"

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

async def fetch_releases(source: SourceConfig, token: str) -> list[RawItem]:
    assert source.repo, "repo required"
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"{GITHUB_API}/repos/{source.repo}/releases"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        releases = r.json()

    items: list[RawItem] = []
    for rel in releases[:20]:  # MVP limit
        if rel.get("draft"):
            continue
        tag = rel.get("tag_name") or rel.get("name") or "unknown"
        body = rel.get("body") or ""
        title = rel.get("name") or f"{source.repo} {tag}"
        html_url = rel.get("html_url") or ""
        published = rel.get("published_at")  # iso string
        raw_hash = _sha(body.strip() + "|" + str(published))

        items.append(
            RawItem(
                source_id=source.id,
                kind="release",
                external_id=tag,
                title=title,
                url=html_url,
                published_at=published,
                raw_text=body,
                raw_hash=raw_hash,
                metadata={"repo": source.repo, "tags": source.tags, "priority": source.priority},
            )
        )
    return items
