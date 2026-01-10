"""
FastAPI application exposing content pack review, jobs, artifacts, metrics, and scheduling policy.
"""
from __future__ import annotations

import json
import os
from typing import Any, List, Optional
from datetime import datetime

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import db
from .scheduler.schedule import schedule_approved_content
from .settings import get_settings


def require_auth(authorization: Optional[str] = Header(None)) -> None:
    token = get_settings().api_token
    if not token:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    provided = authorization.split(" ", 1)[1]
    if provided != token:
        raise HTTPException(status_code=403, detail="Invalid token")


def _ensure_db() -> str:
    path = os.getenv("SOCIALIZER_DB", get_settings().db_path)
    db.init_db(path)
    return path


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_db()
    yield


class ContentPack(BaseModel):
    id: str
    lane: str
    format: str
    status: str
    created_at: str
    source_item_id: Optional[str] = None
    hooks_json: Optional[str] = None
    script_text: Optional[str] = None
    carousel_json: Optional[str] = None
    caption_text: Optional[str] = None
    hashtags_json: Optional[str] = None
    template_asset_text: Optional[str] = None
    sources_block_text: Optional[str] = None
    risk_flags_json: Optional[str] = None


class Job(BaseModel):
    id: str
    content_pack_id: str
    platform: str
    slot_utc: Optional[str]
    scheduled_for_utc: Optional[str]
    status: str
    attempts: int
    last_error: Optional[str] = None
    created_at: Optional[str] = None


class ArtifactRequest(BaseModel):
    step: str
    log_json: Optional[dict] = Field(default_factory=dict)
    screenshot_path: Optional[str] = None
    html_path: Optional[str] = None
    console_path: Optional[str] = None


class MetricsRequest(BaseModel):
    window: str
    views: int
    likes: int
    comments: int
    shares: int
    saves: int


class PolicyUpdate(BaseModel):
    bootstrap_weeks: Optional[int] = None
    epsilon: Optional[float] = None
    jitter_min: Optional[int] = None
    jitter_max: Optional[int] = None
    min_gap_hours: Optional[int] = None
    slots: Optional[List[str]] = None
    enable_optional_slot: Optional[bool] = None


class ScheduleResponse(BaseModel):
    id: Optional[str] = None
    content_pack_id: str
    slot_utc: str
    scheduled_for_utc: str


class CreateJobRequest(BaseModel):
    content_pack_id: str
    platform: str = "instagram_reels"
    scheduled_for_utc: Optional[str] = None
    slot_utc: Optional[str] = None


app = FastAPI(title="Socializer Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5501",
        "http://127.0.0.1:5501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/content-packs", response_model=List[ContentPack])
def list_packs(
    status: Optional[str] = Query(None, pattern="^(draft|approved|rejected)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[ContentPack]:
    return db.list_content_packs(status=status, limit=limit, offset=offset)


@app.get("/content-packs/{content_pack_id}", response_model=ContentPack)
def get_pack(content_pack_id: str) -> ContentPack:
    pack = db.get_content_pack(content_pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="content pack not found")
    return pack


@app.get("/jobs", response_model=List[Job])
def list_jobs(
    status: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> List[Job]:
    return db.list_jobs(status=status, platform=platform, limit=limit, offset=offset)


@app.post("/jobs", response_model=Job)
def create_job(payload: CreateJobRequest, _: None = Depends(require_auth)) -> Job:
    path = _ensure_db()
    pack = db.get_content_pack(payload.content_pack_id, db_path=path)
    if not pack:
        raise HTTPException(status_code=404, detail="content pack not found")
    scheduled_for_utc = payload.scheduled_for_utc or db.utc_now_iso()
    slot_utc = payload.slot_utc or _derive_slot_utc(scheduled_for_utc)
    job_id = db.insert_post_job(
        content_pack_id=payload.content_pack_id,
        platform=payload.platform,
        slot_utc=slot_utc,
        scheduled_for_utc=scheduled_for_utc,
        status="queued",
        attempts=0,
        db_path=path,
    )
    job = db.get_job(job_id, db_path=path)
    return Job(**job)


@app.post("/content-packs/{content_pack_id}/approve")
def approve_pack(content_pack_id: str, _: None = Depends(require_auth)) -> dict:
    path = _ensure_db()
    ok = db.set_content_pack_status(content_pack_id, "approved", db_path=path)
    if not ok:
        raise HTTPException(status_code=404, detail="content pack not found")
    return {"id": content_pack_id, "status": "approved"}


@app.post("/content-packs/{content_pack_id}/reject")
def reject_pack(content_pack_id: str, _: None = Depends(require_auth)) -> dict:
    path = _ensure_db()
    ok = db.set_content_pack_status(content_pack_id, "rejected", db_path=path)
    if not ok:
        raise HTTPException(status_code=404, detail="content pack not found")
    return {"id": content_pack_id, "status": "rejected"}


@app.post("/jobs/{job_id}/retry")
def retry(job_id: str, _: None = Depends(require_auth)) -> dict:
    path = _ensure_db()
    ok = db.retry_job(job_id, db_path=path)
    if not ok:
        raise HTTPException(status_code=404, detail="job not found")
    return {"id": job_id, "status": "queued"}


@app.post("/runs/{job_id}/artifacts")
def add_artifact(job_id: str, payload: ArtifactRequest, _: None = Depends(require_auth)) -> dict:
    path = _ensure_db()
    if not db.get_job(job_id, db_path=path):
        raise HTTPException(status_code=404, detail="job not found")
    artifact_id = db.record_artifact(
        job_id=job_id,
        step=payload.step,
        log_json=payload.log_json,
        screenshot_path=payload.screenshot_path,
        html_path=payload.html_path,
        console_path=payload.console_path,
        db_path=path,
    )
    return {"id": artifact_id}


def list_metrics(job_id: str, db_path: Optional[str] = None) -> List[dict]:
    conn = db.get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM metrics WHERE post_job_id=?", (job_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _calc_reward(job_id: str, window: str, views: int, saves: int, shares: int, db_path: Optional[str] = None) -> float:
    if window == "60m":
        return float(views)
    if window == "24h":
        existing = [m for m in list_metrics(job_id, db_path=db_path) if m["window"] == "60m"]
        if existing:
            views_60m = existing[0]["views"]
            return float(views_60m + 3 * saves + 5 * shares)
        return float(0.7 * views)
    return float(views)


def _derive_slot_utc(scheduled_for_utc: str) -> str:
    try:
        parsed = datetime.fromisoformat(scheduled_for_utc.replace("Z", "+00:00"))
        return parsed.strftime("%H:%M")
    except ValueError:
        return "00:00"


@app.post("/jobs/{job_id}/metrics")
def add_metrics(job_id: str, payload: MetricsRequest, _: None = Depends(require_auth)) -> dict:
    path = _ensure_db()
    job = db.get_job(job_id, db_path=path)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    reward = _calc_reward(job_id, payload.window, payload.views, payload.saves, payload.shares, db_path=path)
    metric_id, inserted = db.record_metrics(
        job_id=job_id,
        window=payload.window,
        views=payload.views,
        likes=payload.likes,
        comments=payload.comments,
        shares=payload.shares,
        saves=payload.saves,
        reward=reward,
        db_path=path,
    )
    
    if not inserted:
        # We still return the reward, but it's the one from the existing record if we want to be fully accurate.
        # But for simplicity, we'll just say already_exists.
        # Let's fetch the existing reward if we want to be nice.
        existing = [m for m in list_metrics(job_id, db_path=path) if m["id"] == metric_id]
        existing_reward = existing[0]["reward"] if existing else reward
        return {"id": metric_id, "reward": existing_reward, "status": "already_exists"}

    if job.get("slot_utc"):
        db.update_slot_stats(job["platform"], job["slot_utc"], reward, db_path=path)
    return {"id": metric_id, "reward": reward}


@app.get("/schedule/policy")
def get_policy() -> dict:
    return db.get_schedule_policy()


@app.post("/schedule/policy")
def update_policy(payload: PolicyUpdate, _: None = Depends(require_auth)) -> dict:
    db.upsert_schedule_policy(
        bootstrap_weeks=payload.bootstrap_weeks,
        epsilon=payload.epsilon,
        jitter_min=payload.jitter_min,
        jitter_max=payload.jitter_max,
        min_gap_hours=payload.min_gap_hours,
        slots=payload.slots,
        enable_optional_slot=payload.enable_optional_slot,
    )
    return db.get_schedule_policy()


@app.post("/schedule/tick", response_model=List[ScheduleResponse])
def schedule_tick(
    platform: str = Query(..., pattern="^(tiktok|instagram_reels|youtube_shorts)$"),
    limit: int = Query(1, ge=1, le=5),
    dry_run: bool = Query(False),
    _: None = Depends(require_auth),
) -> List[ScheduleResponse]:
    return schedule_approved_content(platform=platform, limit=limit, dry_run=dry_run)
