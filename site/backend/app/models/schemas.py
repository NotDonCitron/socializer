from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
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
