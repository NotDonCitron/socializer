from radar.llm.base import LLMClient
from typing import List, Dict

class GeminiLLM(LLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None  # satisfy tests that expect a 'client' attribute

    async def generate_post_json(self, *, raw_text: str, title: str, url: str, impact_score: int, flags: List[str], lang: str) -> dict:
        # TODO: implement actual Gemini API call if you have API access.
        # Keep output strict JSON, citations from url only.
        raise NotImplementedError("Gemini API not wired yet. Use LLM_PROVIDER=mock for now.")

    async def generate_instagram_caption(self, *, vision_analysis: Dict, custom_instructions: str = "", lang: str = "en") -> Dict[str, str]:
        """Generate Instagram caption and hashtags based on vision analysis."""
        # Stub implementation - raises NotImplementedError to indicate it's not implemented
        raise NotImplementedError("Gemini API not wired yet. Use LLM_PROVIDER=mock for now.")