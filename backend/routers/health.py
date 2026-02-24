"""
Health check and system monitoring endpoints.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging
import psutil
import time
from datetime import datetime
import os

from core.database import SessionLocal

router = APIRouter(tags=["monitoring"])
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Track app start time
APP_START_TIME = time.time()

@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Basic health check endpoint.
    Returns 200 if app and database are responsive.
    """
    try:
        # Test DB connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Health check DB error: {str(e)}")
        db_status = "unhealthy"

    uptime_seconds = int(time.time() - APP_START_TIME)

    status = 200 if db_status == "healthy" else 503

    return {
        "status": "ok" if db_status == "healthy" else "error",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime_seconds,
        "database": db_status,
        "service": "QuantCAI API"
    }

@router.get("/health/detailed")
def detailed_health(db: Session = Depends(get_db)):
    """
    Detailed health check with system metrics.
    (Admin-only in production; accessible to all in development)
    """
    try:
        db.execute(text("SELECT 1"))
        db_healthy = True
        db_error = None
    except Exception as e:
        db_healthy = False
        db_error = str(e)

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Database stats (approximate)
    db_stats = {}
    if db_healthy:
        try:
            # Count users
            user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
            post_count = db.execute(text("SELECT COUNT(*) FROM posts")).scalar()
            db_stats = {
                "users": user_count,
                "posts": post_count
            }
        except Exception:
            db_stats = {"error": "could not fetch stats"}

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - APP_START_TIME),
        "database": {
            "healthy": db_healthy,
            "error": db_error,
            "stats": db_stats
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent
        },
        "environment": os.getenv("ENV", "production")
    }
