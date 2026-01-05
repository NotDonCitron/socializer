"""
Vision API integration for image analysis in Instagram AI flow.
Supports OpenAI GPT-4V and Google Gemini Vision.
"""
import os
import base64
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Optional imports with fallbacks
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

class VisionAnalyzer:
    """Handles image analysis using vision-capable LLMs."""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        self.provider = provider.lower()

        if self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI package not installed. Install with: pip install openai")
            self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4o"  # Vision-capable model
        elif self.provider == "gemini":
            if not GEMINI_AVAILABLE:
                raise ImportError("Google Generative AI package not installed. Install with: pip install google-generativeai")
            genai.configure(api_key=api_key or os.getenv("GEMINI_API_KEY"))
            self.client = genai.GenerativeModel('gemini-1.5-pro')
        else:
            raise ValueError(f"Unsupported vision provider: {provider}")

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API calls."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _is_image_file(self, file_path: str) -> bool:
        """Check if file is a supported image format."""
        ext = Path(file_path).suffix.lower()
        return ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']

    async def analyze_image(self, image_path: str) -> Dict:
        """
        Analyze image and return structured insights.

        Returns:
            {
                "objects": ["object1", "object2"],
                "mood": "description",
                "colors": ["color1", "color2"],
                "text_content": "extracted text",
                "scene": "indoor/outdoor/etc",
                "people_count": int,
                "activities": ["activity1"],
                "hashtags_suggestions": ["#tag1", "#tag2"]
            }
        """
        if not self._is_image_file(image_path):
            raise ValueError(f"Unsupported image format: {image_path}")

        if self.provider == "openai":
            return await self._analyze_openai(image_path)
        elif self.provider == "gemini":
            return await self._analyze_gemini(image_path)

    async def _analyze_openai(self, image_path: str) -> Dict:
        """Analyze image using OpenAI GPT-4V."""
        base64_image = self._encode_image(image_path)

        prompt = """
        Analyze this image and provide a detailed JSON response with the following structure:
        {
            "objects": ["list", "of", "visible", "objects"],
            "mood": "emotional tone or atmosphere (e.g., happy, dramatic, peaceful)",
            "colors": ["dominant", "colors"],
            "text_content": "any visible text in the image",
            "scene": "setting (indoor, outdoor, urban, nature, etc.)",
            "people_count": 0,
            "activities": ["activities", "people", "are", "doing"],
            "hashtags_suggestions": ["#relevant", "#hashtags"],
            "caption_ideas": ["2-3", "caption", "suggestions"]
        }

        Be specific and detailed. If uncertain about something, use "unknown".
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )

            result_text = response.choices[0].message.content.strip()

            # Clean JSON response
            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            elif result_text.startswith("```"):
                result_text = result_text[3:-3]

            return json.loads(result_text)

        except Exception as e:
            print(f"OpenAI vision analysis error: {e}")
            return self._fallback_analysis()

    async def _analyze_gemini(self, image_path: str) -> Dict:
        """Analyze image using Google Gemini Vision."""
        try:
            # Upload file to Gemini
            uploaded_file = genai.upload_file(image_path)

            prompt = """
            Analyze this image and provide a detailed JSON response with the following structure:
            {
                "objects": ["list", "of", "visible", "objects"],
                "mood": "emotional tone or atmosphere",
                "colors": ["dominant", "colors"],
                "text_content": "any visible text in the image",
                "scene": "setting (indoor, outdoor, urban, nature, etc.)",
                "people_count": 0,
                "activities": ["activities", "people", "are", "doing"],
                "hashtags_suggestions": ["#relevant", "#hashtags"],
                "caption_ideas": ["2-3", "caption", "suggestions"]
            }

            Be specific and detailed. If uncertain about something, use "unknown".
            """

            response = self.client.generate_content([uploaded_file, prompt])
            result_text = response.text.strip()

            # Clean JSON response
            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            elif result_text.startswith("```"):
                result_text = result_text[3:-3]

            return json.loads(result_text)

        except Exception as e:
            print(f"Gemini vision analysis error: {e}")
            return self._fallback_analysis()

    def _fallback_analysis(self) -> Dict:
        """Return safe fallback analysis when API fails."""
        return {
            "objects": ["unknown"],
            "mood": "neutral",
            "colors": ["unknown"],
            "text_content": "",
            "scene": "unknown",
            "people_count": 0,
            "activities": [],
            "hashtags_suggestions": ["#photo", "#content"],
            "caption_ideas": ["Check this out!"]
        }