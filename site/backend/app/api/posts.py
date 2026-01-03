from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..database.client import get_db
from ..models.schemas import PostDB, PostCreate, PostResponse, UserDB
from sqlalchemy import func

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get("/stats/impact")
async def get_impact_stats(db: AsyncSession = Depends(get_db)):
    # Group by source_repo and sum impact_score
    query = select(
        PostDB.source_repo, 
        func.sum(PostDB.impact_score).label("total_impact"),
        func.count(PostDB.id).label("post_count")
    ).where(PostDB.source_repo != None).group_by(PostDB.source_repo)
    
    result = await db.execute(query)
    stats = []
    for row in result:
        stats.append({
            "repo": row[0],
            "impact": row[1],
            "count": row[2]
        })
    return stats

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, db: AsyncSession = Depends(get_db)):
    # Validate User ID
    user_query = await db.execute(select(UserDB).where(UserDB.id == post.user_id))
    if not user_query.scalar_one_or_none():
         raise HTTPException(status_code=404, detail="User not found")

    new_post = PostDB(**post.model_dump())
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PostDB).where(PostDB.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.get("/", response_model=List[PostResponse])
async def get_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    # Pagination via async select
    query = select(PostDB).order_by(PostDB.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PostDB).where(PostDB.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    await db.delete(post)
    await db.commit()
