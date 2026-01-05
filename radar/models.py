from __future__ import annotations
from pydantic import BaseModel, Field, HttpUrl
from typing import Any, Literal, List, Dict, Optional

class SourceConfig(BaseModel):
    id: str
    type: Literal["github_releases", "webpage_diff"]
    repo: Optional[str] = None
    url: Optional[HttpUrl] = None
    tags: List[str] = Field(default_factory=list)
    priority: int = 3

class PostingConfig(BaseModel):
    generate_de_if_impact_gte: int = 70
    medium_if_impact_gte: int = 70
    post_if_impact_gte: int = 40

class StackConfig(BaseModel):
    stack_slug: str
    title: str
    timezone: str = "UTC"
    languages: List[str] = Field(default_factory=lambda: ["en"])
    posting: PostingConfig = Field(default_factory=PostingConfig)
    sources: List[SourceConfig]

class RawItem(BaseModel):
    source_id: str
    kind: Literal["release", "webpage"]
    external_id: str # e.g. tag_name or url hash key
    title: str
    url: str
    published_at: Optional[str] = None
    raw_text: str
    raw_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScoredItem(BaseModel):
    raw: RawItem
    impact_score: int
    flags: List[str]
    tags: List[str]

class GeneratedPost(BaseModel):
    source_id: str
    external_id: str
    url: str
    impact_score: int
    flags: List[str]
    tags: List[str]
    languages: List[str]

    title_en: str
    hook_en: str
    short_en: str
    medium_en: Optional[str] = None

    title_de: Optional[str] = None
    hook_de: Optional[str] = None
    short_de: Optional[str] = None
    medium_de: Optional[str] = None

    action_items: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
