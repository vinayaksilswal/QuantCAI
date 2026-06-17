import os
import json
import uuid
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models as DBmodels
from core.database import get_db
from security import redis_client, get_current_user_or_api_key
from tier_limits import get_user_tier
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger("quantcai.quantai")
router = APIRouter(prefix="/api/v1/quantai", tags=["QuantAI Copilot"])

# Initialize LLM
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=api_key,
    temperature=0.2
)

@tool
def open_tool(tool_name: str):
    """Opens a tool or page in the application. Allowed values for tool_name: 'quantum-states', 'circuit-builder'"""
    pass

@tool
def manage_circuit(action: str, params: dict):
    """Manages the multi-qubit circuit builder. 
    action can be 'add_gate', 'clear', or 'run'.
    For 'add_gate', params should be {'gate': 'h', 'qubit': 0} or {'gate': 'cx', 'control': 0, 'target': 1}.
    For 'clear' and 'run', params can be {}.
    """
    pass

@tool
def navigate_to_learn(section: str):
    """Navigates to the learn page section."""
    pass

@tool
def start_tutorial(tutorial_id: str):
    """Starts an interactive tutorial."""
    pass

@tool
def apply_gate_to_visualizer(gate: str):
    """Applies a quantum gate to the single-qubit visualizer."""
    pass

llm_with_tools = llm.bind_tools([open_tool, manage_circuit, navigate_to_learn, start_tutorial, apply_gate_to_visualizer])

# System prompts for agents
TUTOR_AGENT_PROMPT = (
    "You are the QuantCAI Pedagogical Tutor Agent. You teach quantum computing through Socratic dialogue.\n"
    "Simplify highly technical terms and use conceptual analogies.\n"
    "Do NOT write complex enterprise code.\n"
    "If the user is on a quiz question, review their state and help guide them to the correct answer without just giving it away.\n"
    "Always end with a simple follow-up question checking understanding.\n"
    "You have access to tools to control the UI. Use them to open tools, build circuits, or navigate. "
    "For example, to build a Bell State, use 'open_tool' to open 'circuit-builder', then use 'manage_circuit' multiple times to clear, add an 'h' gate, add a 'cx' gate, and run."
)

COMPILATION_AGENT_PROMPT = (
    "You are the QuantCAI Quantum Compilation Agent. You specialize in quantum circuit design and OpenQASM code optimization.\n"
    "You have access to the user's active circuit or editor code.\n"
    "Focus on spotting syntax bugs, refactoring OpenQASM script segments, and suggesting gate layout optimization techniques.\n"
    "Ensure any generated OpenQASM code is formatted inside a standard ```qasm block so the client can extract it."
)

COMPLIANCE_AGENT_PROMPT = (
    "You are the QuantCAI Offensive Crypto & Post-Quantum Compliance Agent.\n"
    "Focus purely on cryptography standards (FIPS 203/204, ML-KEM, ML-DSA, SLH-DSA), post-quantum migration timelines, risk auditing, and drafting mitigation policies.\n"
    "Use the provided scanner report (vulnerabilities, leaf certificate signature algorithms, TLS version, etc.) to assess HNDL risks and recommend remediation steps."
)

class QuantAIChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = Field(default=None, description="Optional UUID tracking conversation history.")
    context: Optional[str] = Field(default=None, description="Active context: 'learn', 'circuit-builder', 'qasm-ide', 'pqc-scanner'")
    client_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata from the active view.")

async def get_or_create_wallet_initial(db: AsyncSession, user_id: int) -> DBmodels.WalletBalance:
    """Gets the user's wallet balance or initializes it with a default of 10.0 credits."""
    stmt = select(DBmodels.WalletBalance).where(DBmodels.WalletBalance.user_id == user_id)
    res = await db.execute(stmt)
    wallet = res.scalar_one_or_none()
    if not wallet:
        wallet = DBmodels.WalletBalance(user_id=user_id, balance_credits=10.0)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    return wallet

@router.post("/chat")
async def quantai_chat_endpoint(
    body: QuantAIChatRequest,
    request: Request,
    current_user: DBmodels.User = Depends(get_current_user_or_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Asynchronous streaming endpoint for the globally floating QuantAI Copilot.
    Validates either bearer JWT access token or developer X-API-Key header.
    Validates and atomically deducts credits ($0.003/turn) from the user's Redis cache balance.
    """
    # 1. Enforce credit/token check
    tier = await get_user_tier(db, current_user.id)
    request.state.tier = tier

    if tier not in ("PRO", "ENTERPRISE"):
        wallet_cache_key = f"developer:wallet:{current_user.id}"
        balance_val = await redis_client.get(wallet_cache_key)
        
        if balance_val is None:
            wallet = await get_or_create_wallet_initial(db, current_user.id)
            balance = float(wallet.balance_credits)
            await redis_client.set(wallet_cache_key, str(balance))
        else:
            balance = float(balance_val)

        if balance <= 0:
            await redis_client.set(f"developer:wallet_blocked:{current_user.id}", "1")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient funds. Your wallet balance is empty or below the safety threshold."
            )

        # Atomically deduct cost ($0.003 per turn)
        new_balance = await redis_client.incrbyfloat(wallet_cache_key, -0.003)
        if new_balance <= 0:
            await redis_client.set(f"developer:wallet_blocked:{current_user.id}", "1")

    # 2. Select Specialized Agent based on context
    context_name = body.context or "learn"
    if context_name == "learn":
        sys_prompt = TUTOR_AGENT_PROMPT
    elif context_name in ("circuit-builder", "qasm-ide"):
        sys_prompt = COMPILATION_AGENT_PROMPT
    elif context_name == "pqc-scanner":
        sys_prompt = COMPLIANCE_AGENT_PROMPT
    else:
        sys_prompt = TUTOR_AGENT_PROMPT

    conversation_id = body.conversation_id or str(uuid.uuid4())

    async def sse_event_generator():
        # Load chat history from Redis
        history_key = f"quantai_history:{conversation_id}"
        history = []
        try:
            raw_history = await redis_client.get(history_key)
            if raw_history:
                history = json.loads(raw_history)
        except Exception as e:
            logger.error(f"Failed to load history from Redis: {e}")

        # Assemble prompt payload
        messages = [SystemMessage(content=sys_prompt)]
        for turn in history:
            if turn.get("role") == "user":
                messages.append(HumanMessage(content=turn["content"]))
            else:
                tool_calls = turn.get("tool_calls", [])
                messages.append(AIMessage(
                    content=turn.get("content", ""),
                    tool_calls=tool_calls
                ))
                if tool_calls:
                    for tc in tool_calls:
                        messages.append(ToolMessage(
                            content="Tool executed successfully by the client UI.",
                            tool_call_id=tc.get("id", "unknown")
                        ))

        # Build context prompt
        if tier == "FREE":
            context_payload = f"User message: {body.message}"
        else:
            context_payload = f"Active Subsystem Context: {context_name}\nSubsystem Metadata: {json.dumps(body.client_context)}\nUser message: {body.message}"
        messages.append(HumanMessage(content=context_payload))

        # Send initial conversation ID
        yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conversation_id})}\n\n"

        full_response = ""
        tool_calls_collected = []
        try:
            async for chunk in llm_with_tools.astream(messages):
                content_text = ""
                if isinstance(chunk.content, list):
                    for item in chunk.content:
                        if isinstance(item, dict) and "text" in item:
                            content_text += item["text"]
                        elif isinstance(item, str):
                            content_text += item
                elif isinstance(chunk.content, str):
                    content_text = chunk.content

                if content_text:
                    full_response += content_text
                    yield f"data: {json.dumps({'type': 'text', 'content': content_text})}\n\n"
                    
                if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                    for tc in chunk.tool_calls:
                        tool_calls_collected.append(tc)
                        yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name'], 'args': tc['args']})}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"AI Stream processing failed: {e}")
            yield f"data: {json.dumps({'type': 'text', 'content': 'I encountered an issue generating a response.'})}\n\n"

        # Save turn back to history
        history.append({"role": "user", "content": body.message})
        history.append({
            "role": "assistant", 
            "content": full_response,
            "tool_calls": tool_calls_collected
        })
        # Keep last 15 turns
        history = history[-30:]
        try:
            await redis_client.setex(history_key, 86400, json.dumps(history))
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")
