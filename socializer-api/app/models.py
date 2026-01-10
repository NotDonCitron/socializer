from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Enum as SqlEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

class Lane(str, enum.Enum):
    beginner = "beginner"
    builder = "builder"

class PackStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"

class JobStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    queued = "queued"
    running = "running"
    posted = "posted"
    failed = "failed"
    dead = "dead"

class Platform(str, enum.Enum):
    tiktok = "tiktok"
    instagram = "instagram"
    youtube = "youtube"

class SourceItem(Base):
    __tablename__ = "source_items"
    id = Column(Integer, primary_key=True, index=True)
    uri = Column(String, index=True)
    created_at = Column(DateTime, default=func.now())

class Extract(Base):
    __tablename__ = "extracts"
    id = Column(Integer, primary_key=True, index=True)
    source_item_id = Column(Integer, ForeignKey("source_items.id"))
    content = Column(String)
    created_at = Column(DateTime, default=func.now())

class ContentPack(Base):
    __tablename__ = "content_packs"
    id = Column(Integer, primary_key=True, index=True)
    lane = Column(String, default=Lane.beginner) # beginner, builder
    status = Column(String, default=PackStatus.draft) # draft, approved, rejected
    created_at = Column(DateTime, default=func.now())
    
    jobs = relationship("PostJob", back_populates="content_pack")

class PostJob(Base):
    __tablename__ = "post_jobs"
    id = Column(Integer, primary_key=True, index=True)
    content_pack_id = Column(Integer, ForeignKey("content_packs.id"))
    platform = Column(String) # tiktok, instagram, youtube
    status = Column(String, default=JobStatus.draft)
    scheduled_for_utc = Column(DateTime, nullable=True)
    slot_utc = Column(String, nullable=True) # "13:00"
    attempts = Column(Integer, default=0)
    last_error = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    content_pack = relationship("ContentPack", back_populates="jobs")
    artifacts = relationship("RunArtifact", back_populates="job")
    metrics = relationship("Metric", back_populates="job")

class RunArtifact(Base):
    __tablename__ = "run_artifacts"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("post_jobs.id"))
    artifact_type = Column(String)
    uri = Column(String)
    created_at = Column(DateTime, default=func.now())

    job = relationship("PostJob", back_populates="artifacts")

class Metric(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("post_jobs.id"))
    platform = Column(String)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    reward = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=func.now())

    job = relationship("PostJob", back_populates="metrics")

class SlotStats(Base):
    __tablename__ = "slot_stats"
    id = Column(Integer, primary_key=True, index=True)
    slot_utc = Column(String) # "13:00"
    platform = Column(String)
    samples = Column(Integer, default=0)
    total_reward = Column(Float, default=0.0)

class SchedulePolicy(Base):
    __tablename__ = "schedule_policy"
    id = Column(Integer, primary_key=True, index=True)
    active = Column(Integer, default=1) # Boolean
    slots_json = Column(String, default='["13:00", "19:00"]')
    start_date = Column(DateTime, default=func.now()) # To track week 1, 2, etc.
