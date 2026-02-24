"""
Admin dashboard endpoints. Requires user.role == 'admin'.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from core.auth import get_current_user
import models as DBmodels
from core import database as db

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

def get_admin_user(current_user: DBmodels.User = Depends(get_current_user)) -> DBmodels.User:
    """Dependency to ensure current user is admin."""
    if current_user.role not in ("admin", "root"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def get_db():
    ses = db.SessionLocal()
    try:
        yield ses
    finally:
        ses.close()

# ======================
# User Management
# ======================

@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: DBmodels.User = Depends(get_admin_user)
):
    """List all users with pagination and filters."""
    query = db.query(DBmodels.User)

    if search:
        query = query.filter(
            (DBmodels.User.email.ilike(f"%{search}%")) |
            (DBmodels.User.name.ilike(f"%{search}%"))
        )
    if role:
        query = query.filter(DBmodels.User.role == role)
    if is_active is not None:
        query = query.filter(DBmodels.User.is_active == is_active)

    total = query.count()
    users = query.order_by(DBmodels.User.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "role": u.role,
                "is_active": u.is_active,
                "is_blocked": u.is_blocked,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "failed_login_attempts": u.failed_login_attempts,
                "locked_until": u.locked_until.isoformat() if u.locked_until else None
            }
            for u in users
        ]
    }

@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: DBmodels.User = Depends(get_admin_user)
):
    """Get details for a specific user."""
    user = db.query(DBmodels.User).filter(DBmodels.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "is_active": user.is_active,
        "is_blocked": user.is_blocked,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "token_version": user.token_version,
        "failed_login_attempts": user.failed_login_attempts,
        "locked_until": user.locked_until.isoformat() if user.locked_until else None
    }

@router.post("/users/{user_id}/block")
def block_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: DBmodels.User = Depends(get_admin_user)
):
    """Block a user (prevents login)."""
    user = db.query(DBmodels.User).filter(DBmodels.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role in ("admin", "root"):
        raise HTTPException(status_code=400, detail="Cannot block admin users")
    user.is_blocked = True
    db.add(user)
    db.commit()
    logger.info(f"Admin blocked user {user.email} (ID {user_id})")
    return {"message": f"User {user.email} blocked"}

@router.post("/users/{user_id}/unblock")
def unblock_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: DBmodels.User = Depends(get_admin_user)
):
    """Unblock a user."""
    user = db.query(DBmodels.User).filter(DBmodels.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_blocked = False
    db.add(user)
    db.commit()
    logger.info(f"Admin unblocked user {user.email} (ID {user_id})")
    return {"message": f"User {user.email} unblocked"}

@router.post("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    role: str = Query(..., description="New role: admin, user, root"),
    db: Session = Depends(get_db),
    _: DBmodels.User = Depends(get_admin_user)
):
    """Change a user's role."""
    if role not in ("admin", "user", "root"):
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(DBmodels.User).filter(DBmodels.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == _.id and role != _.role:
        # Admin can't demote themselves through this endpoint
        raise HTTPException(status_code=400, detail="Cannot change your own role via this endpoint")
    user.role = role
    db.add(user)
    db.commit()
    logger.info(f"Admin changed role for {user.email} to {role}")
    return {"message": f"User {user.email} role changed to {role}"}

# ======================
# Audit Logs
# ======================

@router.get("/logs")
def view_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    level: Optional[str] = Query(None),
    since: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    _: DBmodels.User = Depends(get_admin_user)
):
    """View application logs from logtable."""
    query = db.query(DBmodels.Log)

    if level:
        query = query.filter(DBmodels.Log.level == level.upper())
    if since:
        query = query.filter(DBmodels.Log.timestamp >= since)

    total = query.count()
    logs = query.order_by(desc(DBmodels.Log.timestamp)).offset((page-1)*per_page).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "logs": [
            {
                "id": l.id,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
                "level": l.level,
                "logger": l.logger_name,
                "message": l.message,
                "module": l.module,
                "function": l.function,
                "line": l.line_number,
                "request": {
                    "method": l.request_method,
                    "path": l.request_path,
                    "ip": l.request_ip
                } if l.request_method else None,
                "response_status": l.response_status,
                "exception": l.exception
            }
            for l in logs
        ]
    }

@router.get("/logs/errors")
def recent_errors(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: DBmodels.User = Depends(get_admin_user)
):
    """Get recent error logs."""
    since = datetime.utcnow() - timedelta(hours=hours)
    errors = db.query(DBmodels.Log).filter(
        DBmodels.Log.level.in_(["ERROR", "CRITICAL"]),
        DBmodels.Log.timestamp >= since
    ).order_by(desc(DBmodels.Log.timestamp)).limit(limit).all()

    return {
        "total": len(errors),
        "errors": [
            {
                "timestamp": e.timestamp.isoformat(),
                "level": e.level,
                "message": e.message,
                "exception": e.exception,
                "request_path": e.request_path,
                "request_ip": e.request_ip
            }
            for e in errors
        ]
    }

# ======================
# System Metrics
# ======================

@router.get("/metrics")
def system_metrics(_: DBmodels.User = Depends(get_admin_user)):
    """Get system-level metrics."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory": {
            "total_gb": psutil.virtual_memory().total / (1024**3),
            "available_gb": psutil.virtual_memory().available / (1024**3),
            "percent": psutil.virtual_memory().percent
        },
        "disk": {
            "total_gb": psutil.disk_usage('/').total / (1024**3),
            "free_gb": psutil.disk_usage('/').free / (1024**3),
            "percent": psutil.disk_usage('/').percent
        },
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
    }

@router.get("/stats")
def database_stats(
    db: Session = Depends(get_db),
    _: DBmodels.User = Depends(get_admin_user)
):
    """Get database statistics."""
    stats = {}
    try:
        stats["users"] = db.query(DBmodels.User).count()
        stats["posts"] = db.query(DBmodels.Post).count()
        stats["comments"] = db.query(DBmodels.Comment).count()
        stats["likes"] = db.query(DBmodels.Like).count()
        stats["subscribers"] = db.query(DBmodels.Subscriber).filter_by(is_active=True).count()
        stats["circuits"] = db.query(DBmodels.Circuit).count()
        stats["refresh_tokens"] = db.query(DBmodels.RefreshToken).count()
        stats["failed_login_users"] = db.query(DBmodels.User).filter(DBmodels.User.failed_login_attempts > 0).count()
        stats["locked_accounts"] = db.query(DBmodels.User).filter(DBmodels.User.locked_until != None).filter(DBmodels.User.locked_until > datetime.utcnow()).count()
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "counts": stats
    }
