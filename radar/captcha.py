import os
import time
from typing import Optional, Dict, Any
from twocaptcha import TwoCaptcha

class CaptchaSolver:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TWOCAPTCHA_API_KEY")
        if not self.api_key:
            raise ValueError("No 2Captcha API key found. Set TWOCAPTCHA_API_KEY in .env")
        
        self.solver = TwoCaptcha(self.api_key)

    def solve_recaptcha_v2(self, sitekey: str, url: str) -> str:
        """Solves Google ReCaptcha V2 (Checkbox)"""
        print(f"🧩 Solving ReCaptcha V2 for {url}...")
        try:
            result = self.solver.recaptcha(
                sitekey=sitekey,
                url=url
            )
            print(f"✅ Solved: {result['code'][:20]}...")
            return result['code']
        except Exception as e:
            print(f"❌ Captcha failed: {e}")
            raise

    def solve_image(self, image_path: str) -> str:
        """Solves a normal image CAPTCHA (text on image)"""
        print(f"🧩 Solving Image Captcha: {image_path}...")
        try:
            result = self.solver.normal(image_path)
            print(f"✅ Solved: {result['code']}")
            return result['code']
        except Exception as e:
            print(f"❌ Captcha failed: {e}")
            raise

    def report_bad(self, captcha_id: str):
        """Report incorrect solution to get refund"""
        self.solver.report(captcha_id, False)

# Singleton instance
_solver_instance = None

def get_solver() -> CaptchaSolver:
    global _solver_instance
    if _solver_instance is None:
        _solver_instance = CaptchaSolver()
    return _solver_instance
