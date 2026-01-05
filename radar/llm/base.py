from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict

class LLMClient(ABC):
    @abstractmethod
    async def generate_post_json(self, *, raw_text: str, title: str, url: str, impact_score: int, flags: List[str], lang: str) -> dict:
        """Return dict matching our post schema fields for that language."""
        raise NotImplementedError

    @abstractmethod
    async def generate_instagram_caption(self, *, vision_analysis: Dict, custom_instructions: str = "", lang: str = "en") -> Dict[str, str]:
        """Generate Instagram caption and hashtags based on vision analysis."""
        raise NotImplementedError