from __future__ import annotations
from pathlib import Path
from radar.models import GeneratedPost, StackConfig
from datetime import datetime
from radar.pipeline.normalize import slugify

def _frontmatter(post: GeneratedPost, lang: str, noindex: bool) -> str:
    tags = post.tags
    id_slug = slugify(post.external_id)
    permalink = f"/updates/{post.source_id}/{id_slug}/"
    fm = [
        "---",
        f'title: "{(post.title_en if lang=="en" else post.title_de) or ""}"',
        f"impact_score: {post.impact_score}",
        f"source_id: {post.source_id}",
        f"external_id: {post.external_id}",
        f"tags: {tags}",
        f"url: {post.url}",
        f"updated_at: {datetime.utcnow().isoformat()}Z",
        f"permalink: {permalink}",
        f"lang: {lang}",
        f"id_slug: {id_slug}",
    ]
    if noindex:
        fm.append("robots: noindex")
    fm.append("---")
    return "\n".join(fm)

def render_posts(cfg: StackConfig | None, posts: list[GeneratedPost], output_dir: str = "content") -> None:
    out_base = Path(output_dir)
    for p in posts:
        # If cfg is None, use default threshold of 0
        threshold = cfg.posting.post_if_impact_gte if cfg else 0
        noindex = p.impact_score < threshold or p.confidence == "low"

        # EN
        if "en" in p.languages:
            path = out_base / "en" / "updates" / p.source_id
            path.mkdir(parents=True, exist_ok=True)
            id_slug = slugify(p.external_id)
            file = path / f"{id_slug}.md"

            body = f"{p.hook_en}\n\n{p.short_en}\n\n"
            if p.medium_en:
                body += f"\n## Details\n\n{p.medium_en}\n"
            body += "\n## Action items\n" + "\n".join([f"- {x}" for x in p.action_items])
            body += "\n\n## Sources\n" + "\n".join([f"- {s}" for s in p.sources])

            file.write_text(_frontmatter(p, "en", noindex) + "\n\n" + body, encoding="utf-8")

        # DE (optional)
        if "de" in p.languages:
            path = out_base / "de" / "updates" / p.source_id
            path.mkdir(parents=True, exist_ok=True)
            id_slug = slugify(p.external_id)
            file = path / f"{id_slug}.md"

            body = f"{p.hook_de}\n\n{p.short_de}\n\n"
            if p.medium_de:
                body += f"\n## Details\n\n{p.medium_de}\n"
            body += "\n## Action items\n" + "\n".join([f"- {x}" for x in p.action_items])
            body += "\n\n## Quellen\n" + "\n".join([f"- {s}" for s in p.sources])

            file.write_text(_frontmatter(p, "de", noindex) + "\n\n" + body, encoding="utf-8")
