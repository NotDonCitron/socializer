import re

def normalize_text(text: str) -> str:
    t = text.strip()
    t = re.sub(r"\r\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t

_SLUG_INVALID = re.compile(r"[^a-z0-9]+")
_SLUG_DASHES = re.compile(r"-{2,}")

def slugify(value: str) -> str:
    v = (value or "").strip().lower()
    v = v.replace("_", "-").replace(" ", "-")
    v = _SLUG_INVALID.sub("-", v)
    v = _SLUG_DASHES.sub("-", v)
    v = v.strip("-")
    return v or "item"

def normalize_item(item: "RawItem") -> "RawItem":
    from radar.models import RawItem
    
    # Trim basic fields
    title = (item.title or "").strip()
    raw_text = normalize_text(item.raw_text or "")
    
    # Trim tags in metadata if present
    metadata = item.metadata.copy()
    if "tags" in metadata and isinstance(metadata["tags"], list):
        metadata["tags"] = [t.strip() for t in metadata["tags"] if t.strip()]
        
    # Recursive trim for complex metadata (as seen in tests)
    def trim_recursive(obj):
        if isinstance(obj, dict):
            return {k: trim_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [trim_recursive(v) for v in obj]
        elif isinstance(obj, str):
            return obj.strip()
        return obj

    if metadata:
        metadata = trim_recursive(metadata)

    return RawItem(
        source_id=item.source_id,
        kind=item.kind,
        external_id=item.external_id,
        title=title,
        url=item.url,
        published_at=item.published_at,
        raw_text=raw_text,
        raw_hash=item.raw_hash,
        metadata=metadata
    )
