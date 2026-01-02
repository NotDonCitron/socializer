from __future__ import annotations
from datetime import datetime
from pathlib import Path
from radar.models import GeneratedPost

def week_key(dt: datetime) -> str:
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"

def render_weekly(posts: list[GeneratedPost], output_dir: str = "content", lang: str = "en") -> str:
    now = datetime.utcnow()
    key = week_key(now)
    out = Path(output_dir) / lang / "weekly"
    out.mkdir(parents=True, exist_ok=True)
    file = out / f"{key}.md"

    top = sorted(posts, key=lambda p: p.impact_score, reverse=True)[:20]
    lines = [
        "---",
        f'title: "Weekly Digest {key}"',
        f"generated_at: {now.isoformat()}Z",
        "---",
        "",
        "## High impact updates",
        "",
    ]
    for p in top:
        title = p.title_en if lang == "en" else (p.title_de or p.title_en)
        lines.append(f"- **{title}** (impact {p.impact_score}) — {p.url}")

    file.write_text("\n".join(lines), encoding="utf-8")
    return str(file)
