"""
Centralized settings for the Socializer backend.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str = os.getenv("SOCIALIZER_DB", "socializer.sqlite")
    api_token: str | None = os.getenv("SOCIALIZER_API_TOKEN")


def get_settings() -> Settings:
    """Return immutable settings snapshot."""
    return Settings()
