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
from services.ai_service import generate_product_copy
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


class ProductUpdate(BaseModel):
    """Request model for updating a product."""
    productName: Optional[str] = None
    sellPrice: Optional[float] = None
    originalPrice: Optional[float] = None
    costPrice: Optional[float] = None
    inventory: Optional[int] = None
    categoryName: Optional[str] = None
    description: Optional[str] = None
    highlights: Optional[List[str]] = None
    productImage: Optional[str] = None
    productImages: Optional[List[str]] = None
    productVideo: Optional[str] = None
    uploadedVideo: Optional[str] = None
    tagline: Optional[str] = None


class ReorderRequest(BaseModel):
    """Request model for moving a product up or down."""
    direction: str = Field(..., description="'up' or 'down'")




class RewriteRequest(BaseModel):
    """Request model for AI product copy rewrite."""
    title: str
    description: str


class ChatRequest(BaseModel):
    """Request model for the AI chatbot."""
    messages: List[Dict[str, Any]] = Field(
        ..., description="Conversation messages array"
    )


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
        
        import base64
        import gc
        
        encoded_parts = []
        chunk_size = 3 * 1024 * 1024 # 3MB chunk (must be multiple of 3)
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            encoded_parts.append(base64.b64encode(chunk).decode('ascii'))
            del chunk
            
        encoded_data = "".join(encoded_parts)
        del encoded_parts
        gc.collect()
        
        media_record = await prisma.media.create(
            data={
                "filename": file.filename or "uploaded_media",
                "mimeType": mime_type,
                "data": encoded_data
            }
        )
        
        del encoded_data
        gc.collect()
        
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
    if isinstance(raw_data, (bytes, bytearray)):
        raw_data = raw_data.decode('ascii')
    
    try:
        data_bytes = base64.b64decode(raw_data)
    except Exception:
        # Fallback: data may already be raw bytes in some Prisma Bytes fields
        data_bytes = raw_data.encode('latin-1') if isinstance(raw_data, str) else bytes(raw_data)
        
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
# Product Endpoints
# =============================================================================
@router.get("/products/{pid}", response_model=StandardResponse)
async def get_product(pid: str, request: Request) -> StandardResponse:
    """Get a single product by its PID (CJ product identifier)."""
    prisma = request.app.state.prisma
    product = await prisma.product.find_unique(where={"pid": pid})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return StandardResponse(success=True, data=product.model_dump())


@router.put("/products/{pid}", response_model=StandardResponse)
async def update_product(
    pid: str, data: ProductUpdate, request: Request
) -> StandardResponse:
    """Update a product by its PID."""
    prisma = request.app.state.prisma
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    try:
        updated = await prisma.product.update(
            where={"pid": pid},
            data=update_data,
        )
        return StandardResponse(success=True, data=updated.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/products/{pid}", response_model=StandardResponse)
async def delete_product(pid: str, request: Request) -> StandardResponse:
    """Delete a product by its PID."""
    prisma = request.app.state.prisma
    try:
        await prisma.product.delete(where={"pid": pid})
        return StandardResponse(success=True, message="Product deleted")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/products/{pid}/reorder", response_model=StandardResponse)
async def reorder_product(
    pid: str, req: ReorderRequest, request: Request
) -> StandardResponse:
    """Move a product up or down the catalog."""
    prisma = request.app.state.prisma
    
    # Fetch all products sorted
    all_products = await prisma.product.find_many(
        order=[
            {"manualSortOrder": "asc"},
            {"listCount": "desc"}
        ]
    )
    
    if not all_products:
        return StandardResponse(success=False, message="No products found")

    # Initialize manualSortOrder for products that don't have it
    needs_update = False
    for idx, p in enumerate(all_products):
        if p.manualSortOrder is None or p.manualSortOrder != idx:
            p.manualSortOrder = idx
            needs_update = True
            
    if needs_update:
        for p in all_products:
            await prisma.product.update(
                where={"id": p.id},
                data={"manualSortOrder": p.manualSortOrder}
            )

    curr_idx = next((i for i, p in enumerate(all_products) if p.pid == pid), -1)
    if curr_idx == -1:
        raise HTTPException(status_code=404, detail="Product not found")

    swap_idx = curr_idx - 1 if req.direction == "up" else curr_idx + 1
    
    if 0 <= swap_idx < len(all_products):
        curr_p = all_products[curr_idx]
        swap_p = all_products[swap_idx]
        
        await prisma.product.update(
            where={"id": curr_p.id},
            data={"manualSortOrder": swap_p.manualSortOrder}
        )
        await prisma.product.update(
            where={"id": swap_p.id},
            data={"manualSortOrder": curr_p.manualSortOrder}
        )
        
        return StandardResponse(success=True, message="Reordered successfully")
    else:
        return StandardResponse(success=False, message="Cannot move further")




# =============================================================================
# AI Endpoints
# =============================================================================
@router.post("/gemini/rewrite", response_model=StandardResponse)
async def rewrite_product_api(req: RewriteRequest) -> StandardResponse:
    """
    Run AI rewrite on raw product title and description.
    Returns premium e-commerce copy with title, description, highlights, tagline.
    """
    ai_copy = await generate_product_copy(req.title, req.description)
    return StandardResponse(success=True, data=ai_copy)


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
            include={"product": True},
        )
        data = [
            {
                "id": p.id,
                "productName": p.product.productName if p.product else None,
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
