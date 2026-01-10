from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import List, Optional
from ..database.client import Base

# --- SQLAlchemy Models (Database) ---

class UserDB(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    posts = relationship("PostDB", back_populates="author", cascade="all, delete-orphan")

class PostDB(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    source_repo = Column(String, nullable=True)
    impact_score = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    author = relationship("UserDB", back_populates="posts")
    comments = relationship("CommentDB", back_populates="post", cascade="all, delete-orphan")

class CommentDB(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("PostDB", back_populates="comments")


# --- Admin Panel Models ---

class AccountGroupDB(Base):
    __tablename__ = "account_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    email = Column(String, nullable=True)
    proxy = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    color = Column(String, default="#3b82f6")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    accounts = relationship("AccountDB", back_populates="group", cascade="all, delete-orphan")


class AccountDB(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)
    username = Column(String, nullable=False)
    status = Column(String, default="needs_login")
    avatar_url = Column(String, nullable=True)
    group_id = Column(Integer, ForeignKey("account_groups.id"), nullable=True)
    session_data = Column(JSON, nullable=True)
    last_success = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    group = relationship("AccountGroupDB", back_populates="accounts")
    jobs = relationship("JobDB", back_populates="account", cascade="all, delete-orphan")


class JobDB(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)
    status = Column(String, default="scheduled")
    type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    last_run = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    account = relationship("AccountDB", back_populates="jobs")
    logs = relationship("LogDB", back_populates="job", cascade="all, delete-orphan")


class LogDB(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    level = Column(String, default="info")
    message = Column(Text, nullable=False)
    
    job = relationship("JobDB", back_populates="logs")


# --- Pydantic Schemas (API Validation) ---

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PostCreate(BaseModel):
    user_id: int
    title: Optional[str] = None
    content: str
    source_repo: Optional[str] = None
    impact_score: Optional[int] = 0

class PostResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    content: str
    source_repo: Optional[str]
    impact_score: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Admin Panel Schemas ---

class AccountGroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    email: Optional[str] = None
    proxy: Optional[str] = None
    topic: Optional[str] = None
    color: Optional[str] = "#3b82f6"

class AccountGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    email: Optional[str] = None
    proxy: Optional[str] = None
    topic: Optional[str] = None
    color: Optional[str] = "#3b82f6"

class AccountGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    proxy: Optional[str] = None
    topic: Optional[str] = None
    color: Optional[str] = None

class AccountGroupResponse(AccountGroupBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AccountBase(BaseModel):
    platform: str
    username: str
    status: Optional[str] = "needs_login"
    avatar_url: Optional[str] = None
    group_id: Optional[int] = None
    session_data: Optional[dict] = None

class AccountCreate(BaseModel):
    platform: str
    username: str
    status: Optional[str] = "needs_login"
    avatar_url: Optional[str] = None
    group_id: Optional[int] = None
    session_data: Optional[dict] = None

class AccountUpdate(BaseModel):
    platform: Optional[str] = None
    username: Optional[str] = None
    status: Optional[str] = None
    avatar_url: Optional[str] = None
    group_id: Optional[int] = None
    session_data: Optional[dict] = None

class AccountResponse(AccountBase):
    id: int
    last_success: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class JobBase(BaseModel):
    platform: str
    status: Optional[str] = "scheduled"
    type: str
    content: str
    account_id: Optional[int] = None
    scheduled_for: datetime

class JobResponse(JobBase):
    id: int
    last_run: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LogResponse(BaseModel):
    id: int
    job_id: Optional[int] = None
    timestamp: datetime
    level: str
    message: str
    model_config = ConfigDict(from_attributes=True)
