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

from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis
import structlog

from core.config import settings
from core.database import get_db
from security import get_current_user_or_api_key, get_subscription_plan, redis_client
import models as DBmodels
from tier_limits import _extract_qubit_count

log = structlog.get_logger("quantcai.quantum_engine")

# ---------------------------------------------------------------------------
# Constants — Tier Limits
# ---------------------------------------------------------------------------
# This module previously carried its own TIER_LIMITS table, which drifted from
# core.config: it granted the free tier 20 qubits where the config allows 3.
# The stricter config value won only because main.py happens to apply
# enforce_limits("simulator") as a router dependency, which runs first —
# reorder or drop that dependency and the paywall silently widens to 20.
#
# There is now exactly one table: settings.TIER_LIMITS. Resolve through the
# helper below so the lookup cannot silently miss.


def get_tier_limits(tier: str) -> dict:
    """
    Resolve a subscription tier to its limits from the single source of truth.

    Tier strings reach this module in mixed case: models.Tier uses upper
    ("PRO") while the legacy models.SubscriptionPlan uses lower ("pro"), and
    get_subscription_plan() returns the latter. Normalising here prevents a
    missed lookup from silently downgrading a paying customer to FREE.
    """
    return settings.TIER_LIMITS.get(
        str(tier).upper(), settings.TIER_LIMITS["FREE"]
    )


# ---------------------------------------------------------------------------
class NoiseModelType(str, Enum):
    IDEAL = "ideal"
    DEPOLARIZING = "depolarizing"
    THERMAL = "thermal"


class SimulationMethod(str, Enum):
    """
    Qiskit Aer simulation backends.

    Only STATEVECTOR and DENSITY_MATRIX cost 2**n memory. STABILIZER runs
    Clifford circuits in polynomial time, and MATRIX_PRODUCT_STATE handles
    low-entanglement circuits well beyond the statevector qubit ceiling —
    which is why paid tiers get far more reach than max_qubits alone implies.
    """
    AUTOMATIC = "automatic"
    STATEVECTOR = "statevector"
    DENSITY_MATRIX = "density_matrix"
    STABILIZER = "stabilizer"
    MATRIX_PRODUCT_STATE = "matrix_product_state"
    EXTENDED_STABILIZER = "extended_stabilizer"


# Methods whose memory and time cost grows as 2**num_qubits. The others scale
# polynomially for suitable circuits, so the exponential budget must not be
# applied to them or it would reject exactly what these methods make possible.
EXPONENTIAL_METHODS: frozenset[str] = frozenset({
    "automatic", "statevector", "density_matrix",
})


class ExecutionProviderType(str, Enum):
    SIMULATOR = "simulator"
    IBM_QUANTUM = "ibm_quantum"
    AWS_BRAKET = "aws_braket"


class SimulateRequest(BaseModel):
    """Request body for POST /api/v1/simulate."""

    circuit_qasm: str = Field(
        ...,
        min_length=10,
        description="OpenQASM 2.0 circuit string",
        json_schema_extra={"example": 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncx q[0],q[1];\nmeasure q -> c;'},
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
    simulation_method: SimulationMethod = Field(
        default=SimulationMethod.AUTOMATIC,
        description=(
            "Aer simulation method. statevector (all tiers); density_matrix, "
            "stabilizer, matrix_product_state and extended_stabilizer require "
            "Pro. stabilizer and matrix_product_state scale polynomially, so "
            "they reach far more qubits than statevector for suitable circuits."
        ),
    )
    optimization_level: int = Field(
        default=1,
        ge=0,
        le=3,
        description="Qiskit transpiler optimization level (0-3). Levels above 1 require Pro.",
    )
    backend_provider: ExecutionProviderType = Field(
        default=ExecutionProviderType.SIMULATOR,
        description="Execution provider: simulator, ibm_quantum, or aws_braket",
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
    qpu_telemetry: Optional[dict[str, Any]] = None



class JobStatusResponse(BaseModel):
    """Response for GET /api/v1/simulate/{job_id}."""

    job_id: str
    status: str  # queued | running | complete | failed
    result: Optional[SimulationResult] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------






def _estimate_cost_seconds(
    num_qubits: int,
    shots: int,
    depth: int = 1,
    method: str = "automatic",
) -> float:
    """
    Unclamped wall-clock estimate, used to enforce the execution budget.

    Statevector and density-matrix simulation are exponential in qubit count
    and linear in depth and shots, so one oversized request can occupy a worker
    for minutes. This must NOT be clamped — the point is to recognise a request
    that is far too expensive before any work begins.

    Stabilizer and matrix-product-state are polynomial for the circuits they
    are designed for, so applying the exponential model to them would reject
    precisely the large circuits those methods exist to make feasible.
    """
    base = 0.5
    shot_factor = shots / 1024.0
    depth_factor = max(1, depth) / 20.0

    if method not in EXPONENTIAL_METHODS:
        # Polynomial regime: cost tracks qubits * depth * shots, not 2**n.
        return base + (num_qubits * max(1, depth) * 0.0002) * shot_factor

    qubit_factor = 2 ** max(0, num_qubits - 10) * 0.001
    return base + qubit_factor * shot_factor * depth_factor


def _estimate_execution_seconds(
    num_qubits: int, shots: int, depth: int = 1, method: str = "automatic"
) -> int:
    """
    Clamped estimate handed back to the client purely as a polling hint.
    """
    return max(1, min(int(_estimate_cost_seconds(num_qubits, shots, depth, method)) + 1, 30))


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
        "the simulation job. Returns a job_id for polling."
    ),
)
async def submit_simulation(
    body: SimulateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user_or_api_key),
):
    request_start = time.monotonic()
    job_id = str(uuid.uuid4())

    # Normalize standard QASM include library if legacy .h extension is used
    if "qelib1.h" in body.circuit_qasm:
        body.circuit_qasm = body.circuit_qasm.replace("qelib1.h", "qelib1.inc")

    # --- Resolve subscription tier -------------------------------------------
    tier = await get_subscription_plan(
        db, current_user.id, getattr(current_user, "org_id", None)
    )
    limits = get_tier_limits(tier)

    log.info(
        "simulation.request_received",
        job_id=job_id,
        user_id=current_user.id,
        tier=tier,
        shots=body.shots,
        noise_model=body.noise_model.value,
    )

    # --- 0. Validate: concurrent job limits ----------------------------------
    concurrent_jobs_key = f"user:{current_user.id}:concurrent_jobs"
    current_concurrent_jobs = await redis_client.scard(concurrent_jobs_key)
    max_concurrent = limits.get("max_concurrent_jobs", 1)
    
    if current_concurrent_jobs >= max_concurrent:
        log.warning(
            "simulation.concurrent_jobs_exceeded",
            job_id=job_id,
            user_id=current_user.id,
            tier=tier,
            current_jobs=current_concurrent_jobs,
            max_jobs=max_concurrent,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"You have reached the maximum of {max_concurrent} concurrent simulation jobs "
                f"for the '{tier}' tier. Please wait for them to finish."
            ),
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

    # --- Validate: simulation method entitlement -----------------------------
    allowed_methods = limits.get("simulation_methods", ["automatic", "statevector"])
    if body.simulation_method.value not in allowed_methods:
        log.warning(
            "simulation.method_denied",
            job_id=job_id,
            user_id=current_user.id,
            tier=tier,
            requested_method=body.simulation_method.value,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Simulation method '{body.simulation_method.value}' requires a Pro "
                f"subscription. Your current tier is '{tier}'. "
                f"Available on your plan: {', '.join(allowed_methods)}."
            ),
        )

    # --- Validate: transpiler optimization level -----------------------------
    max_opt = limits.get("max_optimization_level", 1)
    if body.optimization_level > max_opt:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Transpiler optimization level {body.optimization_level} requires a "
                f"Pro subscription. The '{tier}' tier is limited to level {max_opt}."
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
    from services.qasm_validator import validate_qasm_security
    try:
        validate_qasm_security(body.circuit_qasm)
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
    from services.qasm_validator import parse_and_validate_qasm
    try:
        num_qubits, circuit_depth = parse_and_validate_qasm(body.circuit_qasm)
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

    # --- 5.5. Deduct QPU Credits Surcharge ----------------------------------
    if body.backend_provider != ExecutionProviderType.SIMULATOR:
        cost_credits = 1000.0 + 10.0 * body.shots
        from sqlalchemy import select
        res = await db.execute(select(DBmodels.WalletBalance).where(DBmodels.WalletBalance.user_id == current_user.id))
        wallet = res.scalar_one_or_none()
        
        if not wallet or wallet.balance_credits < cost_credits:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient wallet balance. Real QPU execution requires {cost_credits} credits. Current balance: {wallet.balance_credits if wallet else 0.0} credits."
            )
            
        wallet.balance_credits = wallet.balance_credits - cost_credits
        db.add(wallet)
        
        # Log usage event
        usage_event = DBmodels.UsageEvent(
            user_id=current_user.id,
            event_type=DBmodels.UsageEventType.QPU_RUN,
            credits_used=int(cost_credits),
            metadata_={"provider": body.backend_provider.value, "shots": body.shots}
        )
        db.add(usage_event)
        await db.commit()
        log.info(
            "simulation.qpu_credits_deducted",
            job_id=job_id,
            user_id=current_user.id,
            cost_credits=cost_credits,
            remaining_credits=float(wallet.balance_credits),
        )

    # --- 6. Queue the Celery task -------------------------------------------
    # --- Enforce the execution budget before any work is dispatched ---------
    # This guard must live here rather than in the worker: USE_CELERY defaults
    # to False, in which case the job runs via FastAPI BackgroundTasks inside
    # the web process, where Celery's task_soft_time_limit never applies and
    # the SoftTimeLimitExceeded handler in worker.py is unreachable. Rejecting
    # up front is the only cap that holds on both dispatch paths.
    estimated_cost = _estimate_cost_seconds(
        num_qubits, body.shots, circuit_depth, body.simulation_method.value
    )
    max_seconds = settings.SIMULATION_MAX_ESTIMATED_SECONDS

    if estimated_cost > max_seconds:
        log.warning(
            "simulation.cost_budget_exceeded",
            job_id=job_id,
            user_id=current_user.id,
            tier=tier,
            num_qubits=num_qubits,
            circuit_depth=circuit_depth,
            shots=body.shots,
            estimated_cost_seconds=round(estimated_cost, 2),
            max_seconds=max_seconds,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Circuit is too expensive to simulate: estimated "
                f"{estimated_cost:.1f}s exceeds the {max_seconds}s limit. "
                f"Reduce qubits ({num_qubits}), depth ({circuit_depth}), "
                f"or shots ({body.shots})."
            ),
        )

    estimated_seconds = _estimate_execution_seconds(
        num_qubits, body.shots, circuit_depth, body.simulation_method.value
    )

    # Store initial job metadata in Redis (TTL = 1 hour)
    job_meta = {
        "job_id": job_id,
        "status": "queued",
        "user_id": current_user.id,
        "tier": tier,
        "circuit_qasm": body.circuit_qasm,
        "shots": body.shots,
        "noise_model": body.noise_model.value,
        "simulation_method": body.simulation_method.value,
        "optimization_level": body.optimization_level,
        "backend_provider": body.backend_provider.value,
        "num_qubits": num_qubits,
        "circuit_depth": circuit_depth,
        "submitted_at": time.time(),
        "result": None,
        "error": None,
    }
    await redis_client.setex(
        f"sim_job:{job_id}", 3600, json.dumps(job_meta)
    )
    # Track concurrent jobs (they should be removed from this set in worker.py)
    await redis_client.sadd(concurrent_jobs_key, job_id)
    await redis_client.expire(concurrent_jobs_key, 3600)


    # Dispatch either to Celery or use FastAPI BackgroundTasks based on configuration.
    # `settings` comes from the module-level import; re-importing it here would
    # make the name function-local for the whole body and raise UnboundLocalError
    # at the budget check above. The worker import stays local to avoid a cycle.
    from worker import run_simulation

    if settings.USE_CELERY:
        run_simulation.delay(job_id)
        dispatch_method = "celery"
    else:
        background_tasks.add_task(run_simulation, job_id)
        dispatch_method = "background_task"

    elapsed_ms = (time.monotonic() - request_start) * 1000
    log.info(
        "simulation.job_queued",
        job_id=job_id,
        user_id=current_user.id,
        num_qubits=num_qubits,
        circuit_depth=circuit_depth,
        estimated_seconds=estimated_seconds,
        validation_ms=round(elapsed_ms, 2),
        dispatch_method=dispatch_method,
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
        sv = result_raw.get("statevector") if get_tier_limits(tier)["statevector_access"] else None

        result_payload = SimulationResult(
            counts=result_raw["counts"],
            statevector=sv,
            execution_time_ms=result_raw["execution_time_ms"],
            shots=result_raw["shots"],
            circuit_depth=result_raw["circuit_depth"],
            num_qubits=result_raw["num_qubits"],
            qpu_telemetry=result_raw.get("qpu_telemetry"),
        )


    return JobStatusResponse(
        job_id=job_id,
        status=job_data["status"],
        result=result_payload,
        error=job_data.get("error"),
    )
