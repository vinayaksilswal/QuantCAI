from fastapi import APIRouter, Depends, HTTPException, status, Request
import bleach
from sqlalchemy.orm import Session, joinedload, selectinload
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address

from core import database as db
import models as DBmodels
from core.auth import get_current_user

router = APIRouter(prefix="/api", tags=["community"])
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

def get_db():
    ses = db.SessionLocal()
    try:
        yield ses
    finally:
        ses.close()

class NotificationCreateRequest(BaseModel):
    email: EmailStr
    message: str

class NotificationResponse(BaseModel):
    id: int
    email: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True

class CreatePostRequest(BaseModel):
    title: str
    body: str

class CreateCommentRequest(BaseModel):
    post_id: int
    body: str

class ToggleLikeRequest(BaseModel):
    post_id: int

@router.post("/notify", response_model=NotificationResponse)
@limiter.limit("5/minute")
def create_notification(request: Request, body: NotificationCreateRequest, db: Session = Depends(get_db)):
    logger.info(f"New notification request from {body.email}")
    try:
        new_req = DBmodels.NotificationRequest(
            email=body.email,
            message=body.message,
        )
        db.add(new_req)
        db.commit()
        db.refresh(new_req)
        logger.info(f"Notification request stored (id={new_req.id})")
        return NotificationResponse.model_validate(new_req)
    except Exception as e:
        logger.error(f"Failed to store notification request: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save notification request")

@router.get("/notify", response_model=List[NotificationResponse])
def list_notifications(db: Session = Depends(get_db), current_user: DBmodels.User = Depends(get_current_user)):
    logger.info("List notification requests")
    if current_user.role not in ("admin", "root"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    try:
        items = db.query(DBmodels.NotificationRequest).order_by(DBmodels.NotificationRequest.created_at.desc()).all()
        return [NotificationResponse.model_validate(i) for i in items]
    except Exception as e:
        logger.error(f"Failed to fetch notification requests: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch notification requests")

@router.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    logger.info("Get posts request")
    try:
        # Use eager loading to fetch everything in minimum queries (FIX N+1)
        posts = db.query(DBmodels.Post).options(
            joinedload(DBmodels.Post.author),
            selectinload(DBmodels.Post.comments).joinedload(DBmodels.Comment.author),
            selectinload(DBmodels.Post.likes)
        ).order_by(DBmodels.Post.created_at.desc()).all()

        result = []
        for post in posts:
            # Sanitize content before returning
            safe_title = bleach.clean(post.title, tags=[], attributes={}, strip=True)
            safe_body = bleach.clean(post.body, tags=['p', 'br', 'strong', 'em', 'b', 'i'], attributes={}, strip=True)

            comment_list = []
            for comment in post.comments:
                # Sanitize comment body
                safe_comment_body = bleach.clean(comment.body, tags=['p', 'br', 'strong', 'em', 'b', 'i'], attributes={}, strip=True)
                comment_list.append({
                    "id": str(comment.id),
                    "body": safe_comment_body,
                    "author": {
                        "id": str(comment.author.id) if comment.author else None,
                        "email": comment.author.email if comment.author else None,
                        "name": comment.author.name if comment.author else None
                    } if comment.author else None,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None
                })

            like_list = [{"id": str(l.id), "user_id": str(l.user_id)} for l in post.likes]

            result.append({
                "id": str(post.id),
                "title": safe_title,
                "body": safe_body,
                "author": {
                    "id": str(post.author.id) if post.author else None,
                    "email": post.author.email if post.author else None,
                    "name": post.author.name if post.author else None
                } if post.author else None,
                "comments": comment_list,
                "likes": like_list,
                "created_at": post.created_at.isoformat() if post.created_at else None
            })
        return result
    except Exception as e:
        logger.error(f"Error getting posts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/posts")
@limiter.limit("10/minute")
def create_post(
    request: Request,
    body: CreatePostRequest,
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    logger.info("Create post request")
    try:
        # Sanitize inputs before storing
        safe_title = bleach.clean(body.title, tags=[], attributes={}, strip=True)
        safe_body = bleach.clean(body.body, tags=['p', 'br', 'strong', 'em', 'b', 'i'], attributes={}, strip=True)

        new_post = DBmodels.Post(
            title=safe_title,
            body=safe_body,
            author_id=current_user.id
        )
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        logger.info(f"Post created: {new_post.id}")
        return {"id": str(new_post.id), "message": "Post created successfully"}
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/comments")
@limiter.limit("20/minute")
def create_comment(
    request: Request,
    body: CreateCommentRequest,
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    logger.info("Create comment request")
    try:
        # Sanitize comment body
        safe_body = bleach.clean(body.body, tags=['p', 'br', 'strong', 'em', 'b', 'i'], attributes={}, strip=True)

        new_comment = DBmodels.Comment(
            post_id=body.post_id,
            body=safe_body,
            author_id=current_user.id
        )
        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)
        logger.info(f"Comment created: {new_comment.id}")
        return {"id": str(new_comment.id), "message": "Comment created successfully"}
    except Exception as e:
        logger.error(f"Error creating comment: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/likes/toggle")
@limiter.limit("30/minute")
def toggle_like(
    request: Request,
    body: ToggleLikeRequest,
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    logger.info("Toggle like request")
    try:
        existing_like = db.query(DBmodels.Like).filter(
            DBmodels.Like.post_id == body.post_id,
            DBmodels.Like.user_id == current_user.id
        ).first()
        if existing_like:
            db.delete(existing_like)
            db.commit()
            return {"liked": False, "message": "Like removed"}
        else:
            new_like = DBmodels.Like(
                post_id=body.post_id,
                user_id=current_user.id
            )
            db.add(new_like)
            db.commit()
            db.refresh(new_like)
            return {"liked": True, "message": "Like added"}
    except Exception as e:
        logger.error(f"Error toggling like: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    logger.info(f"Delete post request: {post_id}")
    try:
        post = db.query(DBmodels.Post).filter(DBmodels.Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.author_id != current_user.id and current_user.role not in ("admin", "root"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete post")

        # Cascades in DBmodels.py handle comments and likes deletion
        db.delete(post)
        db.commit()
        return {"message": "Post deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting post: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    logger.info(f"Delete comment request: {comment_id}")
    try:
        comment = db.query(DBmodels.Comment).filter(DBmodels.Comment.id == comment_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        if comment.author_id != current_user.id and current_user.role not in ("admin", "root"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete comment")
        db.delete(comment)
        db.commit()
        return {"message": "Comment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting comment: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/subscribe")
@limiter.limit("5/minute")
def subscribe(request: Request, email: EmailStr, db: Session = Depends(get_db)):
    logger.info(f"Subscription request for email: {email}")
    try:
        existing_subscriber = db.query(DBmodels.Subscriber).filter(DBmodels.Subscriber.email == email).first()

        if existing_subscriber:
            if existing_subscriber.is_active:
                return {"message": "Email is already subscribed", "subscribed": True}
            else:
                existing_subscriber.is_active = True
                db.commit()
                return {"message": "Subscription reactivated successfully", "subscribed": True}

        new_subscriber = DBmodels.Subscriber(email=email, is_active=True)
        db.add(new_subscriber)
        db.commit()
        db.refresh(new_subscriber)
        return {"message": "Successfully subscribed to newsletter", "subscribed": True}
    except Exception as e:
        logger.error(f"Error subscribing: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/subscribers")
def get_subscribers(db: Session = Depends(get_db), current_user: DBmodels.User = Depends(get_current_user)):
    logger.info("Get subscribers request")
    if current_user.role not in ("admin", "root"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    try:
        subscribers = db.query(DBmodels.Subscriber).filter(
            DBmodels.Subscriber.is_active == True
        ).order_by(DBmodels.Subscriber.created_at.desc()).all()
        return [{
            "id": s.id,
            "email": s.email,
            "created_at": s.created_at.isoformat() if s.created_at else None
        } for s in subscribers]
    except Exception as e:
        logger.error(f"Error getting subscribers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
