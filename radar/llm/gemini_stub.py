from radar.llm.base import LLMClient
from typing import List

class GeminiLLM(LLMClient):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_post_json(self, *, raw_text: str, title: str, url: str, impact_score: int, flags: List[str], lang: str) -> dict:
        # TODO: implement actual Gemini API call if you have API access.
        # Keep output strict JSON, citations from url only.
        raise NotImplementedError("Gemini API not wired yet. Use LLM_PROVIDER=mock for now.")
