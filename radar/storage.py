import sqlite3
from pathlib import Path
from radar.models import RawItem, GeneratedPost

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_items (
    source_id TEXT,
    kind TEXT,
    external_id TEXT,
    title TEXT,
    url TEXT,
    published_at TEXT,
    raw_text TEXT,
    raw_hash TEXT,
    metadata_json TEXT,
    PRIMARY KEY (source_id, kind, external_id)
);

CREATE TABLE IF NOT EXISTS posts (
    source_id TEXT,
    external_id TEXT,
    kind TEXT,
    post_json TEXT,
    PRIMARY KEY (source_id, external_id)
);
"""

def connect(sqlite_path: str) -> sqlite3.Connection:
    Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(sqlite_path)
    con.execute("PRAGMA journal_mode=WAL;")
    con.executescript(SCHEMA)
    return con

def upsert_raw(con: sqlite3.Connection, item: RawItem) -> None:
    import json
    con.execute(
        """INSERT OR REPLACE INTO raw_items
           (source_id, kind, external_id, title, url, published_at, raw_text, raw_hash, metadata_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            item.source_id,
            item.kind,
            item.external_id,
            item.title,
            item.url,
            item.published_at,
            item.raw_text,
            item.raw_hash,
            json.dumps(item.metadata),
        ),
    )
    con.commit()

def raw_exists_with_same_hash(con: sqlite3.Connection, source_id: str, kind: str, external_id: str, raw_hash: str) -> bool:
    cur = con.execute(
        "SELECT raw_hash FROM raw_items WHERE source_id=? AND kind=? AND external_id=?",
        (source_id, kind, external_id),
    )
    row = cur.fetchone()
    return bool(row and row[0] == raw_hash)

def get_latest_raw_item(con: sqlite3.Connection, source_id: str, kind: str) -> RawItem | None:
    import json
    cur = con.execute(
        "SELECT source_id, kind, external_id, title, url, published_at, raw_text, raw_hash, metadata_json "
        "FROM raw_items WHERE source_id=? AND kind=? ORDER BY published_at DESC LIMIT 1",
        (source_id, kind),
    )
    row = cur.fetchone()
    if not row:
        return None
    return RawItem(
        source_id=row[0],
        kind=row[1],
        external_id=row[2],
        title=row[3],
        url=row[4],
        published_at=row[5],
        raw_text=row[6],
        raw_hash=row[7],
        metadata=json.loads(row[8]),
    )

def upsert_post(con: sqlite3.Connection, post: GeneratedPost) -> None:
    import json
    con.execute(
        "INSERT OR REPLACE INTO posts (source_id, external_id, kind, post_json) VALUES (?, ?, ?, ?)",
        (post.source_id, post.external_id, post.kind, post.model_dump_json()),
    )
    con.commit()