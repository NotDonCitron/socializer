from radar.models import ScoredItem, GeneratedPost, StackConfig
from radar.llm.base import LLMClient

async def generate_posts(cfg: StackConfig, scored: list[ScoredItem], llm: LLMClient) -> list[GeneratedPost]:
    out: list[GeneratedPost] = []
    for s in scored:
        if s.impact_score < cfg.posting.post_if_impact_gte:
            continue

        # EN always
        en = await llm.generate_post_json(
            raw_text=s.raw.raw_text,
            title=s.raw.title or "",
            url=s.raw.url,
            impact_score=s.impact_score,
            flags=s.flags,
            lang="en",
        )

        medium_en = None
        if s.impact_score >= cfg.posting.medium_if_impact_gte:
            medium_en = en.get("medium")

        post = GeneratedPost(
            source_id=s.raw.source_id,
            external_id=s.raw.external_id,
            kind=s.raw.kind,
            url=s.raw.url,
            impact_score=s.impact_score,
            flags=s.flags,
            tags=s.tags,
            languages=["en"],

            title_en=en["title"],
            hook_en=en["hook"],
            short_en=en["short"],
            medium_en=medium_en,

            action_items=en.get("action_items", []),
            sources=en.get("sources", [s.raw.url]),
            confidence=en.get("confidence", "medium"),
        )

        # DE only if high impact
        if "de" in cfg.languages and s.impact_score >= cfg.posting.generate_de_if_impact_gte:
            de = await llm.generate_post_json(
                raw_text=s.raw.raw_text,
                title=s.raw.title or "",
                url=s.raw.url,
                impact_score=s.impact_score,
                flags=s.flags,
                lang="de",
            )
            post.languages.append("de")
            post.title_de = de["title"]
            post.hook_de = de["hook"]
            post.short_de = de["short"]
            post.medium_de = de.get("medium")

        out.append(post)
    return out