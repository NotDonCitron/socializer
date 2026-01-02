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
