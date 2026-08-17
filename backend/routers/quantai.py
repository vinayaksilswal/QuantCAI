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

# Enterprise Knowledge Base & Context Engine
from quantai_knowledge import (
    build_context_prompt,
    get_suggestions_for_route,
    get_welcome_message,
    PLATFORM_KNOWLEDGE,
    ENTERPRISE_PLAYBOOK,
    LEARNING_CURRICULUM,
)

logger = logging.getLogger("quantcai.quantai")
router = APIRouter(prefix="/api/v1/quantai", tags=["QuantAI Copilot"])

# Initialize LLM
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


# ---------------------------------------------------------------------------
# Tool Definitions — UI controls & platform actions the AI can invoke
# ---------------------------------------------------------------------------

@tool
def open_tool(tool_name: str):
    """Opens a tool or page in the application.
    Allowed values for tool_name: 'quantum-states', 'circuit-builder', 'pqc-scanner'"""
    pass

@tool
def manage_circuit(action: str, params: dict):
    """Manages the multi-qubit circuit builder.
    action can be 'add_gate', 'clear', or 'run'.
    For 'add_gate', params should be {'gate': 'h', 'qubit': 0} for single-qubit gates
    or {'gate': 'cx', 'control': 0, 'target': 1} for multi-qubit gates.
    Available single-qubit gates: h, x, y, z, s, t, rx, ry, rz
    Available multi-qubit gates: cx (CNOT), cz, swap
    For 'clear' and 'run', params can be {}.
    """
    pass

@tool
def navigate_to_page(path: str, section: str = ""):
    """Navigates to any page on the QuantCAI platform.
    Available paths:
    - '/learn' — Learning hub introduction
    - '/quantum-computing' — Quantum computing fundamentals
    - '/learn/qubits' — Deep dive into qubits, superposition, measurement
    - '/learn/gates' — Quantum gates (Hadamard, CNOT, Pauli, etc.)
    - '/learn/pqc' — Post-Quantum Cryptography (NIST FIPS 203/204/205)
    - '/quantum-states' — Interactive Bloch Sphere visualizer
    - '/circuit-builder' — Multi-qubit circuit builder
    - '/quantum-simulator' — OpenQASM 2.0 code editor and simulator
    - '/pqc-scanner' — PQC vulnerability scanner
    - '/repo-scanner' — GitHub repository scanner
    - '/enterprise' — Enterprise offerings, CLI scanner, on-prem deployment
    - '/tools' — All tools overview
    - '/community' — Community discussions
    - '/profile' — User profile and subscription management
    section is an optional anchor (e.g., 'entanglement', 'quiz').
    Use this to guide users to the most relevant page for their question."""
    pass

@tool
def suggest_learning_path(current_topic: str):
    """Recommends the next learning step in the QuantCAI curriculum.
    Call this when a user completes a topic or asks 'what should I learn next?'
    The learning path order is:
    1. Introduction (/learn) — What is quantum computing
    2. Quantum Computing (/quantum-computing) — Fundamentals
    3. Qubits (/learn/qubits) — Superposition, measurement, Dirac notation
    4. Quantum Gates (/learn/gates) — H, X, Y, Z, CNOT, circuit building
    5. Post-Quantum Cryptography (/learn/pqc) — NIST standards, migration
    current_topic should be the topic name or route the user just completed."""
    pass

@tool
def explain_quiz_hint(page: str, question_index: int = 0):
    """Provides a Socratic teaching hint for a quiz question on a learning page.
    NEVER reveal the answer directly — guide the student to discover it.
    page should be the route like '/learn', '/learn/qubits', '/learn/gates', '/learn/pqc'.
    question_index is usually 0 (first quiz on the page)."""
    pass

@tool
def show_circuit_template(template_name: str):
    """Loads a pre-built circuit template in the Circuit Builder.
    Available templates:
    - 'bell-state' — Creates entangled Bell pair (H + CNOT)
    - 'ghz-state' — Greenberger-Horne-Zeilinger state (3-qubit entanglement)
    - 'teleportation' — Quantum teleportation protocol
    - 'grovers' — Grover's search algorithm
    - 'bernstein-vazirani' — Bernstein-Vazirani algorithm
    - 'qft' — Quantum Fourier Transform
    - 'deutsch-jozsa' — Deutsch-Jozsa algorithm
    - 'superdense-coding' — Superdense coding protocol
    Use this when a user asks to see or build a specific algorithm."""
    pass

@tool
def start_tutorial(tutorial_id: str):
    """Starts an interactive step-by-step tutorial in the Circuit Builder.
    Available tutorials: 'bell-state', 'teleportation'.
    This opens a guided overlay that walks the user through building the circuit."""
    pass

@tool
def apply_gate_to_visualizer(gate: str):
    """Applies a quantum gate to the single-qubit Bloch Sphere visualizer.
    Available gates: 'H' (Hadamard), 'X' (Pauli-X/NOT), 'Y' (Pauli-Y), 'Z' (Pauli-Z),
    'S' (Phase), 'T' (π/8 gate).
    Use this to demonstrate gate effects visually on the Bloch sphere."""
    pass

@tool
def run_pqc_scan(target_url: str):
    """Runs a Post-Quantum Cryptography vulnerability scan against a target domain URL.
    The scan analyzes: TLS version, certificate chain, cipher suites, key exchange algorithms,
    and signature algorithms. Returns a PQC readiness score (0-100) with risk classification.
    Example: run_pqc_scan('example.com')
    Note: Only works on public domains. For internal/private network scanning,
    recommend the QuantCAI CLI Scanner (enterprise feature)."""
    pass

@tool
def recommend_enterprise_action(action_type: str):
    """Shows enterprise call-to-action buttons in the chat UI.
    action_type values:
    - 'demo' — Shows 'Request Custom Demo' button linking to /enterprise
    - 'email' — Shows 'Email Enterprise Team' button for quantc.info@gmail.com
    - 'register_org' — Shows 'Register Organization' button for /signup?plan=enterprise
    - 'cli_info' — Shows CLI scanner information with installation and usage details
    Use this when detecting enterprise buying signals or when users ask about features
    only available on the Enterprise plan (internal scanning, on-prem, SLAs)."""
    pass

# Bind all tools to the LLM
ALL_TOOLS = [
    open_tool, manage_circuit, navigate_to_page, suggest_learning_path,
    explain_quiz_hint, show_circuit_template, start_tutorial,
    apply_gate_to_visualizer, run_pqc_scan, recommend_enterprise_action,
]

llm = None
llm_with_tools = None

if api_key:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.2
        )
        llm_with_tools = llm.bind_tools(ALL_TOOLS)
    except Exception as e:
        logger.warning(f"Could not initialize QuantAI ChatGoogleGenerativeAI: {e}")
else:
    logger.warning("GEMINI_API_KEY is not set. QuantAI features will be disabled.")


# ---------------------------------------------------------------------------
# Multi-Persona Base Prompts
# ---------------------------------------------------------------------------

LEARNER_PERSONA = (
    "You are QuantAI, the intelligent quantum computing tutor for the QuantCAI platform.\n\n"
    "TEACHING STYLE:\n"
    "- Use the Socratic method: ask what the student knows first, then build incrementally\n"
    "- Simplify complex concepts using everyday analogies\n"
    "- Always end with a follow-up question that checks understanding\n"
    "- When students ask about quizzes, guide them WITHOUT revealing answers\n"
    "- Reference the specific content visible on their current page\n"
    "- Proactively suggest hands-on exercises using platform tools\n\n"
    "INTERACTION RULES:\n"
    "- Use tools to DEMONSTRATE, don't just describe. Build circuits, apply gates, navigate to pages.\n"
    "- When a student says 'build a Bell State', actually use manage_circuit to build it step by step.\n"
    "- When they finish a topic, use suggest_learning_path to recommend what's next.\n"
    "- When they struggle with a quiz, use explain_quiz_hint for Socratic guidance.\n"
    "- Format math using LaTeX: $...$ for inline, $$...$$ for blocks.\n"
    "- Keep responses concise but educational. Aim for 2-4 paragraphs max.\n"
)

BUILDER_PERSONA = (
    "You are QuantAI, the quantum circuit design assistant for the QuantCAI platform.\n\n"
    "EXPERTISE:\n"
    "- Quantum circuit design, optimization, and debugging\n"
    "- OpenQASM 2.0 syntax and best practices\n"
    "- Gate decomposition and circuit depth optimization\n"
    "- All standard quantum algorithms (Grover's, Shor's, QFT, VQE, QAOA)\n\n"
    "INTERACTION RULES:\n"
    "- When asked to build a circuit, use manage_circuit to build it step by step (clear → add gates → run)\n"
    "- When showing QASM code, always format inside ```qasm blocks\n"
    "- Analyze the user's current circuit state and provide specific feedback\n"
    "- Suggest circuit templates when relevant using show_circuit_template\n"
    "- Explain measurement results and probability distributions clearly\n"
    "- For beginners, relate circuit concepts back to the learning modules\n"
    "- For advanced users, discuss optimization techniques (gate cancellation, commutation)\n"
)

SECURITY_PERSONA = (
    "You are QuantAI, the Post-Quantum Cryptography security analyst for the QuantCAI platform.\n\n"
    "EXPERTISE:\n"
    "- NIST PQC standards: FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA)\n"
    "- CNSA 2.0 timeline and migration requirements\n"
    "- TLS/SSL security analysis and certificate chain inspection\n"
    "- Cryptographic risk assessment and HNDL (Harvest Now, Decrypt Later) threats\n"
    "- Cipher suite evaluation and quantum vulnerability classification\n\n"
    "INTERACTION RULES:\n"
    "- Use run_pqc_scan to proactively scan domains when users ask about security\n"
    "- Interpret scan results with specific remediation steps\n"
    "- Reference NIST standards by number (FIPS 203/204/205)\n"
    "- For internal network scanning needs, explain the CLI scanner and use recommend_enterprise_action\n"
    "- Provide actionable migration roadmaps (RSA-2048 → ML-KEM-768, ECC-256 → ML-DSA-65)\n"
    "- Discuss compliance timelines and regulatory requirements\n"
)

ENTERPRISE_PERSONA = (
    "You are QuantAI (LQM — Large Quantitative Model), the enterprise PQC compliance advisor.\n\n"
    "EXPERTISE:\n"
    "- Enterprise post-quantum migration strategy\n"
    "- Cryptographic Bill of Materials (CBOM) assessment\n"
    "- Internal network scanning with the QuantCAI CLI Scanner\n"
    "- On-premises deployment architecture\n"
    "- Compliance frameworks: NIST PQC, CNSA 2.0, SOC2, ISO 27001\n"
    "- License management and team access control (RBAC)\n\n"
    "CLI SCANNER KNOWLEDGE:\n"
    "The QuantCAI PQC Scanner CLI is an enterprise tool for internal network scanning.\n"
    "Installation: pip install quantcai-scanner\n"
    "Commands:\n"
    "  quantcai-scanner scan --target example.com          # Scan a single domain\n"
    "  quantcai-scanner scan --target 192.168.1.0/24       # Scan CIDR range\n"
    "  quantcai-scanner scan --target internal.corp.net --port 443 --timeout 10\n"
    "  quantcai-scanner scan --target 10.0.0.0/16 --output json  # JSON report for SIEM\n"
    "  quantcai-scanner scan --target 172.16.0.0/12 --threads 20 # Parallel scanning\n"
    "  quantcai-scanner report --format pdf --input results.json  # Generate PDF report\n"
    "Features: CIDR range scanning, JSON/PDF reports, CI/CD integration, air-gapped support.\n"
    "License: Enterprise license required — contact quantc.info@gmail.com\n\n"
    "INTERACTION RULES:\n"
    "- Provide professional, enterprise-grade responses\n"
    "- When users ask about scanning internal networks, explain CLI scanner capabilities with specific commands\n"
    "- Use recommend_enterprise_action to show CTAs (demo, email, register)\n"
    "- Guide to quantc.info@gmail.com for custom pricing and SLAs\n"
    "- Discuss on-prem deployment options (Docker Compose, Helm charts, Kubernetes)\n"
    "- Always be helpful first — answer their question, then suggest enterprise features\n"
    "- Highlight the value of enterprise features with ROI-focused language\n"
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class QuantAIChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = Field(default=None, description="Optional UUID tracking conversation history.")
    context: Optional[str] = Field(default=None, description="Active context: 'learn', 'circuit-builder', 'qasm-ide', 'pqc-scanner'")
    client_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata from the active view.")
    current_route: Optional[str] = Field(default=None, description="Current frontend route path.")


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


def _select_persona(route: str, tier: str, user_role: Optional[str] = None) -> str:
    """Select the appropriate base persona prompt based on route, tier, and role."""
    route = route or "/"

    # Enterprise users get enterprise persona on enterprise/scanner pages
    is_enterprise_user = tier.upper() == "ENTERPRISE" or user_role in ("enterprise_user", "root")

    if is_enterprise_user and not route.startswith("/sandbox"):
        if route.startswith("/pqc-scanner") or route.startswith("/repo-scanner") or route.startswith("/enterprise"):
            return ENTERPRISE_PERSONA
        # Enterprise users on other pages still get enhanced persona
        return ENTERPRISE_PERSONA

    if route.startswith("/pqc-scanner") or route.startswith("/repo-scanner"):
        return SECURITY_PERSONA
    elif route.startswith("/enterprise"):
        return ENTERPRISE_PERSONA
    elif route.startswith("/circuit-builder") or route.startswith("/quantum-simulator") or route.startswith("/sandbox"):
        return BUILDER_PERSONA
    elif route.startswith("/quantum-states"):
        return BUILDER_PERSONA
    else:
        return LEARNER_PERSONA


# ---------------------------------------------------------------------------
# Suggestions Endpoint
# ---------------------------------------------------------------------------

@router.get("/suggestions")
async def get_ai_suggestions(
    route: str = "/",
    tier: str = "FREE",
):
    """Returns contextual suggestion chips for the AI assistant UI."""
    suggestions = get_suggestions_for_route(route, tier)
    welcome = get_welcome_message(route, tier)
    return {"suggestions": suggestions, "welcome_message": welcome}


# ---------------------------------------------------------------------------
# Main Chat Endpoint
# ---------------------------------------------------------------------------

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

    Enterprise-grade features:
    - Multi-persona context switching (Learner, Builder, Security, Enterprise)
    - Deep platform knowledge via quantai_knowledge module
    - Dynamic prompt assembly based on current page and user state
    - Rich tool integration for interactive experiences
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

    # 2. Determine current route from client context or body
    current_route = body.current_route or body.client_context.get("current_route", "/") if body.client_context else "/"
    # Fallback: infer route from context name
    if current_route == "/" and body.context:
        route_map = {
            "learn": "/learn",
            "circuit-builder": "/circuit-builder",
            "qasm-ide": "/quantum-simulator",
            "pqc-scanner": "/pqc-scanner",
            "quantum-states": "/quantum-states",
            "enterprise": "/enterprise",
        }
        current_route = route_map.get(body.context, "/")

    user_role = current_user.role.value if current_user.role else None

    # 3. Build dynamic system prompt: base persona + contextual knowledge
    base_persona = _select_persona(current_route, tier, user_role)
    context_knowledge = build_context_prompt(
        route=current_route,
        tier=tier,
        client_context=body.client_context or {},
        user_role=user_role,
    )
    full_system_prompt = base_persona + "\n\n" + context_knowledge

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
        messages = [SystemMessage(content=full_system_prompt)]
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

        # Build the user message with context metadata
        context_parts = []
        # Workspace-aware context is a paid capability: the assistant can only
        # see the user's live circuit/scan state on Pro and above. On FREE the
        # client_context is dropped, so answers stay generic. This is the
        # documented tier split and one of the clearer reasons to upgrade.
        workspace_context_allowed = str(tier).upper() != "FREE"
        if body.client_context and workspace_context_allowed:
            # Include relevant client context for the AI to understand the user's state
            filtered_context = {k: v for k, v in body.client_context.items()
                               if k not in ("current_route",) and v is not None}
            if filtered_context:
                context_parts.append(f"[Page Context: {json.dumps(filtered_context)}]")
        context_parts.append(body.message)
        user_payload = "\n".join(context_parts)
        messages.append(HumanMessage(content=user_payload))

        # Send initial metadata (conversation ID + dynamic suggestions)
        suggestions = get_suggestions_for_route(current_route, tier, body.client_context)
        welcome = get_welcome_message(current_route, tier, body.client_context)
        yield f"data: {json.dumps({'type': 'meta', 'conversation_id': conversation_id, 'suggestions': suggestions, 'welcome_message': welcome})}\n\n"

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
            yield f"data: {json.dumps({'type': 'text', 'content': 'I encountered an issue generating a response. Please try again.'})}\n\n"

        # Save turn back to history
        history.append({"role": "user", "content": body.message})
        history.append({
            "role": "assistant",
            "content": full_response,
            "tool_calls": tool_calls_collected
        })
        # Keep last 15 turns (30 messages)
        history = history[-30:]
        try:
            await redis_client.setex(history_key, 86400, json.dumps(history))
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")
