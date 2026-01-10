from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .database.client import engine, Base, AsyncSessionLocal
from .api import users, posts, ai, admin
from .models.schemas import UserDB
from sqlalchemy import select

# Lifespan Events (Startup/Shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if they don't exist (Dev only, use Alembic in Prod!)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database connected & tables created.")

    # Create default user for demo/prototype
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(UserDB).limit(1))
        if not result.scalar():
            default_user = UserDB(username="admin", email="admin@example.com")
            db.add(default_user)
            await db.commit()
            print("Default user 'admin' created.")
    
    yield
    
    # Shutdown
    await engine.dispose()
    print("Database connection closed.")

app = FastAPI(
    title="Socializer API",
    version="0.1.0",
    lifespan=lifespan
)

# Middleware (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(users.router)
app.include_router(posts.router)
app.include_router(ai.router)
app.include_router(admin.router)

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "service": "socializer-api"}
