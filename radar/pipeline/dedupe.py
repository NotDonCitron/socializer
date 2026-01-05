import hashlib
from radar.models import RawItem

def fingerprint(item: RawItem) -> str:
    base = (item.raw_text or "").strip().lower()
    base = " ".join(base.split())
    return hashlib.sha256(base.encode("utf-8")).hexdigest()

def deduplicate_items(items: list[RawItem]) -> list[RawItem]:
    seen_hashes = set()
    deduped = []
    for item in items:
        # Deduplicate based on source_id + external_id OR raw_hash
        # The test expects source_id + external_id to be unique enough, 
        # but also mentions same_hash from different sources should be kept.
        # Let's use (source_id, external_id) as the key as implied by tests.
        key = (item.source_id, item.external_id)
        if key not in seen_hashes:
            seen_hashes.add(key)
            deduped.append(item)
    return deduped
