from __future__ import annotations
from datetime import datetime
from pathlib import Path
from radar.models import GeneratedPost
from radar.pipeline.normalize import slugify

def week_key(dt: datetime) -> str:
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"

def render_weekly(posts: list[GeneratedPost], output_dir: str = "content", lang: str = "en") -> str:
    now = datetime.utcnow()
    key = week_key(now)
    out = Path(output_dir) / lang
    out.mkdir(parents=True, exist_ok=True)
    file = out / f"weekly_digest.md"

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
        id_slug = slugify(p.external_id)
        permalink = f"/updates/{p.source_id}/{id_slug}/"
        lines.append(f"- **[{title}]({permalink})** (impact {p.impact_score})")

    file.write_text("\n".join(lines), encoding="utf-8")
    return str(file)