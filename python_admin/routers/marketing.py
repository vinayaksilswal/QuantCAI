"""
=============================================================================
QuantCAI — Marketing Router
=============================================================================
Handles the marketing dashboard UI and manual override endpoints for:
  - Social media post management (list, create manual, edit)
  - Email campaign management (list, create manual, edit)
  - Manual media upload with AI caption generation override

All endpoints use request.app.state.prisma (no standalone Prisma instances).
All endpoints are authenticated via JWT.
=============================================================================
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import Any, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from pydantic import BaseModel

from auth import verify_credentials
from services.ai_service import generate_campaign_email, generate_campaign_variation
from services.email_service import send_email_blast
from services.social_service import (
    post_to_facebook,
    post_to_instagram,
    update_facebook_post,
    update_instagram_post,
)
from services.scheduler import execute_marketing_loop

router = APIRouter(
    prefix="/marketing",
    tags=["Marketing"],
    dependencies=[Depends(verify_credentials)],
)
templates = Jinja2Templates(directory="templates")

# Ensure uploads directory exists
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# =============================================================================
# Request/Response Models
# =============================================================================
class SocialPostUpdate(BaseModel):
    """Model for updating an existing social post."""
    caption: Optional[str] = None
    scheduledAt: Optional[str] = None
    status: Optional[str] = None


class EmailCampaignUpdate(BaseModel):
    """Model for updating an existing email campaign."""
    subject: Optional[str] = None
    bodyText: Optional[str] = None
    bodyHtml: Optional[str] = None
    scheduledAt: Optional[str] = None
    status: Optional[str] = None


class ManualEmailRequest(BaseModel):
    """Model for creating a manual email campaign."""
    generateAiEmail: bool = False
    productId: Optional[str] = None
    manualSubject: str = ""
    manualBodyHtml: str = ""
    manualBodyText: str = ""

class AutoApproveUpdate(BaseModel):
    autoApprove: bool


# =============================================================================
# Dashboard
# =============================================================================
@router.get("/")
async def marketing_root() -> RedirectResponse:
    """Redirect /marketing to /marketing/dashboard."""
    return RedirectResponse(url="/marketing/dashboard")


@router.get("/dashboard")
async def marketing_dashboard(request: Request) -> Any:
    """Render the marketing automation dashboard page."""
    prisma = request.app.state.prisma
    audiences = await prisma.audience.find_many()
    state = await prisma.marketingstate.find_unique(where={"id": "singleton"})
    if not state:
        state = await prisma.marketingstate.create(data={"id": "singleton"})
        
    return templates.TemplateResponse(
        request=request,
        name="marketing.html",
        context={"title": "Marketing Automation", "audiences": audiences, "autoApprove": state.autoApprove},
    )

@router.post("/settings/auto-approve")
async def toggle_auto_approve(
    data: AutoApproveUpdate, request: Request
) -> dict[str, Any]:
    prisma = request.app.state.prisma
    try:
        state = await prisma.marketingstate.upsert(
            where={"id": "singleton"},
            data={
                "create": {"id": "singleton", "autoApprove": data.autoApprove},
                "update": {"autoApprove": data.autoApprove}
            }
        )
        return {"success": True, "autoApprove": state.autoApprove}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-automation")
async def run_automation_manually(request: Request) -> dict[str, Any]:
    try:
        # Note: In production you might want to run this in the background, 
        # but for a manual trigger, awaiting is fine for feedback.
        await execute_marketing_loop()
        return {"success": True, "message": "Automation loop executed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Social Post Endpoints
# =============================================================================
@router.get("/posts")
async def get_social_posts(request: Request) -> Any:
    """List all social posts, newest first, with product data included."""
    prisma = request.app.state.prisma
    posts = await prisma.socialpost.find_many(
        order={"scheduledAt": "desc"},
        include={"campaign": True},
    )
    return posts


@router.put("/posts/{post_id}")
async def edit_social_post(
    post_id: str, 
    request: Request,
    caption: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    scheduledAt: Optional[str] = Form(None),
    existing_media: List[str] = Form([]),
    files: List[UploadFile] = File(None)
) -> Any:
    """
    Edit an existing social post.
    Supports updating caption, status, and modifying media (appending files or removing existing).
    """
    prisma = request.app.state.prisma

    existing = await prisma.socialpost.find_unique(where={"id": post_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Post not found")

    new_caption = caption

    # Check if we are publishing a draft or retrying a failed post
    publishing_draft = existing.status in ("DRAFT", "FAILED") and status == "POSTED"
    
    # Check if we are updating a live post's caption
    updating_live_caption = existing.status == "POSTED" and new_caption and existing.caption != new_caption

    # Process new file uploads
    new_media_urls: list[str] = []
    if files:
        for file in files:
            if file.filename:
                import shutil
                file_location = os.path.join(UPLOAD_DIR, file.filename)
                with open(file_location, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                base_url = str(request.base_url).rstrip("/")
                url = f"{base_url}/uploads/{file.filename}"
                
                is_video_ext = file.filename.lower().endswith((".mp4", ".mov", ".webm", ".avi", ".mkv"))
                if (file.content_type and file.content_type.startswith("video/")) or is_video_ext:
                    url += "?type=video"
                    
                new_media_urls.append(url)

    cleaned_existing_media = []
    base_url_str = str(request.base_url).rstrip("/")
    import urllib.parse
    for url in existing_media:
        parsed = urllib.parse.urlparse(url)
        if parsed.netloc:
            url = f"{base_url_str}{parsed.path}"
            if parsed.query:
                url += f"?{parsed.query}"
        
        # Ensure it has ?type=video if it's a video
        if url.lower().split("?")[0].endswith((".mp4", ".mov", ".webm", ".avi", ".mkv")):
            if "type=video" not in url.lower():
                url += "&type=video" if "?" in url else "?type=video"
        cleaned_existing_media.append(url)

    # Combine existing media we want to keep with new media
    final_media_urls = cleaned_existing_media + new_media_urls

    update_data: dict[str, Any] = {
        "mediaUrls": final_media_urls
    }
    
    if publishing_draft:
        fb_post_id, ig_post_id = None, None
        errors: list[str] = []
        platform = existing.platform
        media_urls = final_media_urls

        caption_to_post = new_caption or existing.caption or ""

        if platform in ("FACEBOOK", "BOTH"):
            try:
                fb_post_id = await post_to_facebook(message=caption_to_post, media_urls=media_urls)
                if not fb_post_id:
                    errors.append("FB: Post returned None")
            except Exception as e:
                errors.append(f"FB: {str(e)}")

        if platform in ("INSTAGRAM", "BOTH"):
            try:
                ig_post_id = await post_to_instagram(message=caption_to_post, media_urls=media_urls)
                if not ig_post_id:
                    errors.append("IG: Post returned None")
            except Exception as e:
                errors.append(f"IG: {str(e)}")

        if platform == "BOTH":
            is_success = fb_post_id is not None and ig_post_id is not None
        elif platform == "FACEBOOK":
            is_success = fb_post_id is not None
        elif platform == "INSTAGRAM":
            is_success = ig_post_id is not None
        else:
            is_success = False
        
        # Override status if publishing failed
        update_data["status"] = "POSTED" if is_success else "FAILED"
        update_data["fbPostId"] = fb_post_id
        update_data["igPostId"] = ig_post_id
        update_data["errorLog"] = " | ".join(errors) if errors else None
        if is_success:
            update_data["postedAt"] = datetime.now()

    elif updating_live_caption:
        if existing.fbPostId:
            try:
                await update_facebook_post(existing.fbPostId, new_caption)
            except Exception as e:
                logger.warning(f"Failed to update FB post: {e}")
        if existing.igPostId:
            try:
                await update_instagram_post(existing.igPostId, new_caption)
            except Exception as e:
                logger.warning(f"Failed to update IG post: {e}")

    # Build update payload
    if caption is not None:
        update_data["caption"] = caption
    if status is not None and "status" not in update_data:
        update_data["status"] = status
    if scheduledAt:
        update_data["scheduledAt"] = datetime.fromisoformat(
            scheduledAt.replace("Z", "+00:00")
        )

    updated = await prisma.socialpost.update(
        where={"id": post_id},
        data=update_data,
    )
    return updated


@router.post("/posts/generate-caption")
async def api_generate_caption(
    request: Request,
    product_id: str = Form(...),
) -> dict[str, Any]:
    """Generates an AI caption for a given product ID without creating a post."""
    prisma = request.app.state.prisma
    campaign = await prisma.socialcampaign.find_unique(where={"id": product_id})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    caption = await generate_campaign_variation(campaign.baseCaption)
    return {"success": True, "caption": caption}


@router.post("/posts/manual")
async def create_manual_social_post(
    request: Request,
    platform: str = Form("BOTH"),
    generate_ai_caption: str = Form("false"),
    product_id: Optional[str] = Form(None),
    manual_caption: Optional[str] = Form(""),
    status: str = Form("DRAFT"),
    files: List[UploadFile] = File(None),
) -> dict[str, Any]:
    """
    Manual Override: Create and publish a social media post.

    Allows manual media uploads and optional AI caption generation.
    Overrides the automated scheduler flow.

    Args:
        platform: FACEBOOK, INSTAGRAM, or BOTH
        generate_ai_caption: "true" to use AI for caption generation
        product_id: Optional product ID to associate with the post
        manual_caption: Manual caption text (ignored if AI generation is on)
        files: Optional media file uploads
    """
    prisma = request.app.state.prisma

    # Handle file uploads
    media_urls: list[str] = []
    if files:
        for file in files:
            if file.filename:
                import shutil
                file_location = os.path.join(UPLOAD_DIR, file.filename)
                with open(file_location, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                base_url = str(request.base_url).rstrip("/")
                url = f"{base_url}/uploads/{file.filename}"
                
                is_video_ext = file.filename.lower().endswith((".mp4", ".mov", ".webm", ".avi", ".mkv"))
                if (file.content_type and file.content_type.startswith("video/")) or is_video_ext:
                    url += "?type=video"
                    
                media_urls.append(url)

    caption = manual_caption or ""
    campaign = None

    if product_id:
        campaign = await prisma.socialcampaign.find_unique(where={"id": product_id})
        # If campaign found but no manual media, use campaign media
        if campaign and not media_urls:
            if campaign.mediaUrl:
                media_urls.append(campaign.mediaUrl)

    # Generate AI caption if requested
    if generate_ai_caption.lower() == "true" and campaign:
        caption = await generate_campaign_variation(campaign.baseCaption)

    # Create the post record
    post = await prisma.socialpost.create(
        data={
            "campaignId": campaign.id if campaign else None,
            "platform": platform,
            "type": "MANUAL",
            "caption": caption,
            "mediaUrls": media_urls,
            "scheduledAt": datetime.now(),
            "status": "DRAFT",
        }
    )

    if status == "DRAFT":
        return {"success": True, "post": post.model_dump(), "errors": []}

    # Post to platforms
    fb_post_id, ig_post_id = None, None
    errors: list[str] = []

    if platform in ("FACEBOOK", "BOTH"):
        try:
            fb_post_id = await post_to_facebook(message=caption, media_urls=media_urls)
            if not fb_post_id:
                errors.append("FB: Post returned None")
        except Exception as e:
            errors.append(f"FB: {str(e)}")

    if platform in ("INSTAGRAM", "BOTH"):
        try:
            ig_post_id = await post_to_instagram(message=caption, media_urls=media_urls)
            if not ig_post_id:
                errors.append("IG: Post returned None")
        except Exception as e:
            errors.append(f"IG: {str(e)}")

    if platform == "BOTH":
        is_success = fb_post_id is not None and ig_post_id is not None
    elif platform == "FACEBOOK":
        is_success = fb_post_id is not None
    elif platform == "INSTAGRAM":
        is_success = ig_post_id is not None
    else:
        is_success = False

    # Update post record with results
    await prisma.socialpost.update(
        where={"id": post.id},
        data={
            "status": "POSTED" if is_success else "FAILED",
            "postedAt": datetime.now() if is_success else None,
            "errorLog": " | ".join(errors) if errors else None,
            "fbPostId": fb_post_id,
            "igPostId": ig_post_id,
        },
    )

    return {"success": is_success, "post": post.model_dump(), "errors": errors}


# =============================================================================
# Email Campaign Endpoints
# =============================================================================
@router.get("/emails")
async def get_email_campaigns(request: Request) -> Any:
    """List all email campaigns, newest first, with product data included."""
    prisma = request.app.state.prisma
    emails = await prisma.emailcampaign.find_many(
        order={"scheduledAt": "desc"},
        include={"campaign": True},
    )
    return emails


@router.put("/emails/{campaign_id}")
async def edit_email_campaign(
    campaign_id: str, data: EmailCampaignUpdate, request: Request
) -> Any:
    """Edit an existing email campaign record. If publishing a draft, send the email."""
    prisma = request.app.state.prisma
    
    existing = await prisma.emailcampaign.find_unique(where={"id": campaign_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Campaign not found")

    publishing_draft = existing.status in ("DRAFT", "FAILED") and data.status == "SENT"

    update_data: dict[str, Any] = {}
    if data.subject is not None:
        update_data["subject"] = data.subject
    if data.bodyText is not None:
        update_data["bodyText"] = data.bodyText
    if data.bodyHtml is not None:
        update_data["bodyHtml"] = data.bodyHtml
    if data.status is not None:
        update_data["status"] = data.status
    if data.scheduledAt:
        update_data["scheduledAt"] = datetime.fromisoformat(
            data.scheduledAt.replace("Z", "+00:00")
        )

    if publishing_draft:
        # Trigger sending the email
        subject = data.subject or existing.subject
        body_html = data.bodyHtml or existing.bodyHtml
        body_text = data.bodyText or existing.bodyText
        
        try:
            result = await send_email_blast(
                subject=subject,
                html_body=body_html,
                text_body=body_text,
                prisma=prisma,
            )
            is_success = result.get("success", False)
            recipient_count = result.get("count", 0)
            error_log = result.get("error")

            update_data["status"] = "SENT" if is_success else "FAILED"
            update_data["sentAt"] = datetime.now() if is_success else None
            update_data["recipientCount"] = recipient_count
            update_data["errorLog"] = error_log
        except Exception as e:
            update_data["status"] = "FAILED"
            update_data["errorLog"] = str(e)

    try:
        updated = await prisma.emailcampaign.update(
            where={"id": campaign_id},
            data=update_data,
        )
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emails/manual")
async def create_manual_email(
    data: ManualEmailRequest, request: Request
) -> dict[str, Any]:
    """
    Manual Override: Create and send an email campaign.

    Can either use manual content or AI-generate content from a product.
    Sends via Resend to all audience members and users.
    """
    prisma = request.app.state.prisma

    subject = data.manualSubject
    body_html = data.manualBodyHtml
    body_text = data.manualBodyText

    social_campaign = None
    if data.productId:
        social_campaign = await prisma.socialcampaign.find_unique(where={"id": data.productId})

    # Generate AI email content if requested
    if data.generateAiEmail and social_campaign:
        ai_content = await generate_campaign_email(social_campaign)
        subject = ai_content.get("subject", subject)
        body_html = ai_content.get("bodyHtml", body_html)
        body_text = ai_content.get("bodyText", body_text)

    # Create campaign record
    campaign = await prisma.emailcampaign.create(
        data={
            "campaignId": social_campaign.id if social_campaign else None,
            "type": "MANUAL",
            "subject": subject,
            "bodyText": body_text,
            "bodyHtml": body_html,
            "scheduledAt": datetime.now(),
            "status": "DRAFT",
        }
    )

    # Send via Resend
    try:
        result = await send_email_blast(
            subject=subject,
            html_body=body_html,
            text_body=body_text,
            prisma=prisma,
        )
        is_success = result.get("success", False)
        recipient_count = result.get("count", 0)
        error_log = result.get("error")

        await prisma.emailcampaign.update(
            where={"id": campaign.id},
            data={
                "status": "SENT" if is_success else "FAILED",
                "sentAt": datetime.now() if is_success else None,
                "recipientCount": recipient_count,
                "errorLog": error_log,
            },
        )
        return {"success": is_success, "campaign": campaign.model_dump()}

    except Exception as e:
        await prisma.emailcampaign.update(
            where={"id": campaign.id},
            data={"status": "FAILED", "errorLog": str(e)},
        )
        raise HTTPException(status_code=500, detail=str(e))
