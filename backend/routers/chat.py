from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List
import logging
import models as DBmodels
from core.auth import get_current_user
from fastapi.responses import StreamingResponse
from services.ai import run_chat_stream

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, current_user: DBmodels.User = Depends(get_current_user)):
    """
    Chat with the Quantum AI Assistant (Streaming).
    """
    logger.info(f"Chat request from user: {current_user.email}")
    
    try:
        return StreamingResponse(
            run_chat_stream(request.message, request.history),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error in chat_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal AI Error")
