from typing import Dict, Optional, Tuple, List

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
    def __init__(self, presets: Optional[Dict[str, Tuple[str, str]]] = None):
        self.presets = presets or DEFAULT_PRESETS

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

    # Future placeholder for AI
    async def generate_smart_caption(self, video_path: str, context: str = "") -> str:
        """
        TODO: Implement AI analysis of video/context to generate caption + tags.
        """
        pass
