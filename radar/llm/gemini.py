import os
import json

# Optional import with fallback
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

from typing import List, Optional
from radar.llm.base import LLMClient

class GeminiLLM(LLMClient):
    def __init__(self, api_key: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("Google Generative AI package not installed. Install with: pip install google-generativeai")

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def generate_post_json(self, *, raw_text: str, title: str, url: str, impact_score: int, flags: List[str], lang: str) -> dict:

        # Construct a clear prompt for the model
        prompt = f"""
        You are an expert social media manager. Create a JSON response for a {lang} post.

        Context:
        - Title: {title}
        - Description/Context: {raw_text}
        - URL: {url}
        - Vibe/Flags: {', '.join(flags)}

        Output Schema (JSON only):
        {{
            "title": "Engaging title",
            "hook": "Catchy first line/hook",
            "short": "Short caption for TikTok/Reels (max 150 chars)",
            "medium": "Longer caption (optional)",
            "hashtags": "#tag1 #tag2",
            "action_items": ["item1"],
            "confidence": "high|medium|low"
        }}
        """

        try:
            # Generate content
            response = self.model.generate_content(prompt)

            # Basic cleanup to ensure JSON
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]

            return json.loads(text)

        except Exception as e:
            print(f"Gemini generation error: {e}")
            # Return a fallback structure so the app doesn't crash
            return {
                "title": title,
                "hook": "Check this out!",
                "short": f"New video: {title}",
                "hashtags": "#viral #new",
                "confidence": "low"
            }

    async def generate_instagram_caption(self, *, vision_analysis: dict, custom_instructions: str = "", lang: str = "en") -> dict:
        """Generate Instagram caption and hashtags based on vision analysis."""

        # Construct prompt for Instagram caption generation
        prompt = f"""
        You are a social media expert creating engaging Instagram captions. Based on this image analysis, create a compelling caption and hashtags.

        Image Analysis:
        - Objects: {', '.join(vision_analysis.get('objects', []))}
        - Mood/Atmosphere: {vision_analysis.get('mood', 'unknown')}
        - Colors: {', '.join(vision_analysis.get('colors', []))}
        - Scene: {vision_analysis.get('scene', 'unknown')}
        - People: {vision_analysis.get('people_count', 0)} people
        - Activities: {', '.join(vision_analysis.get('activities', []))}
        - Text in image: "{vision_analysis.get('text_content', '')}"

        {f"Additional instructions: {custom_instructions}" if custom_instructions else ""}

        Create a JSON response with:
        {{
            "caption": "Engaging caption (80-150 characters, {lang} language)",
            "hashtags": "10-15 relevant hashtags (space-separated, no # symbols)",
            "mood_match": "how well the caption matches the image mood",
            "engagement_potential": "high|medium|low"
        }}

        Make it authentic and engaging for Instagram audience.
        """

        try:
            response = self.model.generate_content(prompt)

            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]

            result = json.loads(text)

            # Ensure we have required fields
            result.setdefault("caption", "Beautiful moment captured!")
            result.setdefault("hashtags", "photo beautiful moment life")
            result.setdefault("mood_match", "good")
            result.setdefault("engagement_potential", "medium")

            return result

        except Exception as e:
            print(f"Gemini caption generation error: {e}")
            return {
                "caption": "Amazing capture!",
                "hashtags": "photo beautiful amazing moment",
                "mood_match": "neutral",
                "engagement_potential": "medium"
            }