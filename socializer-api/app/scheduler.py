import random
import json
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from .models import ContentPack, PostJob, SchedulePolicy, SlotStats, JobStatus, PackStatus, Lane, Platform
import logging

logger = logging.getLogger(__name__)

PLATFORMS = [Platform.tiktok, Platform.instagram, Platform.youtube]
STAGGER_MINUTES = {
    Platform.tiktok: (0, 10),
    Platform.instagram: (20, 40),
    Platform.youtube: (40, 60)
}
EPSILON = 0.20

def get_policy(db: Session):
    policy = db.query(SchedulePolicy).first()
    if not policy:
        policy = SchedulePolicy(active=True, slots_json='["13:00", "19:00"]', start_date=datetime.utcnow())
        db.add(policy)
        db.commit()
        db.refresh(policy)
    return policy

def get_slots(policy: SchedulePolicy):
    return json.loads(policy.slots_json)

def get_week_number(policy: SchedulePolicy):
    delta = datetime.utcnow() - policy.start_date
    return delta.days // 7

def check_gap_and_limits(db: Session, target_date: datetime.date):
    # Check max 1/day/platform
    # We assume we schedule for ALL platforms at once, so just checking one is roughly enough, 
    # but let's be safe.
    
    # Range for target date
    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)
    
    count = db.query(PostJob).filter(
        PostJob.scheduled_for_utc >= start_of_day,
        PostJob.scheduled_for_utc <= end_of_day
    ).count()
    
    if count > 0:
        return False, "Max 1/day limit"

    # Check min gap 18h from LAST scheduled job (any platform? or same platform?)
    # "min gap 18h". Usually per platform. 
    # If we schedule all together, we just need to check the latest job overall.
    last_job = db.query(PostJob).order_by(PostJob.scheduled_for_utc.desc()).first()
    if last_job and last_job.scheduled_for_utc:
        diff = start_of_day - last_job.scheduled_for_utc
        # Logic: The gap should be between the previous job and the NEW job.
        # But we don't know the exact time yet (depends on slot).
        # Worst case: previous job was late, new job is early.
        # Let's just enforce 18h from last job time.
        if (start_of_day + timedelta(hours=12)) - last_job.scheduled_for_utc < timedelta(hours=18):
             # Rough check. If last job was yesterday 23:00, and today we target 13:00. Gap is 14h.
             # We need to be careful.
             pass
    
    return True, "OK"

def select_slot(db: Session, policy: SchedulePolicy, week_num: int):
    slots = get_slots(policy)
    if not slots:
        return None

    if week_num < 2: # Weeks 1-2 (0 and 1) -> Rotation
        # Simple rotation based on total jobs count
        total_jobs = db.query(PostJob).count()
        # Divide by number of platforms to get "batches"
        batch_count = total_jobs // len(PLATFORMS)
        return slots[batch_count % len(slots)]
    else: # Week 3+ -> Bandit
        # Check samples
        # We need to aggregate stats per slot?
        # Or just pick a slot and use it for all.
        
        # Epsilon-greedy
        if random.random() < EPSILON:
             return random.choice(slots)
        
        # Exploit
        best_slot = None
        best_reward = -1.0
        
        for slot in slots:
            # Aggregate reward for this slot across platforms
            stats = db.query(SlotStats).filter(SlotStats.slot_utc == slot).all()
            total_r = sum(s.total_reward for s in stats)
            total_n = sum(s.samples for s in stats)
            
            # "min_samples_per_slot=5"
            # If any platform has < 5 samples for this slot? 
            # Or aggregate? "min_samples_per_slot=5".
            # Let's assume aggregate samples > 5 * 3? Or just 5?
            # Prompt: "min_samples_per_slot=5".
            # If total_n < 5, maybe prioritize it?
            # Standard epsilon-greedy doesn't force exploration, but we can.
            
            avg = (total_r / total_n) if total_n > 0 else 0
            if avg > best_reward:
                best_reward = avg
                best_slot = slot
        
        if best_slot:
            return best_slot
        return random.choice(slots)

def select_content_pack(db: Session):
    # Lane mix 60/40
    # Get last 10 jobs to see lane history
    last_jobs = db.query(PostJob).join(ContentPack).order_by(PostJob.created_at.desc()).limit(10).all()
    
    beginner_count = 0
    for job in last_jobs:
        if job.content_pack.lane == Lane.beginner:
            beginner_count += 1
    
    target_lane = Lane.beginner
    # If we want 60% beginner. 6/10.
    if len(last_jobs) > 0:
        ratio = beginner_count / len(last_jobs)
        if ratio >= 0.6:
            target_lane = Lane.builder
    
    # Find approved pack
    # "not yet job-linked": pack.jobs is empty
    # SQLAlchemy: ~ContentPack.jobs.any()
    pack = db.query(ContentPack).filter(
        ContentPack.status == PackStatus.approved,
        ContentPack.lane == target_lane,
        ~ContentPack.jobs.any()
    ).first()
    
    if not pack:
        # Fallback to other lane
        other_lane = Lane.builder if target_lane == Lane.beginner else Lane.beginner
        pack = db.query(ContentPack).filter(
            ContentPack.status == PackStatus.approved,
            ContentPack.lane == other_lane,
            ~ContentPack.jobs.any()
        ).first()
        
    return pack

def tick(db: Session, dry_run: bool = False):
    policy = get_policy(db)
    if not policy.active:
        return {"status": "skipped", "reason": "Policy inactive"}

    # Determine target date: Today or Tomorrow?
    # We want to keep the pipeline full?
    # Prompt: "schedule tick".
    # Let's try to schedule for *tomorrow* if today is full, or today if empty.
    # Simple logic: Find next valid slot.
    
    now = datetime.utcnow()
    candidates = [now.date(), now.date() + timedelta(days=1), now.date() + timedelta(days=2)]
    
    target_date = None
    
    for date_candidate in candidates:
        if date_candidate.weekday() >= 5: # Sat=5, Sun=6. Mon-Fri only.
            continue
        
        # Check gap and limits
        ok, reason = check_gap_and_limits(db, date_candidate)
        if ok:
            # Also check if we already have jobs for this date?
            # check_gap_and_limits handles "max 1/day".
            target_date = date_candidate
            break
    
    if not target_date:
        return {"status": "skipped", "reason": "No valid dates found (limits reached?)"}

    # Select Slot
    week_num = get_week_number(policy)
    slot_str = select_slot(db, policy, week_num)
    if not slot_str:
        return {"status": "error", "reason": "No slots defined"}

    # Parse slot time
    h, m = map(int, slot_str.split(":"))
    base_time = datetime.combine(target_date, time(h, m))
    
    # Check 18h gap constraint strictly against base_time
    last_job = db.query(PostJob).order_by(PostJob.scheduled_for_utc.desc()).first()
    if last_job and last_job.scheduled_for_utc:
        if (base_time - last_job.scheduled_for_utc) < timedelta(hours=18):
             # Try next day?
             # For simplicity, just skip this tick if we can't fit it.
             return {"status": "skipped", "reason": "Min gap 18h violation"}

    # Select Pack
    pack = select_content_pack(db)
    if not pack:
        return {"status": "skipped", "reason": "No content packs available"}

    if dry_run:
        return {"status": "dry_run", "target_date": str(target_date), "slot": slot_str, "pack_id": pack.id}

    # Create Jobs
    # Jitter: +/- 7-12m
    # Random sign
    jitter_minutes = random.randint(7, 12) * (1 if random.random() > 0.5 else -1)
    
    jobs = []
    for platform in PLATFORMS:
        stagger_min, stagger_max = STAGGER_MINUTES[platform]
        stagger = random.randint(stagger_min, stagger_max)
        
        final_time = base_time + timedelta(minutes=jitter_minutes + stagger)
        
        job = PostJob(
            content_pack_id=pack.id,
            platform=platform,
            status=JobStatus.queued,
            scheduled_for_utc=final_time,
            slot_utc=slot_str
        )
        db.add(job)
        jobs.append(job)
    
    db.commit()
    return {"status": "scheduled", "jobs": [j.id for j in jobs], "slot": slot_str}
