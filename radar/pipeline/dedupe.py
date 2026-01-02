import hashlib
from radar.models import RawItem

def fingerprint(item: RawItem) -> str:
    base = (item.raw_text or "").strip().lower()
    base = " ".join(base.split())
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
