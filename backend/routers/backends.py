"""
QuantCAI Enterprise — Backend & Hardware API Router
=====================================================
Exposes hardware backend information, coupling maps, cost estimation,
and transpilation endpoints for the enterprise frontend.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from security import get_current_user_or_api_key
import models as DBmodels

logger = logging.getLogger("quantcai.routers.backends")

router = APIRouter(prefix="/api/v1", tags=["enterprise-backends"])


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------
class BackendSummary(BaseModel):
    id: str
    name: str
    provider: str
    technology: str
    qubits: int
    topology: str
    basis_gates: list[str]
    pricing_model: str
    status: str
    queue_length: int = 0


class CouplingMapNode(BaseModel):
    id: int
    t1: Optional[float] = None
    t2: Optional[float] = None
    readoutError: float = 0.0


class CouplingMapEdge(BaseModel):
    source: int
    target: int
    cxError: float = 0.01
    cxTime: float = 500


class CouplingMapResponse(BaseModel):
    nodes: list[CouplingMapNode]
    edges: list[CouplingMapEdge]
    topology: str
    totalQubits: int


class CostEstimateRequest(BaseModel):
    backend: str = Field(..., description="Backend ID")
    shots: int = Field(default=1024, ge=1)
    circuit_depth: int = Field(default=1, ge=1)
    gate_count: int = Field(default=1, ge=1)
    optimization_level: int = Field(default=1, ge=0, le=3)
    error_mitigation: dict = Field(default_factory=dict)


class CostEstimateResponse(BaseModel):
    estimatedCost: float
    breakdown: dict
    warning: Optional[str] = None
    optimizationTip: Optional[str] = None
    effectiveShots: int
    pricingModel: str
    backendId: str


class TranspileRequest(BaseModel):
    circuit_qasm: str = Field(..., min_length=10, description="OpenQASM circuit source")
    backend: str = Field(..., description="Target backend ID")
    optimization_level: int = Field(default=1, ge=0, le=3)


class TranspileResponse(BaseModel):
    original_depth: int
    original_gates: int
    transpiled_depth: int
    transpiled_gates: int
    added_swaps: int
    depth_increase: int
    gate_increase: int
    basis_gates_used: list[str]
    optimization_level: int
    transpile_time_ms: float
    transpiled_qasm: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/backends",
    response_model=list[BackendSummary],
    summary="List available quantum backends",
    description="Returns all registered quantum hardware and simulator backends.",
)
async def list_available_backends(
    current_user: DBmodels.User = Depends(get_current_user_or_api_key),
):
    from services.backend_configs import list_backends
    backends = list_backends()
    return [BackendSummary(**b) for b in backends]


@router.get(
    "/backends/{backend_id}/coupling-map",
    response_model=CouplingMapResponse,
    summary="Get coupling map for hardware visualization",
    description="Returns nodes (qubits) and edges (connections) for D3.js visualization.",
)
async def get_coupling_map(
    backend_id: str,
    current_user: DBmodels.User = Depends(get_current_user_or_api_key),
):
    from services.backend_configs import get_coupling_map_data

    try:
        data = get_coupling_map_data(backend_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return CouplingMapResponse(
        nodes=[CouplingMapNode(**n) for n in data["nodes"]],
        edges=[CouplingMapEdge(**e) for e in data["edges"]],
        topology=data["topology"],
        totalQubits=data["totalQubits"],
    )


@router.get(
    "/backends/{backend_id}",
    summary="Get full backend configuration",
    description="Returns detailed backend specifications including noise params.",
)
async def get_backend_details(
    backend_id: str,
    current_user: DBmodels.User = Depends(get_current_user_or_api_key),
):
    from services.backend_configs import get_backend_config

    try:
        config = get_backend_config(backend_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Remove coupling map from full response (too large)
    response = {k: v for k, v in config.items() if k != "coupling_map"}
    response["has_coupling_map"] = config.get("coupling_map") is not None
    return response


@router.post(
    "/estimate-cost",
    response_model=CostEstimateResponse,
    summary="Estimate execution cost",
    description="Pre-execution cost estimation based on backend, shots, and circuit complexity.",
)
async def estimate_execution_cost(
    body: CostEstimateRequest,
    current_user: DBmodels.User = Depends(get_current_user_or_api_key),
):
    from services.cost_estimator import estimate_cost

    try:
        result = estimate_cost(
            backend_id=body.backend,
            shots=body.shots,
            circuit_depth=body.circuit_depth,
            gate_count=body.gate_count,
            error_mitigation=body.error_mitigation,
            optimization_level=body.optimization_level,
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return CostEstimateResponse(**result)


@router.post(
    "/transpile",
    response_model=TranspileResponse,
    summary="Transpile circuit for target backend",
    description="Hardware-aware circuit transpilation with coupling map constraints.",
)
async def transpile_circuit(
    body: TranspileRequest,
    current_user: DBmodels.User = Depends(get_current_user_or_api_key),
):
    from qiskit import QuantumCircuit
    from services.transpiler import transpile_circuit as do_transpile

    # Parse QASM
    try:
        qc = QuantumCircuit.from_qasm_str(body.circuit_qasm)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse QASM: {e}"
        )

    # Transpile
    try:
        result = do_transpile(qc, body.backend, body.optimization_level)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transpilation error: {e}")

    # Export transpiled circuit to QASM
    transpiled_qasm = None
    try:
        transpiled_qasm = result["transpiled_circuit"].qasm()
    except Exception:
        pass  # Some circuits can't be exported back to QASM 2.0

    return TranspileResponse(
        original_depth=result["original_depth"],
        original_gates=result["original_gates"],
        transpiled_depth=result["transpiled_depth"],
        transpiled_gates=result["transpiled_gates"],
        added_swaps=result["added_swaps"],
        depth_increase=result["depth_increase"],
        gate_increase=result["gate_increase"],
        basis_gates_used=result["basis_gates_used"],
        optimization_level=result["optimization_level"],
        transpile_time_ms=result["transpile_time_ms"],
        transpiled_qasm=transpiled_qasm,
    )
