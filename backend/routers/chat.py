from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import logging
import DBmodels
from auth_utils import get_current_user
from fastapi.responses import StreamingResponse
from QuantAI import run_chat_stream
import json

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
    
    return StreamingResponse(
        run_chat_stream(request.message, request.history),
        media_type="text/event-stream"
    )

