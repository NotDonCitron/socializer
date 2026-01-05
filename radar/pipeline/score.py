import re
from radar.models import RawItem, ScoredItem

HIGH_KEYWORDS = [
    ("breaking", 35, "breaking"),
    ("deprecated", 35, "deprecation"),
    ("deprecat", 35, "deprecation"),
    ("removed", 35, "removed"),
    ("migration", 35, "migration"),
    ("rename", 20, "rename"),
    ("security", 25, "security"),
    ("vulnerability", 25, "security"),
    ("cve-", 25, "security"),
    ("tool calling", 30, "tool-calling"),
    ("function calling", 30, "tool-calling"),
    ("json schema", 30, "schema"),
    ("structured output", 30, "schema"),
    ("response format", 30, "schema"),
]
MED_KEYWORDS = [
    ("performance", 10, "performance"),
    ("faster", 10, "performance"),
    ("latency", 10, "performance"),
    ("new provider", 10, "providers"),
    ("support", 10, "support"),
]

def semver_major_bump(new_tag: str, old_tag: str | None) -> bool:
    def get_major(tag: str | None) -> int | None:
        if not tag:
            return None
        m = re.search(r"(\d+)\.", tag)
        return int(m.group(1)) if m else None

    new_major = get_major(new_tag)
    old_major = get_major(old_tag)

    if new_major is not None and old_major is not None:
        return new_major > old_major
    
    # Fallback for first time seen or non-semver
    if new_major is not None and old_major is None:
        return new_major >= 1
    
    return False

def score_item(raw: RawItem, prev_raw: RawItem | None = None) -> ScoredItem:
    text = (raw.raw_text or "").lower()
    score = 10
    flags: list[str] = []
    for kw, points, flag in HIGH_KEYWORDS:
        if kw in text:
            score += points
            if flag not in flags:
                flags.append(flag)
    for kw, points, flag in MED_KEYWORDS:
        if kw in text:
            score += points
            if flag not in flags:
                flags.append(flag)

    if raw.kind == "release":
        prev_version = prev_raw.external_id if prev_raw else None
        if semver_major_bump(raw.external_id, prev_version):
            score += 45
            flags.append("major")

    score = max(0, min(100, score))
    tags = list(dict.fromkeys(raw.metadata.get("tags", [])))  # unique keep order
    return ScoredItem(raw=raw, impact_score=score, flags=flags, tags=tags)
