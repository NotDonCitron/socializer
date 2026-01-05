from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database.client import get_db
from ..models.schemas import UserDB, UserCreate, UserResponse, PostDB, PostResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check for existing user
    query = select(UserDB).where((UserDB.email == user.email) | (UserDB.username == user.username))
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already registered")

    new_user = UserDB(**user.model_dump())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB).where(UserDB.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}/posts", response_model=List[PostResponse])
async def get_user_posts(user_id: int, db: AsyncSession = Depends(get_db)):
    # Verify user exists first (optional but good practice)
    await get_user(user_id, db) 
    
    result = await db.execute(select(PostDB).where(PostDB.user_id == user_id).order_by(PostDB.created_at.desc()))
    return result.scalars().all()
