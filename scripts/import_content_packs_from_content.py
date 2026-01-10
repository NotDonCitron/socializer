import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import re
import yaml
import uuid
import json

# HACK: add socializer-api to path
sys.path.append(os.path.join(os.getcwd(), "socializer-api"))

from socializer_api import db


FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n(.*)$", re.S)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text.strip()
    raw = match.group(1)
    body = match.group(2)
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        data = {}
    return data, body.strip()


def extract_hook(body: str) -> str:
    for line in body.splitlines():
        candidate = line.strip()
        if candidate and not candidate.startswith("#") and candidate != "---":
            return candidate
    return ""


def extract_sources(body: str) -> str | None:
    for heading in ("Sources", "Quellen"):
        marker = f"## {heading}"
        if marker not in body:
            continue
        section = body.split(marker, 1)[1]
        lines = []
        for line in section.splitlines()[1:]:
            if line.strip().startswith("## "):
                break
            if line.strip().startswith("- "):
                lines.append(line.strip()[2:])
        if lines:
            return "\n".join(lines)
    return None


def normalize_tags(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        tags = [value]
    else:
        tags = list(value)
    return [t.strip().lstrip("#") for t in tags if t]


def file_created_at(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(db.ISO_FMT)


def get_or_create_source_item(conn, canonical_url: str, title: str) -> str:
    cur = conn.cursor()
    cur.execute("SELECT id FROM source_items WHERE canonical_url = ?", (canonical_url,))
    row = cur.fetchone()
    if row:
        return row["id"]

    source_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO source_items (id, source_type, canonical_url, title, fetched_at, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            source_id,
            "markdown",
            canonical_url,
            title,
            db.utc_now_iso(),
            "imported",
        ),
    )
    conn.commit()
    return source_id


def upsert_content_pack(
    conn,
    source_item_id: str,
    lane: str,
    pack_format: str,
    hooks: list[str],
    script_text: str,
    caption_text: str | None,
    hashtags: list[str],
    sources_block_text: str | None,
    risk_flags: list[str],
) -> tuple[str, str]:
    cur = conn.cursor()
    cur.execute("SELECT id FROM content_packs WHERE source_item_id = ?", (source_item_id,))
    row = cur.fetchone()
    if row:
        pack_id = row["id"]
        cur.execute(
            """
            UPDATE content_packs
            SET lane = ?, format = ?, hooks_json = ?, script_text = ?, caption_text = ?,
                hashtags_json = ?, sources_block_text = ?, risk_flags_json = ?
            WHERE id = ?
            """,
            (
                lane,
                pack_format,
                json.dumps(hooks),
                script_text,
                caption_text,
                json.dumps(hashtags),
                sources_block_text,
                json.dumps(risk_flags),
                pack_id,
            ),
        )
        conn.commit()
        return pack_id, "updated"

    pack_id = db.insert_content_pack(
        lane=lane,
        format=pack_format,
        status="draft",
        source_item_id=source_item_id,
        hooks=hooks,
        script_text=script_text,
        caption_text=caption_text,
        hashtags=hashtags,
        sources_block_text=sources_block_text,
        risk_flags=risk_flags,
    )
    return pack_id, "inserted"


def import_posts(content_root: Path, db_path: str) -> tuple[int, int]:
    db.init_db(db_path)
    conn = db.get_connection(db_path)
    inserted = 0
    updated = 0

    md_files = sorted(content_root.rglob("*.md"))
    for path in md_files:
        rel = path.relative_to(content_root).as_posix()
        if "/weekly/" in rel or rel.endswith("weekly_digest.md"):
            continue

        text = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)

        title = frontmatter.get("title") or path.stem
        canonical_url = f"content/{rel}"
        source_item_id = get_or_create_source_item(conn, canonical_url, title)
        hook = extract_hook(body)
        tags = normalize_tags(frontmatter.get("tags"))
        sources_block = extract_sources(body)
        risk_flags = []
        if frontmatter.get("robots") == "noindex":
            risk_flags.append("noindex")

        pack_id, action = upsert_content_pack(
            conn,
            source_item_id=source_item_id,
            lane="builder",
            pack_format="markdown",
            hooks=[hook] if hook else [],
            script_text=body,
            caption_text=title if title else hook,
            hashtags=tags,
            sources_block_text=sources_block,
            risk_flags=risk_flags,
        )

        if action == "inserted":
            created_at = frontmatter.get("updated_at") or file_created_at(path)
            cur = conn.cursor()
            cur.execute("UPDATE content_packs SET created_at = ? WHERE id = ?", (created_at, pack_id))
            conn.commit()
            inserted += 1
        else:
            updated += 1

    conn.close()
    return inserted, updated


def main() -> None:
    repo_root = Path(os.getcwd())
    content_root = repo_root / "content"
    db_path = os.getenv("SOCIALIZER_DB", str(repo_root / "socializer.sqlite"))

    if not content_root.exists():
        print(f"Content folder not found: {content_root}")
        return

    inserted, updated = import_posts(content_root, db_path)
    print(f"Imported {inserted} content packs, updated {updated} existing.")


if __name__ == "__main__":
    main()
