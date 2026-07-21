import logging
import json
import uuid
import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models as DBmodels
from models_billing import WalletBalance
from core.database import get_db
from security import get_current_user_or_api_key, redis_client
from services.quantum import QuantumEngine
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from routers.quantai import open_tool, manage_circuit, navigate_to_page, start_tutorial, apply_gate_to_visualizer, run_pqc_scan

logger = logging.getLogger("quantcai.developer_api")
router = APIRouter(prefix="/api/v1/developer", tags=["Developer APIs"])

# Simulation Schemas
class CircuitSimulateRequest(BaseModel):
    circuit_data: List[Dict[str, Any]]
    num_qubits: int = 5
    shots: int = 1024
    use_noise: bool = False

class QasmSimulateRequest(BaseModel):
    qasm_string: str
    shots: int = 1024
    use_noise: bool = False

class QuantAIChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[str] = "api"

# Helper for wallet deduction
async def deduct_wallet(db: AsyncSession, user_id: int, amount: float):
    stmt = select(WalletBalance).where(WalletBalance.user_id == user_id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    
    if not wallet or wallet.balance_credits < amount:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient wallet balance. Operation requires {amount} credits."
        )
    
    wallet.balance_credits = wallet.balance_credits - amount
    db.add(wallet)
    
    # Log usage event
    usage_event = DBmodels.UsageEvent(
        user_id=user_id,
        event_type=DBmodels.UsageEventType.QPU_RUN if amount > 1.0 else DBmodels.UsageEventType.CHAT_TURN,
        credits_used=int(amount),
        metadata_={"source": "developer_api"}
    )
    db.add(usage_event)
    await db.commit()

@router.post("/simulate/circuit")
async def simulate_circuit(
    request: CircuitSimulateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user_or_api_key)
):
    await deduct_wallet(db, current_user.id, 5.0)  # Standard API simulation cost
    engine = QuantumEngine()
    return engine.run_circuit_v1(request.circuit_data, request.num_qubits, request.shots, request.use_noise)

@router.post("/simulate/qasm")
async def simulate_qasm(
    request: QasmSimulateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user_or_api_key)
):
    await deduct_wallet(db, current_user.id, 5.0)
    engine = QuantumEngine()
    return engine.run_qasm_v1(request.qasm_string, request.shots, request.use_noise)

@router.post("/quantai/chat")
async def quantai_chat(
    request: QuantAIChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user_or_api_key)
):
    await deduct_wallet(db, current_user.id, 0.003)
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="AI API not configured")
        
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key, temperature=0.2)
    llm_with_tools = llm.bind_tools([open_tool, manage_circuit, navigate_to_page, start_tutorial, apply_gate_to_visualizer, run_pqc_scan])
    
    sys_prompt = "You are the QuantCAI Developer AI Assistant. You have access to tools to control the quantum environment."
    messages = [SystemMessage(content=sys_prompt), HumanMessage(content=request.message)]
    
    try:
        response = await llm_with_tools.ainvoke(messages)
    except Exception as e:
        logger.error(f"AI invocation failed: {e}")
        raise HTTPException(status_code=500, detail="AI invocation failed")
        
    tool_calls = []
    if hasattr(response, 'tool_calls') and response.tool_calls:
        tool_calls = response.tool_calls
        
    content_text = ""
    if isinstance(response.content, str):
        content_text = response.content
    elif isinstance(response.content, list):
        for item in response.content:
            if isinstance(item, dict) and "text" in item:
                content_text += item["text"]
            elif isinstance(item, str):
                content_text += item
                
    return {
        "status": "success",
        "response": content_text,
        "tool_calls": tool_calls
    }
