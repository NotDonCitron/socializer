import os
import random
from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models import SourceItem, Extract, ContentPack, PostJob, Lane, PackStatus, JobStatus, Platform
from app.schemas import ContentPackCreate

# Ensure tables exist
Base.metadata.create_all(bind=engine)

def seed():
    db = SessionLocal()
    
    # Check if we have data
    if db.query(SourceItem).count() > 0:
        print("Database already has data. Skipping seed.")
        db.close()
        return

    print("Seeding database...")

    # 1. Create Source Items
    sources = [
        "https://example.com/blog/python-tips",
        "https://news.ycombinator.com/item?id=12345",
        "https://github.com/fastapi/fastapi/releases/tag/0.100.0",
        "https://www.rust-lang.org/learn",
        "https://lexfridman.com/podcast",
    ]
    
    source_objs = []
    for uri in sources:
        item = SourceItem(uri=uri)
        db.add(item)
        source_objs.append(item)
    db.commit()

    # 2. Create Extracts (Mock Content)
    extract_texts = [
        "Python tip: Use enumerate() instead of range(len()) for cleaner loops.",
        "Hacker News discussion on the future of AI coding assistants.",
        "FastAPI 0.100.0 released with Pydantic V2 support! Huge performance boost.",
        "Rust ownership model prevents data races at compile time.",
        "Lex Fridman interviews Sam Altman about AGI timeline.",
    ]
    
    for i, item in enumerate(source_objs):
        extract = Extract(source_item_id=item.id, content=extract_texts[i])
        db.add(extract)
    db.commit()

    # 3. Create Content Packs (Drafts & Approved)
    lanes = [Lane.beginner, Lane.builder]
    
    for i in range(10):
        status = PackStatus.approved if i < 5 else PackStatus.draft
        lane = random.choice(lanes)
        
        pack = ContentPack(
            lane=lane,
            status=status,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5))
        )
        db.add(pack)
        
        # Link content? Model doesn't have direct link in ContentPack to Extract yet (simplified schema),
        # but logically they are related. We'll skip explicit link for this simple seed.
        
    db.commit()

    print("Seeding complete!")
    print(f"Created {len(sources)} SourceItems.")
    print("Created 10 ContentPacks (5 Approved, 5 Draft).")
    db.close()

if __name__ == "__main__":
    seed()
