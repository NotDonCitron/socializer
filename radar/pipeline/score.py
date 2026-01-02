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

def semver_major_bump(tag: str) -> bool:
    # very rough: detects x.y.z where x is major; you can improve later
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", tag)
    if not m:
        return False
    major = int(m.group(1))
    return major >= 2  # not perfect; MVP heuristic

def score_item(raw: RawItem) -> ScoredItem:
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

    if raw.kind == "release" and semver_major_bump(raw.external_id):
        score += 45
        flags.append("major")

    score = max(0, min(100, score))
    tags = list(dict.fromkeys(raw.metadata.get("tags", [])))  # unique keep order
    return ScoredItem(raw=raw, impact_score=score, flags=flags, tags=tags)
