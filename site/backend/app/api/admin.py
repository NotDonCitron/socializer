from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional

from ..database.client import get_db
from ..models.schemas import (
    AccountDB, AccountResponse, AccountCreate, AccountUpdate,
    AccountGroupDB, AccountGroupResponse, AccountGroupCreate, AccountGroupUpdate,
    JobDB, JobResponse, LogDB, LogResponse
)

router = APIRouter(prefix="/api", tags=["admin"])


# --- Accounts Endpoints ---

@router.get("/accounts", response_model=List[AccountResponse])
async def get_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """List all social accounts."""
    query = select(AccountDB).order_by(AccountDB.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific account by ID."""
    result = await db.execute(select(AccountDB).where(AccountDB.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(account: AccountCreate, db: AsyncSession = Depends(get_db)):
    """Create a new social account."""
    # Verify group exists if group_id is provided
    if account.group_id:
        group_result = await db.execute(select(AccountGroupDB).where(AccountGroupDB.id == account.group_id))
        group = group_result.scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=404, detail="Account group not found")
    
    new_account = AccountDB(**account.model_dump())
    db.add(new_account)
    await db.commit()
    await db.refresh(new_account)
    return new_account


@router.put("/accounts/{account_id}", response_model=AccountResponse)
async def update_account(account_id: int, account_update: AccountUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing account."""
    result = await db.execute(select(AccountDB).where(AccountDB.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Verify group exists if group_id is being updated
    if account_update.group_id:
        group_result = await db.execute(select(AccountGroupDB).where(AccountGroupDB.id == account_update.group_id))
        group = group_result.scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=404, detail="Account group not found")
    
    # Update only provided fields
    update_data = account_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an account."""
    result = await db.execute(select(AccountDB).where(AccountDB.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    await db.delete(account)
    await db.commit()


# --- Account Groups Endpoints ---

@router.get("/account-groups", response_model=List[AccountGroupResponse])
async def get_account_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """List all account groups."""
    query = select(AccountGroupDB).order_by(AccountGroupDB.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/account-groups/{group_id}", response_model=AccountGroupResponse)
async def get_account_group(group_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific account group by ID."""
    result = await db.execute(select(AccountGroupDB).where(AccountGroupDB.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Account group not found")
    return group


@router.post("/account-groups", response_model=AccountGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_account_group(group: AccountGroupCreate, db: AsyncSession = Depends(get_db)):
    """Create a new account group."""
    new_group = AccountGroupDB(**group.model_dump())
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return new_group


@router.put("/account-groups/{group_id}", response_model=AccountGroupResponse)
async def update_account_group(group_id: int, group_update: AccountGroupUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing account group."""
    result = await db.execute(select(AccountGroupDB).where(AccountGroupDB.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Account group not found")
    
    # Update only provided fields
    update_data = group_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)
    
    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/account-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account_group(group_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an account group."""
    result = await db.execute(select(AccountGroupDB).where(AccountGroupDB.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Account group not found")
    
    await db.delete(group)
    await db.commit()


# --- Jobs Endpoints ---

@router.get("/jobs", response_model=List[JobResponse])
async def get_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    platform: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all automation jobs with optional filtering."""
    query = select(JobDB).order_by(desc(JobDB.created_at))

    if status:
        query = query.where(JobDB.status == status)
    if platform:
        query = query.where(JobDB.platform == platform)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific job by ID."""
    result = await db.execute(select(JobDB).where(JobDB.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/run", status_code=status.HTTP_200_OK)
async def trigger_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Trigger a job to run immediately."""
    result = await db.execute(select(JobDB).where(JobDB.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update job status to running
    job.status = "running"
    await db.commit()

    # Create a log entry for the job trigger
    log_entry = LogDB(
        job_id=job_id,
        level="info",
        message=f"Job {job_id} triggered manually"
    )
    db.add(log_entry)
    await db.commit()

    return {"status": "success", "message": f"Job {job_id} has been triggered", "job": job}


# --- Logs Endpoints ---

@router.get("/logs", response_model=List[LogResponse])
async def get_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    job_id: Optional[int] = None,
    level: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List logs with optional filtering."""
    query = select(LogDB).order_by(desc(LogDB.timestamp))

    if job_id:
        query = query.where(LogDB.job_id == job_id)
    if level:
        query = query.where(LogDB.level == level)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/jobs/{job_id}/logs", response_model=List[LogResponse])
async def get_job_logs(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get all logs for a specific job."""
    result = await db.execute(
        select(LogDB).where(LogDB.job_id == job_id).order_by(desc(LogDB.timestamp))
    )
    return result.scalars().all()
