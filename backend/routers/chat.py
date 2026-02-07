from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import logging
import DBmodels
from auth_utils import get_current_user
from QuantAI import run_chat

router = APIRouter(prefix="/api", tags=["chat"])
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, current_user: DBmodels.User = Depends(get_current_user)):
    """
    Chat with the Quantum AI Assistant.
    """
    logger.info(f"Chat request from user: {current_user.email}")
    try:
        response_text = run_chat(request.message, request.history)
        return ChatResponse(response=response_text)
    except Exception as e:
        error_str = str(e)
        logger.error(f"Error in chat endpoint: {error_str}", exc_info=True)
        
        # Check for 429 / Resource Exhausted errors
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            raise HTTPException(
                status_code=503, 
                detail="The AI service is currently experiencing high load or rate limits. Please try again in a moment."
            )
            
        raise HTTPException(status_code=500, detail="Failed to process chat request")
