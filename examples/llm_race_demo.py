#!/usr/bin/env python3
"""
LLM Race Competition Demo
Demonstrates the LLM race where two LLMs compete to login via Firefox cookies and perform Instagram engagement.

This script shows:
1. Setting up the race with two LLM participants
2. Running the three-phase competition (cookie extraction, login, engagement)
3. Determining the winner based on completed tasks and speed

Usage:
    python examples/llm_race_demo.py

Environment variables needed:
    GEMINI_API_KEY (required)
    OPENAI_API_KEY (optional, for second participant)
    INSTAGRAM_USERNAME & INSTAGRAM_PASSWORD (optional, for real engagement)
"""
import asyncio
import os
import sys
from pathlib import Path

# Add radar to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from radar.llm_race import LLMRace, main as race_main

async def main():
    """Main LLM race demonstration."""
    print("🏁 LLM Race Competition Demo")
    print("=" * 50)

    # Check environment
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY environment variable required")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set - running with Gemini only")

    # Check for Instagram credentials for real engagement
    if not os.getenv("INSTAGRAM_USERNAME") or not os.getenv("INSTAGRAM_PASSWORD"):
        print("⚠️  Warning: INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD not set")
        print("   The race will complete but engagement actions will be simulated")
        print("   To perform REAL Instagram engagement that shows in your activity:")
        print("   1. Set INSTAGRAM_USERNAME=your_username")
        print("   2. Set INSTAGRAM_PASSWORD=your_password")
        print("   3. Check https://www.instagram.com/your_activity/interactions/reviews")
        print()

    print("This demo will run the LLM race competition.")
    print("Two LLMs will compete to:")
    print("1. Extract Instagram cookies from Firefox")
    print("2. Login using those cookies")
    print("3. Perform engagement actions (like, save) on target post")
    print("\nStarting race...")

    try:
        # Run the race using the main function from llm_race.py
        await race_main()

    except Exception as e:
        print(f"❌ Error during race: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())