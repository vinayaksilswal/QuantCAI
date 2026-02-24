from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from core import database as db
import models as DBmodels
from core.auth import get_current_user

router = APIRouter(prefix="/api", tags=["content"])
logger = logging.getLogger(__name__)

def get_db():
    ses = db.SessionLocal()
    try:
        yield ses
    finally:
        ses.close()

class LearnBlockCreate(BaseModel):
    title: str
    body_md: str
    image_url: Optional[str] = None

class LearnBlockResponse(BaseModel):
    id: int
    title: str
    body_md: str
    image_url: Optional[str]
    author_id: int
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/learn-blocks", response_model=List[LearnBlockResponse])
def get_learn_blocks(db: Session = Depends(get_db)):
    try:
        blocks = db.query(DBmodels.LearnBlock).order_by(DBmodels.LearnBlock.created_at.desc()).all()
        return blocks
    except Exception as e:
        logger.error(f"Error fetching learn blocks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/learn-blocks", response_model=LearnBlockResponse)
def create_learn_block(
    body: LearnBlockCreate,
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user)
):
    if current_user.role not in ("admin", "root"):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        new_block = DBmodels.LearnBlock(
            title=body.title,
            body_md=body.body_md,
            image_url=body.image_url,
            author_id=current_user.id
        )
        db.add(new_block)
        db.commit()
        db.refresh(new_block)
        return new_block
    except Exception as e:
        logger.error(f"Error creating learn block: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
