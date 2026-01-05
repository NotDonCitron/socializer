import os
import subprocess
from typing import Dict, Optional, Tuple, List

# Try to import LLMClient, fallback if not available
try:
    from radar.llm.base import LLMClient
except ImportError:
    class LLMClient: pass

# Default presets based on user preferences
DEFAULT_PRESETS = {
    "viral": ("Viral/FYP", "#fyp #foryou #viral #trending #foryoupage"),
    "gaming": ("Gaming", "#gaming #gamer #twitch #streamer #gamingcommunity"),
    "tech": ("Tech/Coding", "#tech #coding #developer #programming #ai #software"),
    "funny": ("Funny", "#funny #comedy #humor #lol #memes"),
    "music": ("Music", "#music #song #musician #producer #beats"),
    "food": ("Food", "#food #foodie #recipe #cooking #yummy"),
    "fitness": ("Fitness", "#fitness #gym #workout #health #motivation"),
}

class ContentManager:
    """
    Manages content preparation: hashtags, captions, and eventually AI generation.
    """
    def __init__(self, presets: Optional[Dict[str, Tuple[str, str]]] = None, llm: Optional[LLMClient] = None):
        self.presets = presets or DEFAULT_PRESETS
        self.llm = llm

    def get_hashtags(self, category_keys: List[str]) -> str:
        """
        Get combined hashtags for specific categories.
        
        Args:
            category_keys: List of keys (e.g. ['viral', 'tech']) or indices (e.g. ['1', '3'])
        
        Returns:
            String of space-separated hashtags
        """
        selected_tags = []
        
        # Map indices to keys if necessary (for backward compatibility with interactive menus)
        indexed_keys = list(self.presets.keys())
        
        for key in category_keys:
            key = key.lower().strip()
            
            # Direct key match
            if key in self.presets:
                name, tags = self.presets[key]
                if tags:
                    selected_tags.append(tags)
                continue
                
            # Index match (1-based string)
            if key.isdigit():
                idx = int(key) - 1
                if 0 <= idx < len(indexed_keys):
                    real_key = indexed_keys[idx]
                    _, tags = self.presets[real_key]
                    if tags:
                        selected_tags.append(tags)

        return " ".join(selected_tags)

    def prepare_caption(self, base_caption: str, categories: List[str] = None) -> str:
        """
        Combine a base caption with hashtags from categories.
        """
        if not categories:
            return base_caption
            
        tags = self.get_hashtags(categories)
        if not tags:
            return base_caption
            
        return f"{base_caption} {tags}"

    async def generate_smart_caption(
        self, 
        video_path: str, 
        context: str = "",
        vibe: str = "funny"
    ) -> Dict[str, str]:
        """
        AI analysis of video/context to generate caption + tags.
        """
        filename = os.path.basename(video_path)
        
        if not self.llm:
            # Basic rule-based generation if no LLM
            clean_name = filename.split('.')[0].replace('_', ' ').replace('-', ' ').title()
            return {
                "caption": f"{clean_name} {context}".strip(),
                "hashtags": self.get_hashtags([vibe, "viral"])
            }

        # Use LLM to generate
        prompt_context = f"Video: {filename}. Description: {context}. Tone: {vibe}."
        
        try:
            # Reuse the general post generation interface
            res = await self.llm.generate_post_json(
                raw_text=prompt_context,
                title=filename,
                url=video_path,
                impact_score=50,
                flags=[vibe],
                lang="en"
            )
            
            return {
                "caption": res.get("short", res.get("hook", f"Check out {filename}!")),
                "hashtags": res.get("hashtags", self.get_hashtags([vibe, "viral"]))
            }
        except Exception as e:
            print(f"AI Generation Error: {e}")
            return {
                "caption": f"Trending video: {filename}",
                "hashtags": "#viral #automation"
            }

    def _extract_frame(self, video_path: str, timestamp: str = "00:00:01") -> Optional[str]:
        """Extract a single frame from the video using ffmpeg."""
        output_path = video_path + ".thumb.jpg"
        try:
            cmd = [
                "ffmpeg", "-y", "-i", video_path, 
                "-ss", timestamp, "-vframes", "1", 
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except Exception:
            return None
