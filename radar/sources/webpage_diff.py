from __future__ import annotations
import httpx, hashlib
from radar.models import RawItem, SourceConfig

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

async def fetch_page(source: SourceConfig) -> RawItem:
    assert source.url, "url required"
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        r = await client.get(str(source.url), headers={"User-Agent": "ai-agent-radar/0.1"})
        r.raise_for_status()
        html = r.text

    raw_hash = _sha(html)
    return RawItem(
        source_id=source.id,
        kind="webpage",
        external_id="snapshot",
        title=f"Webpage update: {source.id}",
        url=str(source.url),
        raw_text=html,
        raw_hash=raw_hash,
        metadata={"tags": source.tags, "priority": source.priority},
    )
