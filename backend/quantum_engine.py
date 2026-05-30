"""
QuantCAI B2D Quantum Simulation API — FastAPI Router
=====================================================
POST /api/v1/simulate   → validate QASM, enforce tier limits, queue Celery task
GET  /api/v1/simulate/{job_id}  → poll job status / retrieve results from Redis
"""

from __future__ import annotations

import os
import re
import json
import uuid
import time
from enum import Enum
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
import structlog

from core.database import get_db
from security import get_current_user_or_api_key, get_subscription_plan
import models as DBmodels

# ---------------------------------------------------------------------------
# Structlog configuration
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger("quantcai.quantum_engine")

# ---------------------------------------------------------------------------
# Redis client (reuses the REDIS_URL from .env)
# ---------------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

# ---------------------------------------------------------------------------
# Constants — Tier Limits
# ---------------------------------------------------------------------------
TIER_LIMITS = {
    "free": {
        "max_shots": 1024,
        "max_qubits": 20,
        "noise_models": {"ideal"},
        "statevector_access": False,
    },
    "pro": {
        "max_shots": 65536,
        "max_qubits": 29,
        "noise_models": {"ideal", "depolarizing", "thermal"},
        "statevector_access": True,
    },
    "enterprise": {
        "max_shots": 65536,
        "max_qubits": 29,
        "noise_models": {"ideal", "depolarizing", "thermal"},
        "statevector_access": True,
    },
}

# Security: patterns that indicate potentially dangerous QASM constructs
FORBIDDEN_QASM_PATTERNS = [
    re.compile(r"\bwhile\b", re.IGNORECASE),
    re.compile(r"\bfor\b", re.IGNORECASE),
    re.compile(r"\bif\b", re.IGNORECASE),
    re.compile(r"\brecursive\b", re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------
class NoiseModelType(str, Enum):
    IDEAL = "ideal"
    DEPOLARIZING = "depolarizing"
    THERMAL = "thermal"


class SimulateRequest(BaseModel):
    """Request body for POST /api/v1/simulate."""

    circuit_qasm: str = Field(
        ...,
        min_length=10,
        description="OpenQASM 2.0 circuit string",
        json_schema_extra={"example": 'OPENQASM 2.0;\ninclude "qelib1.h";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;'},
    )
    shots: int = Field(
        default=1024,
        ge=1,
        description="Number of measurement shots",
    )
    noise_model: NoiseModelType = Field(
        default=NoiseModelType.IDEAL,
        description="Noise model: ideal (free), depolarizing/thermal (pro)",
    )

    @field_validator("circuit_qasm")
    @classmethod
    def must_start_with_openqasm(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped.upper().startswith("OPENQASM"):
            raise ValueError("circuit_qasm must begin with an OPENQASM version header")
        return v


class SimulateSubmitResponse(BaseModel):
    """Response returned immediately after queuing a simulation job."""

    job_id: str
    status: str = "queued"
    estimated_seconds: int = 3


class SimulationResult(BaseModel):
    """Nested result payload returned when a job is complete."""

    counts: dict[str, int]
    statevector: Optional[Any] = None
    execution_time_ms: float
    shots: int
    circuit_depth: int
    num_qubits: int


class JobStatusResponse(BaseModel):
    """Response for GET /api/v1/simulate/{job_id}."""

    job_id: str
    status: str  # queued | running | complete | failed
    result: Optional[SimulationResult] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_qubit_count(qasm_str: str) -> int:
    """
    Parse the number of qubits declared in a QASM string.
    Supports multiple qreg declarations — returns the total.
    """
    total = 0
    for match in re.finditer(r"qreg\s+\w+\s*\[\s*(\d+)\s*\]", qasm_str):
        total += int(match.group(1))
    return total


def _validate_qasm_security(qasm_str: str) -> None:
    """
    Reject QASM strings containing while-loops, for-loops, if-statements,
    or recursive gate definitions — all of which are potential DoS vectors.
    Only scans non-comment lines.
    """
    for line_no, raw_line in enumerate(qasm_str.splitlines(), start=1):
        line = raw_line.split("//")[0].strip()  # strip inline comments
        if not line:
            continue
        for pattern in FORBIDDEN_QASM_PATTERNS:
            if pattern.search(line):
                raise ValueError(
                    f"Forbidden construct detected on line {line_no}: "
                    f"'{pattern.pattern.strip()}' statements are not allowed for security reasons"
                )


def _validate_qasm_parse(qasm_str: str) -> tuple[int, int]:
    """
    Attempt to parse the QASM string with Qiskit.
    Returns (num_qubits, circuit_depth) on success; raises ValueError on failure.
    """
    try:
        from qiskit import QuantumCircuit

        qc = QuantumCircuit.from_qasm_str(qasm_str)
        return qc.num_qubits, qc.depth()
    except Exception as exc:
        raise ValueError(f"QASM parse error: {exc}") from exc


def _estimate_execution_seconds(num_qubits: int, shots: int) -> int:
    """
    Rough heuristic for estimated wall-clock time so the caller can set
    reasonable polling intervals.
    """
    # Exponential scaling: each qubit roughly doubles state-vector size
    base = 0.5
    qubit_factor = 2 ** max(0, num_qubits - 10) * 0.001
    shot_factor = shots / 1024.0
    estimated = base + qubit_factor * shot_factor
    return max(1, min(int(estimated) + 1, 30))


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api/v1", tags=["quantum-simulation"])


@router.post(
    "/simulate",
    response_model=SimulateSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit an OpenQASM circuit for simulation",
    description=(
        "Validates the circuit, checks tier-based feature access, and queues "
        "the simulation job on a Celery worker. Returns a job_id for polling."
    ),
)
async def submit_simulation(
    body: SimulateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user_or_api_key),
):
    request_start = time.monotonic()
    job_id = str(uuid.uuid4())

    # --- Resolve subscription tier -------------------------------------------
    tier = await get_subscription_plan(
        db, current_user.id, getattr(current_user, "org_id", None)
    )
    limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

    log.info(
        "simulation.request_received",
        job_id=job_id,
        user_id=current_user.id,
        tier=tier,
        shots=body.shots,
        noise_model=body.noise_model.value,
    )

    # --- 1. Validate: noise model access ------------------------------------
    if body.noise_model.value not in limits["noise_models"]:
        log.warning(
            "simulation.noise_model_denied",
            job_id=job_id,
            user_id=current_user.id,
            tier=tier,
            requested_noise=body.noise_model.value,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Noise model '{body.noise_model.value}' requires a Pro or Enterprise subscription. "
                f"Your current tier is '{tier}'."
            ),
        )

    # --- 2. Validate: shots limit -------------------------------------------
    if body.shots > limits["max_shots"]:
        log.warning(
            "simulation.shots_exceeded",
            job_id=job_id,
            user_id=current_user.id,
            tier=tier,
            requested_shots=body.shots,
            max_shots=limits["max_shots"],
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Requested {body.shots} shots exceeds the maximum of "
                f"{limits['max_shots']} for the '{tier}' tier."
            ),
        )

    # --- 3. Validate: security scan (forbidden constructs) ------------------
    try:
        _validate_qasm_security(body.circuit_qasm)
    except ValueError as exc:
        log.warning(
            "simulation.qasm_security_violation",
            job_id=job_id,
            user_id=current_user.id,
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # --- 4. Validate: parse the QASM with Qiskit ----------------------------
    try:
        num_qubits, circuit_depth = _validate_qasm_parse(body.circuit_qasm)
    except ValueError as exc:
        log.warning(
            "simulation.qasm_parse_failed",
            job_id=job_id,
            user_id=current_user.id,
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # --- 5. Validate: qubit count -------------------------------------------
    if num_qubits > limits["max_qubits"]:
        log.warning(
            "simulation.qubit_limit_exceeded",
            job_id=job_id,
            user_id=current_user.id,
            tier=tier,
            num_qubits=num_qubits,
            max_qubits=limits["max_qubits"],
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Circuit uses {num_qubits} qubits, which exceeds the maximum of "
                f"{limits['max_qubits']} for the '{tier}' tier."
            ),
        )

    # --- 6. Queue the Celery task -------------------------------------------
    estimated_seconds = _estimate_execution_seconds(num_qubits, body.shots)

    # Store initial job metadata in Redis (TTL = 1 hour)
    job_meta = {
        "job_id": job_id,
        "status": "queued",
        "user_id": current_user.id,
        "tier": tier,
        "circuit_qasm": body.circuit_qasm,
        "shots": body.shots,
        "noise_model": body.noise_model.value,
        "num_qubits": num_qubits,
        "circuit_depth": circuit_depth,
        "submitted_at": time.time(),
        "result": None,
        "error": None,
    }
    await redis_client.setex(
        f"sim_job:{job_id}", 3600, json.dumps(job_meta)
    )

    # Dispatch to Celery (import here to avoid circular imports at module load)
    from worker import run_simulation

    run_simulation.delay(job_id)

    elapsed_ms = (time.monotonic() - request_start) * 1000
    log.info(
        "simulation.job_queued",
        job_id=job_id,
        user_id=current_user.id,
        num_qubits=num_qubits,
        circuit_depth=circuit_depth,
        estimated_seconds=estimated_seconds,
        validation_ms=round(elapsed_ms, 2),
    )

    return SimulateSubmitResponse(
        job_id=job_id,
        status="queued",
        estimated_seconds=estimated_seconds,
    )


@router.get(
    "/simulate/{job_id}",
    response_model=JobStatusResponse,
    summary="Poll simulation job status",
    description="Returns the current status and result (when complete) of a simulation job.",
)
async def get_simulation_status(
    job_id: str,
    request: Request,
    current_user: DBmodels.User = Depends(get_current_user_or_api_key),
):
    log.info(
        "simulation.status_poll",
        job_id=job_id,
        user_id=current_user.id,
    )

    raw = await redis_client.get(f"sim_job:{job_id}")
    if raw is None:
        log.warning(
            "simulation.job_not_found",
            job_id=job_id,
            user_id=current_user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found. It may have expired (results are kept for 1 hour).",
        )

    job_data = json.loads(raw)

    # Ownership check: only the submitting user may poll their own job
    if job_data.get("user_id") != current_user.id:
        log.warning(
            "simulation.unauthorized_poll",
            job_id=job_id,
            requesting_user=current_user.id,
            owning_user=job_data.get("user_id"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this job.",
        )

    result_payload = None
    if job_data["status"] == "complete" and job_data.get("result"):
        result_raw = job_data["result"]
        # Determine statevector visibility based on tier
        tier = job_data.get("tier", "free")
        sv = result_raw.get("statevector") if TIER_LIMITS.get(tier, TIER_LIMITS["free"])["statevector_access"] else None

        result_payload = SimulationResult(
            counts=result_raw["counts"],
            statevector=sv,
            execution_time_ms=result_raw["execution_time_ms"],
            shots=result_raw["shots"],
            circuit_depth=result_raw["circuit_depth"],
            num_qubits=result_raw["num_qubits"],
        )

    return JobStatusResponse(
        job_id=job_id,
        status=job_data["status"],
        result=result_payload,
        error=job_data.get("error"),
    )
