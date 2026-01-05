#!/usr/bin/env python3
"""
Generate AI/tech content for draft content packs.
Following BMAD Quick Flow methodology.
"""
import json
import random
import sqlite3
from pathlib import Path
from typing import Dict, List, Any

# Content strategy
PLATFORMS = ["tiktok", "instagram", "youtube_shorts"]
AUDIENCE = "Tech professionals, AI enthusiasts, developers, tech entrepreneurs (25-45)"
BRAND_VOICE = "Professional + Educational (authoritative but accessible)"
CONTENT_PILLARS = [
    "AI Breakthroughs & News",
    "Developer Tools & Automation",
    "AI Ethics & Society Impact",
    "Productivity Hacks for Devs",
    "Tech Career & Trends"
]
CTA_OPTIONS = [
    "Follow for daily AI insights",
    "Link in bio for the full breakdown",
    "Comment your thoughts below",
    "Save this for later",
    "Share with your dev team"
]

# AI/Tech topics for content generation
TOPICS = [
    {
        "topic": "GPT-4 Turbo API cost reduction",
        "angle": "How OpenAI's price drop changes the AI automation game",
        "pillar": "AI Breakthroughs & News",
        "quality": 9
    },
    {
        "topic": "GitHub Copilot Workspace launch",
        "angle": "AI agents are now building entire features - here's what changed",
        "pillar": "Developer Tools & Automation",
        "quality": 9
    },
    {
        "topic": "AI watermarking requirements",
        "angle": "New regulations require AI-generated content labeling - what this means for creators",
        "pillar": "AI Ethics & Society Impact",
        "quality": 8
    },
    {
        "topic": "Cursor AI editor vs traditional IDEs",
        "angle": "Why developers are ditching VS Code for AI-first editors",
        "pillar": "Developer Tools & Automation",
        "quality": 8
    },
    {
        "topic": "AI replacing junior developers debate",
        "angle": "The truth about AI impact on entry-level tech jobs",
        "pillar": "Tech Career & Trends",
        "quality": 7
    },
    {
        "topic": "Local LLM performance on M3 chips",
        "angle": "Run GPT-4 level models on your laptop - no cloud needed",
        "pillar": "Developer Tools & Automation",
        "quality": 9
    },
    {
        "topic": "Anthropic Claude 3.5 Sonnet coding abilities",
        "angle": "This AI writes better code than most developers - tested on real projects",
        "pillar": "AI Breakthroughs & News",
        "quality": 9
    },
    {
        "topic": "AI hallucination prevention techniques",
        "angle": "3 prompting strategies that reduce AI errors by 80%",
        "pillar": "Developer Tools & Automation",
        "quality": 8
    }
]


def generate_hooks(topic: Dict[str, Any]) -> List[str]:
    """Generate 3 compelling hooks."""
    base = topic["angle"]
    return [
        f"🚨 {base.split('-')[0].strip()}",
        f"Everyone's talking about {topic['topic']}, but here's what they miss...",
        f"I tested {topic['topic']} for 30 days. Here's what happened."
    ]


def generate_script(topic: Dict[str, Any]) -> str:
    """Generate 60-90 second video script."""
    return f"""[HOOK - 0:00-0:05]
{topic['angle']}

[CONTEXT - 0:05-0:20]
So {topic['topic']} just dropped, and it's changing the way we think about AI development. Let me break down what actually matters here.

[MAIN POINTS - 0:20-0:50]

Point 1: The Technical Shift
This isn't just an incremental update. We're seeing fundamental changes in how these systems operate. [Show key metrics/examples]

Point 2: Practical Implications
For developers and tech teams, this means [specific actionable insight]. I've already implemented this in production and the results are significant.

Point 3: What's Next
Based on the roadmap and current trajectory, expect [forward-looking prediction] within the next 6-12 months.

[CALL TO ACTION - 0:50-0:60]
If you're building with AI, this changes your strategy. Link in bio for my detailed technical breakdown. Follow for more AI insights like this daily.

Drop a comment if you've tried this already - curious about real-world results.
"""


def generate_caption(topic: Dict[str, Any]) -> str:
    """Generate engaging caption."""
    return f"""{topic['angle']}

{topic['topic']} represents a significant shift in the AI landscape. Here's my technical analysis after hands-on testing:

✅ What works
✅ What doesn't
✅ How to implement this yourself

Full breakdown linked in bio. This is moving fast - staying informed is your competitive advantage.

What's your take on this development? Let me know below. 👇
"""


def generate_hashtags(topic: Dict[str, Any]) -> List[str]:
    """Generate 10-15 relevant hashtags."""
    base_tags = ["#AI", "#ArtificialIntelligence", "#MachineLearning", "#TechNews", "#Developer"]

    pillar_tags = {
        "AI Breakthroughs & News": ["#AINews", "#TechInnovation", "#AIResearch"],
        "Developer Tools & Automation": ["#DevTools", "#Automation", "#CodingLife", "#Programming"],
        "AI Ethics & Society Impact": ["#AIEthics", "#TechEthics", "#FutureOfWork"],
        "Productivity Hacks for Devs": ["#ProductivityHacks", "#DevLife", "#TechTips"],
        "Tech Career & Trends": ["#TechCareer", "#CareerAdvice", "#TechTrends"]
    }

    topic_specific = [
        f"#{topic['topic'].split()[0].replace('-', '')}",
        "#AITools",
        "#SoftwareEngineering",
        "#TechCommunity"
    ]

    all_tags = base_tags + pillar_tags.get(topic["pillar"], []) + topic_specific
    return list(set(all_tags))[:15]


def generate_carousel(topic: Dict[str, Any]) -> List[str]:
    """Generate 5-7 carousel slides (Instagram)."""
    return [
        f"📊 SLIDE 1 (COVER)\n{topic['angle']}\n\nSwipe for the technical breakdown →",

        "📈 SLIDE 2 (PROBLEM)\nWhy this matters:\n• Previous approach had limitations\n• Industry needed a shift\n• Timing is critical for early adopters",

        f"⚡ SLIDE 3 (SOLUTION)\n{topic['topic']} changes the game:\n• Key feature 1\n• Key feature 2\n• Key feature 3",

        "🔧 SLIDE 4 (IMPLEMENTATION)\nHow to apply this:\n1. Step one\n2. Step two\n3. Step three\n\nReal results: [Specific metrics]",

        "⚠️ SLIDE 5 (GOTCHAS)\nWatch out for:\n• Common mistake 1\n• Common mistake 2\n• Edge case to consider",

        "🚀 SLIDE 6 (NEXT STEPS)\nTake action:\n→ Link in bio for detailed guide\n→ Follow for daily AI insights\n→ Comment your questions below",

        "💡 SLIDE 7 (CTA)\nDon't miss future updates.\n\nFollow @youraccount\n\nWhat's your experience with this? Drop a comment! 👇"
    ]


def generate_content_pack(topic: Dict[str, Any]) -> Dict[str, Any]:
    """Generate complete content pack."""
    return {
        "topic": topic["topic"],
        "angle": topic["angle"],
        "pillar": topic["pillar"],
        "quality_score": topic["quality"],
        "platforms": PLATFORMS,
        "hooks": generate_hooks(topic),
        "script": generate_script(topic),
        "caption": generate_caption(topic),
        "hashtags": generate_hashtags(topic),
        "carousel": generate_carousel(topic),
        "cta": random.choice(CTA_OPTIONS)
    }


def update_db_content_pack(pack_id: str, content: Dict[str, Any], db_path: str):
    """Update content pack in database."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        UPDATE content_packs
        SET
            format = ?,
            hooks_json = ?,
            script_text = ?,
            carousel_json = ?,
            caption_text = ?,
            hashtags_json = ?
        WHERE id = ?
    """, (
        "video_short",
        json.dumps(content["hooks"]),
        content["script"],
        json.dumps(content["carousel"]),
        content["caption"],
        json.dumps(content["hashtags"]),
        pack_id
    ))

    conn.commit()
    conn.close()


def main():
    db_path = "/home/kek/socializer/socializer_ide.sqlite"
    export_dir = Path("/home/kek/socializer/export")
    export_dir.mkdir(exist_ok=True)

    # IDs of the first 5 draft packs
    pack_ids = [
        "8d2f8101-39cb-4b56-a103-4ee99da375fc",
        "a46dfda0-0a65-49b6-986c-af60bded2e11",
        "5ce14d59-40ef-4a5c-939b-6a03454a5ff5",
        "b9ae07be-a5d8-4f9c-ac26-2bd40680c4fa",
        "fea78af6-7339-4d8f-b5bf-a9e97179f990"
    ]

    # Filter topics by quality (8+)
    quality_topics = [t for t in TOPICS if t["quality"] >= 8]
    selected_topics = quality_topics[:5]

    print(f"🚀 Generating content for {len(selected_topics)} topics...")
    print(f"Quality filter: {len(quality_topics)}/{len(TOPICS)} topics passed (score >= 8)")
    print()

    for pack_id, topic in zip(pack_ids, selected_topics):
        print(f"📝 Processing: {topic['topic']}")

        # Generate content
        content = generate_content_pack(topic)

        # Update database
        update_db_content_pack(pack_id, content, db_path)

        # Save JSON export
        export_path = export_dir / f"content_pack_{pack_id}.json"
        with open(export_path, "w") as f:
            json.dump(content, f, indent=2)

        print(f"   ✅ Saved to {export_path.name}")
        print(f"   📊 Quality: {content['quality_score']}/10")
        print(f"   🎯 Pillar: {content['pillar']}")
        print()

    print("=" * 60)
    print("✅ COMPLETE")
    print(f"Generated content for {len(selected_topics)} packs")
    print(f"Filtered out {len(TOPICS) - len(quality_topics)} low-quality topics")
    print(f"Export location: {export_dir}")
    print()
    print("Next steps:")
    print("- Review JSON files in export/")
    print("- Check updated database records")
    print("- Approve packs via API if satisfied")


if __name__ == "__main__":
    main()
