from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import logging
import database as db
import DBmodels
from auth_utils import get_current_user

router = APIRouter(prefix="/api", tags=["community"])
logger = logging.getLogger(__name__)

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
def create_notification(request: NotificationCreateRequest, db: Session = Depends(get_db)):
    logger.info(f"New notification request from {request.email}")
    try:
        new_req = DBmodels.NotificationRequest(
            email=request.email,
            message=request.message,
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
def list_notifications(db: Session = Depends(get_db)):
    logger.info("List notification requests")
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
        posts = db.query(DBmodels.Post).order_by(DBmodels.Post.created_at.desc()).all()
        result = []
        for post in posts:
            author = db.query(DBmodels.User).filter(DBmodels.User.id == post.author_id).first()
            comments = db.query(DBmodels.Comment).filter(DBmodels.Comment.post_id == post.id).order_by(DBmodels.Comment.created_at.asc()).all()
            comment_list = []
            for comment in comments:
                comment_author = db.query(DBmodels.User).filter(DBmodels.User.id == comment.author_id).first()
                comment_list.append({
                    "id": str(comment.id),
                    "body": comment.body,
                    "author": {
                        "id": str(comment_author.id) if comment_author else None,
                        "email": comment_author.email if comment_author else None,
                        "name": comment_author.name if comment_author else None
                    } if comment_author else None,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None
                })
            likes = db.query(DBmodels.Like).filter(DBmodels.Like.post_id == post.id).all()
            like_list = [{"id": str(l.id), "user_id": str(l.user_id)} for l in likes]
            result.append({
                "id": str(post.id),
                "title": post.title,
                "body": post.body,
                "author": {
                    "id": str(author.id) if author else None,
                    "email": author.email if author else None,
                    "name": author.name if author else None
                } if author else None,
                "comments": comment_list,
                "likes": like_list,
                "created_at": post.created_at.isoformat() if post.created_at else None
            })
        return result
    except Exception as e:
        logger.error(f"Error getting posts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/posts")
def create_post(
    request: CreatePostRequest,
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    logger.info("Create post request")
    try:
        new_post = DBmodels.Post(
            title=request.title,
            body=request.body,
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
def create_comment(
    request: CreateCommentRequest,
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    logger.info("Create comment request")
    try:
        new_comment = DBmodels.Comment(
            post_id=request.post_id,
            body=request.body,
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
def toggle_like(
    request: ToggleLikeRequest,
    db: Session = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user),
):
    logger.info("Toggle like request")
    try:
        existing_like = db.query(DBmodels.Like).filter(
            DBmodels.Like.post_id == request.post_id,
            DBmodels.Like.user_id == current_user.id
        ).first()
        if existing_like:
            db.delete(existing_like)
            db.commit()
            return {"liked": False, "message": "Like removed"}
        else:
            new_like = DBmodels.Like(
                post_id=request.post_id,
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
        
        db.query(DBmodels.Comment).filter(DBmodels.Comment.post_id == post_id).delete()
        db.query(DBmodels.Like).filter(DBmodels.Like.post_id == post_id).delete()
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
def subscribe(email: EmailStr, db: Session = Depends(get_db)):
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
def get_subscribers(db: Session = Depends(get_db)):
    logger.info("Get subscribers request")
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
