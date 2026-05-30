from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
import logging
from typing import List
from datetime import datetime, timezone
from core import database as db
import models as DBmodels
from core.auth import get_current_user

router = APIRouter(prefix="/api", tags=["users"])
logger = logging.getLogger(__name__)

def get_db():
    ses = db.SessionLocal()
    try:
        yield ses
    finally:
        ses.close()

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
    is_blocked: bool
    role: str
    token_version: int
    
    class Config:
        from_attributes = True

class PageProgressResponse(BaseModel):
    page_key: str
    read_at: datetime

    class Config:
        from_attributes = True

class TrackProgressRequest(BaseModel):
    page_key: str

@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db), current_user: DBmodels.User = Depends(get_current_user)
):
    logger.info("Get all users request")
    try:
        if current_user.role not in ("admin", "root"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        users = db.query(DBmodels.User).all()
        return [UserResponse.model_validate(user) for user in users]
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/courses")
def get_all_courses(db: Session = Depends(get_db)):
    logger.info("Get all courses request")
    try:
        courses = db.query(DBmodels.Course).filter(DBmodels.Course.is_active == True).all()
        return [{"id": c.id, "title": c.title, "description": c.description, "created_at": c.created_at.isoformat() if c.created_at else None} for c in courses]
    except Exception as e:
        logger.error(f"Error getting courses: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/progress", response_model=List[PageProgressResponse])
def get_user_progress(
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user)
):
    try:
        progress = db.query(DBmodels.PageProgress).filter(DBmodels.PageProgress.user_id == current_user.id).all()
        return progress
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/progress")
def track_progress(
    body: TrackProgressRequest,
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user)
):
    try:
        # Update if exists, else create
        existing = db.query(DBmodels.PageProgress).filter(
            DBmodels.PageProgress.user_id == current_user.id,
            DBmodels.PageProgress.page_key == body.page_key
        ).with_for_update().first()
        
        if existing:
            existing.read_at = datetime.utcnow()
        else:
            new_progress = DBmodels.PageProgress(
                user_id=current_user.id,
                page_key=body.page_key
            )
            db.add(new_progress)
        
        db.commit()
        return {"message": "Progress tracked"}
    except Exception as e:
        logger.error(f"Error tracking progress: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/usage/summary")
def get_usage_summary(
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user)
):
    """
    Returns user-specific usage statistics (API calls today, PQC scans this month,
    simulations run) and the last 10 usage events.
    """
    try:
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        # 1. API Calls Today
        api_calls_today = db.query(func.count(DBmodels.UsageEvent.id)).filter(
            DBmodels.UsageEvent.user_id == current_user.id,
            DBmodels.UsageEvent.event_type == DBmodels.UsageEventType.API_CALL,
            DBmodels.UsageEvent.created_at >= today_start
        ).scalar() or 0

        # 2. PQC Scans This Month
        pqc_scans_this_month = db.query(func.count(DBmodels.UsageEvent.id)).filter(
            DBmodels.UsageEvent.user_id == current_user.id,
            DBmodels.UsageEvent.event_type == DBmodels.UsageEventType.PQC_SCAN,
            DBmodels.UsageEvent.created_at >= month_start
        ).scalar() or 0

        # 3. Simulations Run
        simulations_run = db.query(func.count(DBmodels.UsageEvent.id)).filter(
            DBmodels.UsageEvent.user_id == current_user.id,
            DBmodels.UsageEvent.event_type == DBmodels.UsageEventType.SIMULATION_RUN
        ).scalar() or 0

        # 4. Recent Activity (last 10 usage events)
        recent_events = db.query(DBmodels.UsageEvent).filter(
            DBmodels.UsageEvent.user_id == current_user.id
        ).order_by(DBmodels.UsageEvent.created_at.desc()).limit(10).all()

        events_list = [
            {
                "id": ev.id,
                "event_type": ev.event_type.value if hasattr(ev.event_type, "value") else str(ev.event_type),
                "credits_used": ev.credits_used,
                "created_at": ev.created_at.isoformat() if ev.created_at else None,
                "metadata": ev.metadata_
            }
            for ev in recent_events
        ]

        return {
            "api_calls_today": api_calls_today,
            "pqc_scans_this_month": pqc_scans_this_month,
            "simulations_run": simulations_run,
            "recent_events": events_list
        }
    except Exception as e:
        logger.error(f"Error fetching usage summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

