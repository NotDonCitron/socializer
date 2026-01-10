from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from sqlmodel import Field, SQLModel, Relationship, create_engine, Column, JSON
import os

# --- Models ---

class Proxy(SQLModel, table=True):
    __tablename__ = "proxies"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = Field(default="http")  # http, https, socks5
    
    country: Optional[str] = None
    provider: Optional[str] = None
    
    is_active: bool = Field(default=True)
    last_used: Optional[datetime] = None
    success_rate: float = Field(default=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    accounts: List["Account"] = Relationship(back_populates="proxy")

    def to_playwright_dict(self) -> dict:
        """Convert to Playwright proxy format"""
        proxy_dict = {"server": f"{self.protocol}://{self.host}:{self.port}"}
        if self.username and self.password:
            proxy_dict["username"] = self.username
            proxy_dict["password"] = self.password
        return proxy_dict


class Account(SQLModel, table=True):
    __tablename__ = "accounts"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    platform: str = Field(index=True)  # twitter, linkedin, instagram, tiktok
    username: str = Field(index=True)
    password: Optional[str] = None
    
    status: str = Field(default="needs_login") # connected, disconnected, expired, needs_login, error
    avatar_url: Optional[str] = None
    
    # Session data stored as JSON
    session_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    last_success: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to Proxy
    proxy_id: Optional[str] = Field(default=None, foreign_key="proxies.id")
    proxy: Optional[Proxy] = Relationship(back_populates="accounts")


# --- Database Connection ---

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///data/radar.sqlite"
)

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
