import os
import re
import json
import uuid
import logging
import asyncio
from datetime import datetime, timezone
from typing import TypedDict, Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import models as DBmodels
from core.database import get_db
from core.auth import get_current_user
from security import get_subscription_plan, redis_client
from quantum_engine import submit_simulation, get_simulation_status, SimulateRequest

# LangChain + LangGraph
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel as PydanticBaseModel

# Router configuration
router = APIRouter(tags=["tutor"])
logger = logging.getLogger("quantcai.tutor")

# LLM Configuration
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.warning("Neither GEMINI_API_KEY nor GOOGLE_API_KEY found in environment.")

# Initialize primary tutor LLM (Gemini 1.5 Pro)
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=api_key,
    temperature=0
)

# Socratic prompt for tutor
TUTOR_SYSTEM_PROMPT = (
    "You are the QuantCAI Quantum Computing Tutor. You teach quantum computing through Socratic dialogue. "
    "Never just give answers — ask the student what they already know first, then build incrementally. "
    "When a student asks about a concept, explain it at their level, then ask a follow-up question that checks understanding. "
    "When they request a simulation, generate valid OpenQASM 2.0 code and explain what each gate does line-by-line."
)

# -----------------------------------------------------------------------------
# LangGraph Definitions
# -----------------------------------------------------------------------------

class TutorState(TypedDict):
    # Input parameters
    message: str
    conversation_id: str
    user_id: int
    is_pro: bool
    db: AsyncSession
    request: Request
    
    # Execution states & Outputs
    usage_exceeded: bool
    intent: Optional[str]
    response: Optional[str]
    circuit_result: Optional[dict]

# Structured classification schemas
class IntentClassifier(PydanticBaseModel):
    intent: str = Field(
        ...,
        description="Must be exactly one of: 'conceptual_question', 'simulation_request', 'math_help', 'off_topic'"
    )

class SimulationResponse(PydanticBaseModel):
    openqasm_code: str = Field(
        ...,
        description="Valid OpenQASM 2.0 code starting with 'OPENQASM 2.0;' and including 'qelib1.h'. Must include measurements."
    )
    explanation: str = Field(
        ...,
        description="Line-by-line explanation of what each gate does."
    )

# Setup structured outputs
try:
    structured_classifier = llm.with_structured_output(IntentClassifier)
except Exception as e:
    logger.warning(f"Could not initialize structured intent classifier: {e}")
    structured_classifier = None

try:
    structured_simulation = llm.with_structured_output(SimulationResponse)
except Exception as e:
    logger.warning(f"Could not initialize structured simulation generator: {e}")
    structured_simulation = None


# Helper: query daily usage count
async def get_tutor_queries_today(db: AsyncSession, user_id: int) -> int:
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    stmt = select(func.count(DBmodels.UsageEvent.id)).where(
        DBmodels.UsageEvent.user_id == user_id,
        DBmodels.UsageEvent.event_type == DBmodels.UsageEventType.TUTOR_QUERY,
        DBmodels.UsageEvent.created_at >= today_start
    )
    result = await db.execute(stmt)
    return result.scalar() or 0


# --- Node 1: usage_check ---
async def usage_check_node(state: TutorState) -> Dict[str, Any]:
    db = state["db"]
    user_id = state["user_id"]
    is_pro = state["is_pro"]
    
    if is_pro:
        return {"usage_exceeded": False}
    
    try:
        queries_today = await get_tutor_queries_today(db, user_id)
        if queries_today >= 5:
            return {
                "usage_exceeded": True,
                "response": "You have reached your daily limit of 5 free tutor queries. Upgrade to Pro for unlimited access!",
                "intent": "off_topic",
                "circuit_result": None
            }
        return {"usage_exceeded": False}
    except Exception as e:
        logger.error(f"Error in usage_check_node: {e}", exc_info=True)
        # default to blocking to prevent abuse if DB goes down
        return {
            "usage_exceeded": True,
            "response": "Tutor service is temporarily unavailable. Please try again later.",
            "intent": "off_topic"
        }


# --- Node 2: classify_intent ---
async def classify_intent_node(state: TutorState) -> Dict[str, Any]:
    message = state["message"]
    
    classify_prompt = [
        SystemMessage(content=(
            "You are an intent classifier for a quantum computing tutor. Classify the user's message into one of these categories:\n"
            "- 'conceptual_question': Asking about quantum concepts, theories, gates, physics, history, etc.\n"
            "- 'simulation_request': Asking to run a simulation, build/run a circuit, write code for a quantum circuit, or generate/execute OpenQASM.\n"
            "- 'math_help': Asking to solve a math problem, calculate amplitudes/probabilities, work out Dirac notation / linear algebra steps.\n"
            "- 'off_topic': Conversations unrelated to quantum computing, quantum mechanics, or math/simulation of quantum systems.\n\n"
            "Return JSON with the 'intent' key containing exactly one of the values."
        )),
        HumanMessage(content=message)
    ]
    
    intent = "conceptual_question"
    if structured_classifier:
        try:
            res = await structured_classifier.ainvoke(classify_prompt)
            if res.intent in ["conceptual_question", "simulation_request", "math_help", "off_topic"]:
                intent = res.intent
        except Exception as e:
            logger.error(f"Structured intent classification failed: {e}", exc_info=True)
            # fallback below
            structured_classifier_failed = True
    
    if not structured_classifier or 'structured_classifier_failed' in locals():
        try:
            res = await llm.ainvoke(classify_prompt)
            content = res.content.lower()
            if "simulation_request" in content or "simulation" in content or "circuit" in content or "openqasm" in content or "qasm" in content:
                intent = "simulation_request"
            elif "math_help" in content or "math" in content or "calculate" in content or "dirac" in content or "linear algebra" in content:
                intent = "math_help"
            elif "off_topic" in content or "offtopic" in content:
                intent = "off_topic"
            else:
                intent = "conceptual_question"
        except Exception as e:
            logger.error(f"Fallback intent classification failed: {e}", exc_info=True)
            intent = "conceptual_question"
            
    return {"intent": intent}


# --- Node 3: generate_response ---
async def generate_response_node(state: TutorState) -> Dict[str, Any]:
    intent = state["intent"]
    message = state["message"]
    conversation_id = state["conversation_id"]
    user_id = state["user_id"]
    db = state["db"]
    request = state["request"]
    
    response = ""
    circuit_result = None
    
    # 1. Fetch conversation history from Redis
    history_key = f"tutor_history:{conversation_id}"
    history = []
    try:
        raw_history = await redis_client.get(history_key)
        if raw_history:
            history = json.loads(raw_history)
    except Exception as e:
        logger.error(f"Failed to read history from Redis: {e}", exc_info=True)
        
    try:
        if intent == "conceptual_question":
            # Call Gemini Pro with System Prompt + History + User Message
            messages = [SystemMessage(content=TUTOR_SYSTEM_PROMPT)]
            for turn in history:
                if turn.get("role") == "user":
                    messages.append(HumanMessage(content=turn["content"]))
                else:
                    messages.append(AIMessage(content=turn["content"]))
            messages.append(HumanMessage(content=message))
            
            res = await llm.ainvoke(messages)
            response = res.content
            
        elif intent == "simulation_request":
            # Generate valid OpenQASM 2.0 and explanation
            sim_prompt = [
                SystemMessage(content=(
                    "You are the QuantCAI Quantum Computing Tutor. The student wants to simulate a quantum circuit.\n"
                    "Generate valid OpenQASM 2.0 code that implements their request, and write a line-by-line explanation of the gates.\n"
                    "Remember: OpenQASM 2.0 must begin with 'OPENQASM 2.0;' and include 'qelib1.h';. "
                    "It must declare qreg and creg. Include measurement gates (e.g. measure q[0] -> c[0];) so measurement results can be simulated.\n"
                    "Provide the response inside the requested JSON format containing 'openqasm_code' and 'explanation'."
                )),
                HumanMessage(content=message)
            ]
            
            qasm_code = ""
            explanation = ""
            
            if structured_simulation:
                try:
                    res = await structured_simulation.ainvoke(sim_prompt)
                    qasm_code = res.openqasm_code
                    explanation = res.explanation
                except Exception as e:
                    logger.error(f"Structured simulation generation failed: {e}", exc_info=True)
                    structured_sim_failed = True
                    
            if not structured_simulation or 'structured_sim_failed' in locals():
                # Fallback manual parsing
                fallback_sim_prompt = [
                    SystemMessage(content=(
                        "You are the QuantCAI Quantum Computing Tutor. Generate valid OpenQASM 2.0 code for the student's request, followed by a line-by-line explanation of what each gate does.\n"
                        "Make sure you format the OpenQASM code inside a ```qasm block so it can be extracted, and write the explanation in plain text after the code block."
                    )),
                    HumanMessage(content=message)
                ]
                res = await llm.ainvoke(fallback_sim_prompt)
                content = res.content
                explanation = content
                
                # Try to extract code blocks
                if "```" in content:
                    parts = content.split("```")
                    for part in parts:
                        cleaned_part = part.strip()
                        if cleaned_part.startswith("qasm") or cleaned_part.startswith("openqasm"):
                            qasm_code = cleaned_part.replace("qasm", "", 1).replace("openqasm", "", 1).strip()
                            explanation = content.replace(f"```{part}```", "").strip()
                            break
                        elif "OPENQASM 2.0" in cleaned_part:
                            qasm_code = cleaned_part
                            explanation = content.replace(f"```{part}```", "").strip()
                            break
                else:
                    match = re.search(r'(OPENQASM 2\.0;.*)', content, re.DOTALL)
                    if match:
                        qasm_code = match.group(1).strip()
                        
            # Ensure we have valid fallback qasm
            if not qasm_code:
                qasm_code = (
                    'OPENQASM 2.0;\n'
                    'include "qelib1.h";\n'
                    'qreg q[2];\n'
                    'creg c[2];\n'
                    'h q[0];\n'
                    'cx q[0],q[1];\n'
                    'measure q -> c;'
                )
                explanation = "Generating standard Bell State (entanglement) circuit because a specific configuration could not be formatted."
                
            response = f"Here is the OpenQASM 2.0 circuit representing your request:\n\n```qasm\n{qasm_code}\n```\n\n### Gate Explanation:\n{explanation}"
            
            # Execute simulation internally
            # Retrieve DB user directly using state['user_id']
            # We fetch user model since submit_simulation requires a User object
            stmt = select(DBmodels.User).where(DBmodels.User.id == user_id)
            user_result = await db.execute(stmt)
            current_user_obj = user_result.scalar_one_or_none()
            
            if current_user_obj:
                try:
                    sim_req = SimulateRequest(circuit_qasm=qasm_code, shots=1024)
                    submit_res = await submit_simulation(
                        body=sim_req,
                        request=request,
                        db=db,
                        current_user=current_user_obj
                    )
                    job_id = submit_res.job_id
                    
                    # Poll for completion
                    for _ in range(50):  # 5 seconds maximum polling time
                        status_res = await get_simulation_status(
                            job_id=job_id,
                            request=request,
                            current_user=current_user_obj
                        )
                        if status_res.status == "complete":
                            if status_res.result:
                                circuit_result = status_res.result.model_dump() if hasattr(status_res.result, "model_dump") else status_res.result
                            break
                        elif status_res.status == "failed":
                            logger.error(f"Internal simulation job {job_id} failed: {status_res.error}")
                            circuit_result = {"error": status_res.error}
                            break
                        await asyncio.sleep(0.1)
                        
                    if not circuit_result:
                        circuit_result = {"error": "Simulation timed out during internal execution."}
                except Exception as e:
                    logger.error(f"Error simulating QASM internally: {e}", exc_info=True)
                    circuit_result = {"error": str(e)}
            else:
                circuit_result = {"error": "Could not resolve user to execute simulation."}
                
        elif intent == "math_help":
            # Step-by-step using LaTeX
            math_prompt = [
                SystemMessage(content=(
                    "You are the QuantCAI Quantum Computing Tutor. Solve the student's mathematical question step-by-step using a clear chain-of-thought.\n"
                    "Ensure all mathematical equations and formulas are in LaTeX format (e.g., $...$ for inline or $$...$$ for block notation).\n"
                    "Explain the concepts behind the math, and end with a Socratic follow-up question checking understanding."
                )),
                HumanMessage(content=message)
            ]
            res = await llm.ainvoke(math_prompt)
            response = res.content
            
        elif intent == "off_topic":
            # Redirect back to quantum computing
            off_topic_prompt = [
                SystemMessage(content=(
                    "You are the QuantCAI Quantum Computing Tutor. The student has asked something off-topic.\n"
                    "Politely redirect them back to quantum computing, offering a couple of interesting quantum concepts they might want to learn about instead."
                )),
                HumanMessage(content=message)
            ]
            res = await llm.ainvoke(off_topic_prompt)
            response = res.content
            
        else:
            response = "I'm sorry, I'm not sure how to address that. Can we return to discussing quantum computing?"
            
    except Exception as e:
        logger.error(f"LLM generation failed for intent {intent}: {e}", exc_info=True)
        response = "I'm sorry, I encountered an issue connecting to my AI processor. Please try again."
        
    # 2. Save turn to Redis conversation history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response})
    # Keep only the last 10 turns (20 messages)
    history = history[-20:]
    try:
        await redis_client.setex(history_key, 86400, json.dumps(history))
    except Exception as e:
        logger.error(f"Failed to write history to Redis: {e}", exc_info=True)
        
    # 3. Log usage event in DB
    try:
        usage_event = DBmodels.UsageEvent(
            user_id=user_id,
            event_type=DBmodels.UsageEventType.TUTOR_QUERY,
            credits_used=1,
            metadata_={"conversation_id": conversation_id, "intent": intent}
        )
        db.add(usage_event)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log usage event: {e}", exc_info=True)
        await db.rollback()

    return {"response": response, "circuit_result": circuit_result}


# -----------------------------------------------------------------------------
# LangGraph Workflow Construction
# -----------------------------------------------------------------------------

workflow = StateGraph(TutorState)

# Add nodes
workflow.add_node("usage_check", usage_check_node)
workflow.add_node("classify_intent", classify_intent_node)
workflow.add_node("generate_response", generate_response_node)

# Add edges
workflow.add_edge(START, "usage_check")

def route_after_usage_check(state: TutorState):
    if state.get("usage_exceeded"):
        return END
    return "classify_intent"

workflow.add_conditional_edges(
    "usage_check",
    route_after_usage_check,
    {
        END: END,
        "classify_intent": "classify_intent"
    }
)
workflow.add_edge("classify_intent", "generate_response")
workflow.add_edge("generate_response", END)

tutor_graph = workflow.compile()


# -----------------------------------------------------------------------------
# FastAPI Endpoint Definition
# -----------------------------------------------------------------------------

class TutorChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = Field(default=None, description="Optional UUID tracking conversation history.")

class TutorChatResponse(BaseModel):
    response: str
    conversation_id: str
    intent: str
    circuit_result: Optional[dict] = None


@router.post(
    "/tutor/chat",
    response_model=TutorChatResponse,
    summary="Chat with the Socratic Quantum AI Tutor",
    description="Endpoint for students to discuss quantum topics, ask math equations, or request circuit simulations."
)
async def tutor_chat_endpoint(
    body: TutorChatRequest,
    request: Request,
    current_user: DBmodels.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Resolve subscription plan
    try:
        plan = await get_subscription_plan(db, current_user.id, current_user.org_id)
        is_pro = plan.lower() in ("pro", "enterprise")
    except Exception as e:
        logger.error(f"Error checking user plan: {e}", exc_info=True)
        is_pro = False
        
    conversation_id = body.conversation_id or str(uuid.uuid4())
    
    initial_state = {
        "message": body.message,
        "conversation_id": conversation_id,
        "user_id": current_user.id,
        "is_pro": is_pro,
        "db": db,
        "request": request,
        "usage_exceeded": False,
        "intent": None,
        "response": None,
        "circuit_result": None
    }
    
    try:
        final_state = await tutor_graph.ainvoke(initial_state)
    except Exception as e:
        logger.error(f"Error executing tutor graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Tutor service encountered an internal AI error."
        )
        
    return TutorChatResponse(
        response=final_state.get("response") or "I could not formulate a response. Please try again.",
        conversation_id=conversation_id,
        intent=final_state.get("intent") or "unknown",
        circuit_result=final_state.get("circuit_result")
    )
