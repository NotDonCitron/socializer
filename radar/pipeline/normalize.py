import re

def normalize_text(text: str) -> str:
    t = text.strip()
    t = re.sub(r"\r\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t
