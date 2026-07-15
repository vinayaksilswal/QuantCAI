"""
=============================================================================
QuantCAI — API Router (v1)
=============================================================================
Handles all REST API endpoints for:
  - Product CRUD operations
  - CJ Dropshipping integration (query, import, bulk import, fulfillment)
  - AI copy rewriting
  - Chatbot (consolidated from former ai_chat.py)

All endpoints are authenticated via JWT cookie/Bearer token.
All endpoints use request.app.state.prisma (no standalone Prisma instances).
=============================================================================
"""

from __future__ import annotations

import json
import shutil
import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Response
from loguru import logger
from pydantic import BaseModel, Field

from auth import verify_credentials
from services.chat_agent import chat_with_agent


router = APIRouter(
    prefix="/api/v1",
    tags=["API"],
    dependencies=[Depends(verify_credentials)],
)


# =============================================================================
# Request/Response Models
# =============================================================================
class StandardResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None





class ChatRequest(BaseModel):
    """Request model for the AI chatbot."""
    messages: List[Dict[str, Any]] = Field(
        ..., description="Conversation messages array"
    )

class CampaignCreate(BaseModel):
    baseCaption: str
    mediaUrl: str
    mediaType: str

class CampaignUpdate(BaseModel):
    isActive: Optional[bool] = None
    baseCaption: Optional[str] = None


# =============================================================================
# Upload Endpoints
# =============================================================================
from fastapi.responses import Response
import base64

@router.post("/upload-media", response_model=StandardResponse)
async def upload_media(request: Request, file: UploadFile = File(...)) -> StandardResponse:
    """Upload a video or image file to the database (Media table)."""
    try:
        prisma = request.app.state.prisma
        mime_type = file.content_type or "application/octet-stream"
        
        raw_data = await file.read()
        
        media_record = await prisma.media.create(
            data={
                "filename": file.filename or "uploaded_media",
                "mimeType": mime_type,
                "data": raw_data
            }
        )
        
        url_suffix = "?type=video.mp4" if mime_type.startswith("video/") else "?type=image.jpg"
        base_url = str(request.base_url).rstrip("/")
        
        return StandardResponse(success=True, data={"url": f"{base_url}/api/v1/media/{media_record.id}{url_suffix}"})
    except Exception as e:
        logger.error(f"Failed to upload media: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

public_router = APIRouter(
    prefix="/api/v1",
    tags=["Public API"]
)

@public_router.get("/media/{media_id}")
async def get_media(media_id: str, request: Request):
    """Retrieve media from the database (PUBLIC)."""
    prisma = request.app.state.prisma
    media_record = await prisma.media.find_unique(where={"id": media_id})
    if not media_record:
        raise HTTPException(status_code=404, detail="Media not found")
        
    import base64
    import re
    from fastapi.responses import Response, StreamingResponse
    
    # Data is stored as base64-encoded ASCII string — decode back to raw bytes
    raw_data = media_record.data
    
    if type(raw_data).__name__ == 'Base64':
        data_bytes = base64.b64decode(str(raw_data))
    elif isinstance(raw_data, (bytes, bytearray)):
        data_bytes = raw_data
    else:
        try:
            data_bytes = base64.b64decode(str(raw_data))
        except Exception:
            data_bytes = str(raw_data).encode('latin-1')
        
    file_size = len(data_bytes)
    
    range_header = request.headers.get("Range")
    if range_header:
        byte1, byte2 = 0, None
        match = re.search(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            g = match.groups()
            byte1 = int(g[0])
            if g[1]:
                byte2 = int(g[1])
                
        MAX_CHUNK_SIZE = 3 * 1024 * 1024 # 3MB max chunk
        
        if byte2 is None:
            byte2 = byte1 + MAX_CHUNK_SIZE - 1
            
        if (byte2 - byte1 + 1) > MAX_CHUNK_SIZE:
            byte2 = byte1 + MAX_CHUNK_SIZE - 1
            
        if byte2 >= file_size:
            byte2 = file_size - 1
            
        length = byte2 - byte1 + 1
        
        data = data_bytes[byte1:byte2 + 1]
        
        headers = {
            "Content-Range": f"bytes {byte1}-{byte2}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
            "Cache-Control": "public, max-age=86400",
        }
        return Response(content=data, status_code=206, headers=headers, media_type=media_record.mimeType)
    
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Cache-Control": "public, max-age=86400",
    }
    
    def iter_bytes():
        chunk_size = 1024 * 1024 # 1MB chunks
        for i in range(0, file_size, chunk_size):
            yield data_bytes[i:i+chunk_size]
            
    return StreamingResponse(iter_bytes(), headers=headers, media_type=media_record.mimeType)

# =============================================================================
# Social Campaign Endpoints
# =============================================================================
@router.post("/campaigns", response_model=StandardResponse)
async def create_campaign(data: CampaignCreate, request: Request) -> StandardResponse:
    """Create a new social media campaign."""
    prisma = request.app.state.prisma
    try:
        campaign = await prisma.socialcampaign.create(
            data={
                "baseCaption": data.baseCaption,
                "mediaUrl": data.mediaUrl,
                "mediaType": data.mediaType,
            }
        )
        return StandardResponse(success=True, data=campaign.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/campaigns", response_model=StandardResponse)
async def get_campaigns(request: Request) -> StandardResponse:
    """Get all social media campaigns."""
    prisma = request.app.state.prisma
    try:
        campaigns = await prisma.socialcampaign.find_many(
            order={"createdAt": "desc"}
        )
        data = [c.model_dump() for c in campaigns]
        return StandardResponse(success=True, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/campaigns/{cid}", response_model=StandardResponse)
async def update_campaign(cid: str, data: CampaignUpdate, request: Request) -> StandardResponse:
    """Update a social media campaign's active status and caption."""
    prisma = request.app.state.prisma
    try:
        update_data = {}
        if data.isActive is not None:
            update_data["isActive"] = data.isActive
        if data.baseCaption is not None:
            update_data["baseCaption"] = data.baseCaption
            
        updated = await prisma.socialcampaign.update(
            where={"id": cid},
            data=update_data,
        )
        return StandardResponse(success=True, data=updated.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/campaigns/{cid}", response_model=StandardResponse)
async def delete_campaign(cid: str, request: Request) -> StandardResponse:
    """Delete a social media campaign."""
    prisma = request.app.state.prisma
    try:
        await prisma.socialcampaign.delete(where={"id": cid})
        return StandardResponse(success=True, message="Campaign deleted")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))





# =============================================================================
# Chatbot Endpoint (Consolidated — replaces former ai_chat.py router)
# =============================================================================
@router.post("/chat", response_model=StandardResponse)
async def chat_api(req: ChatRequest, request: Request) -> StandardResponse:
    """
    AI Chatbot with LLM tool calling.

    Accepts a conversation history and returns the assistant's response.
    The chatbot can autonomously execute backend tools (search products,
    post social ads, send emails, trigger fulfillment, etc.) based on
    natural language queries.
    """
    prisma = request.app.state.prisma
    response_message = await chat_with_agent(req.messages, prisma)
    return StandardResponse(success=True, data=response_message)


# =============================================================================
# Social Media — Manual Trigger & Status Endpoints
# =============================================================================
@router.post("/social/trigger", response_model=StandardResponse)
async def trigger_social_post(request: Request) -> StandardResponse:
    """
    Manually trigger one full marketing loop iteration immediately.
    This selects the next product in the rotation, generates AI copy,
    and posts to Facebook + Instagram (if auto-approve is ON).
    """
    import asyncio
    from services.scheduler import execute_marketing_loop
    logger.info("[MANUAL TRIGGER] Admin manually triggered marketing loop")
    # Fire and forget — don't block the HTTP response
    asyncio.create_task(execute_marketing_loop())
    return StandardResponse(
        success=True,
        message="Marketing loop triggered. Check logs or /api/v1/social/recent-posts for results."
    )


@router.get("/social/recent-posts", response_model=StandardResponse)
async def get_recent_social_posts(request: Request) -> StandardResponse:
    """
    Returns the 10 most recent social post records from the database,
    including status (DRAFT / POSTED / FAILED), platform, caption snippet,
    and post IDs.
    """
    prisma = request.app.state.prisma
    try:
        posts = await prisma.socialpost.find_many(
            order={"createdAt": "desc"},
            take=10,
            include={"campaign": True},
        )
        data = [
            {
                "id": p.id,
                "campaignId": p.campaignId,
                "platform": p.platform,
                "type": p.type,
                "status": p.status,
                "caption": (p.caption or "")[:120] + ("..." if len(p.caption or "") > 120 else ""),
                "fbPostId": p.fbPostId,
                "igPostId": p.igPostId,
                "postedAt": p.postedAt.isoformat() if p.postedAt else None,
                "scheduledAt": p.scheduledAt.isoformat() if p.scheduledAt else None,
                "errorLog": p.errorLog,
            }
            for p in posts
        ]
        return StandardResponse(success=True, data=data)
    except Exception as e:
        logger.error(f"Failed to fetch recent social posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social/scheduler-status", response_model=StandardResponse)
async def get_scheduler_status(request: Request) -> StandardResponse:
    """
    Returns the next scheduled marketing loop run time and auto-approve status.
    """
    from datetime import timezone
    prisma = request.app.state.prisma
    scheduler = request.app.state.scheduler

    next_run = None
    try:
        job = scheduler.get_job("marketing_loop")
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()
    except Exception:
        pass

    state = await prisma.marketingstate.find_unique(where={"id": "singleton"})
    return StandardResponse(
        success=True,
        data={
            "schedulerRunning": scheduler.running if scheduler else False,
            "nextRunAt": next_run,
            "autoApprove": state.autoApprove if state else False,
            "lastSocialIdx": state.lastSocialIdx if state else 0,
            "lastEmailIdx": state.lastEmailIdx if state else 0,
        }
    )
