from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .models import Lane, PackStatus, JobStatus, Platform

class ContentPackBase(BaseModel):
    lane: str = Lane.beginner

class ContentPackCreate(ContentPackBase):
    pass

class ContentPack(ContentPackBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PostJobBase(BaseModel):
    platform: str
    scheduled_for_utc: Optional[datetime] = None
    slot_utc: Optional[str] = None

class PostJob(PostJobBase):
    id: int
    content_pack_id: int
    status: str
    attempts: int
    last_error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RunArtifactCreate(BaseModel):
    artifact_type: str
    uri: str

class MetricCreate(BaseModel):
    views: int = 0
    likes: int = 0
    shares: int = 0

class SchedulePolicyBase(BaseModel):
    active: bool
    slots: List[str]

class SchedulePolicy(SchedulePolicyBase):
    id: int
    start_date: datetime

    class Config:
        from_attributes = True
