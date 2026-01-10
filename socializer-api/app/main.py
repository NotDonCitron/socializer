from fastapi import FastAPI, Depends, HTTPException, status, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from datetime import datetime

from .database import get_db, engine, Base
from . import models, schemas, scheduler

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Socializer API")

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:5501", 
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5501",
    "*" # Allow all for dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_TOKEN = os.getenv("SOCIALIZER_API_TOKEN")

def verify_token(authorization: Optional[str] = Header(None)):
    if API_TOKEN:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing Authorization Header")
        scheme, _, param = authorization.partition(" ")
        if scheme.lower() != "bearer" or param != API_TOKEN:
            raise HTTPException(status_code=403, detail="Invalid Token")

@app.get("/content-packs", response_model=List[schemas.ContentPack])
def list_content_packs(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.ContentPack)
    if status:
        query = query.filter(models.ContentPack.status == status)
    return query.all()

@app.get("/content-packs/{id}", response_model=schemas.ContentPack)
def get_content_pack(id: int, db: Session = Depends(get_db)):
    pack = db.query(models.ContentPack).filter(models.ContentPack.id == id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return pack

@app.post("/content-packs/{id}/approve", dependencies=[Depends(verify_token)])
def approve_pack(id: int, db: Session = Depends(get_db)):
    pack = db.query(models.ContentPack).filter(models.ContentPack.id == id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    pack.status = models.PackStatus.approved
    db.commit()
    return {"status": "approved"}

@app.post("/content-packs/{id}/reject", dependencies=[Depends(verify_token)])
def reject_pack(id: int, db: Session = Depends(get_db)):
    pack = db.query(models.ContentPack).filter(models.ContentPack.id == id).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    pack.status = models.PackStatus.rejected
    db.commit()
    return {"status": "rejected"}

@app.get("/jobs", response_model=List[schemas.PostJob])
def list_jobs(
    status: Optional[str] = None, 
    platform: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    query = db.query(models.PostJob)
    if status:
        query = query.filter(models.PostJob.status == status)
    if platform:
        query = query.filter(models.PostJob.platform == platform)
    return query.all()

@app.post("/jobs/{id}/retry", dependencies=[Depends(verify_token)])
def retry_job(id: int, db: Session = Depends(get_db)):
    job = db.query(models.PostJob).filter(models.PostJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    # Reset status to queued?
    job.status = models.JobStatus.queued
    job.attempts += 1
    db.commit()
    return {"status": "retrying"}

@app.post("/runs/{job_id}/artifacts", dependencies=[Depends(verify_token)])
def add_artifact(job_id: int, artifact: schemas.RunArtifactCreate, db: Session = Depends(get_db)):
    job = db.query(models.PostJob).filter(models.PostJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    art = models.RunArtifact(job_id=job_id, artifact_type=artifact.artifact_type, uri=artifact.uri)
    db.add(art)
    db.commit()
    return {"status": "created"}

@app.post("/jobs/{job_id}/metrics", dependencies=[Depends(verify_token)])
def update_metrics(job_id: int, metric_data: schemas.MetricCreate, db: Session = Depends(get_db)):
    job = db.query(models.PostJob).filter(models.PostJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Calculate Reward
    # Reward function not specified, assume weighted sum or raw views?
    # Prompt: "compute reward + update slot_stats"
    # Simple reward: views + 10*likes + 20*shares?
    # Or just normalized?
    # Let's use: views + 5*likes + 10*shares.
    reward = metric_data.views + (metric_data.likes * 5) + (metric_data.shares * 10)

    metric = models.Metric(
        job_id=job_id,
        platform=job.platform,
        views=metric_data.views,
        likes=metric_data.likes,
        shares=metric_data.shares,
        reward=reward
    )
    db.add(metric)
    
    # Update Slot Stats
    if job.slot_utc:
        slot_stat = db.query(models.SlotStats).filter(
            models.SlotStats.slot_utc == job.slot_utc,
            models.SlotStats.platform == job.platform
        ).first()
        
        if not slot_stat:
            slot_stat = models.SlotStats(slot_utc=job.slot_utc, platform=job.platform)
            db.add(slot_stat)
        
        slot_stat.samples += 1
        slot_stat.total_reward += reward
    
    db.commit()
    return {"status": "updated", "reward": reward}

@app.post("/schedule/tick", dependencies=[Depends(verify_token)])
def schedule_tick(
    dry_run: bool = False,
    db: Session = Depends(get_db)
):
    result = scheduler.tick(db, dry_run=dry_run)
    return result

@app.get("/schedule/policy", response_model=schemas.SchedulePolicy)
def get_policy_endpoint(db: Session = Depends(get_db)):
    return scheduler.get_policy(db)

@app.post("/schedule/policy", dependencies=[Depends(verify_token)])
def update_policy(policy_data: schemas.SchedulePolicyBase, db: Session = Depends(get_db)):
    policy = scheduler.get_policy(db)
    policy.active = policy_data.active
    import json
    policy.slots_json = json.dumps(policy_data.slots)
    db.commit()
    return {"status": "updated"}
