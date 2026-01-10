import os
import json
import google.generativeai as genai
from typing import List, Optional
from radar.llm.base import LLMClient

class GeminiLLM(LLMClient):
    def __init__(self, api_key: Optional[str] = None):
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
