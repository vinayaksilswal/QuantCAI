"""
QuantCAI — Circuit Builder Router (V1 Enterprise)
===================================================
Provides both legacy endpoints and new V1 enterprise endpoints
for circuit simulation and OpenQASM 3.0 export.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import logging
import json
import time
from slowapi import Limiter
from slowapi.util import get_remote_address

from core import database as db
import models as DBmodels
from core.auth import get_current_user
from services.quantum import QuantumEngine, CircuitBuildError, SimulationError
from schemas_circuit import (
    CircuitRunRequest as V1CircuitRunRequest,
    CircuitExportRequest,
    SimulationResultResponse,
    ExportResponse,
)

router = APIRouter(prefix="/api", tags=["circuit"])
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

quantum_engine = QuantumEngine()

def get_db():
    ses = db.SessionLocal()
    try:
        yield ses
    finally:
        ses.close()


# ---------------------------------------------------------------------------
# Legacy Schemas (kept for backward compatibility)
# ---------------------------------------------------------------------------
class QuantumStateRequest(BaseModel):
    current_state: dict
    gate: str

class CircuitRunRequest(BaseModel):
    circuit: list # List of gate objects {name, qubits, params}
    num_qubits: int = 5
    use_noise: bool = False


# ---------------------------------------------------------------------------
# Legacy Endpoints (backward compatible)
# ---------------------------------------------------------------------------
@router.post("/quantum/state/apply")
@limiter.limit("20/minute")
def apply_quantum_gate(request: Request, body: QuantumStateRequest, current_user: DBmodels.User = Depends(get_current_user)):
    """Calculate next quantum state given current state and a gate"""
    try:
        new_state = quantum_engine.calculate_next_state(body.current_state, body.gate)
        return new_state
    except Exception as e:
        logger.error(f"Error applying gate: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/circuit/run")
@limiter.limit("10/minute")
def run_circuit(request: Request, body: CircuitRunRequest, current_user: DBmodels.User = Depends(get_current_user)):
    """Run a full quantum circuit (legacy endpoint)"""
    try:
        result = quantum_engine.run_circuit(body.circuit, body.num_qubits, body.use_noise)
        return result
    except Exception as e:
        logger.error(f"Error running circuit: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# V1 Enterprise Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/v1/circuit/simulate",
    response_model=SimulationResultResponse,
    summary="Simulate a quantum circuit (V1)",
    description=(
        "Accepts a JSON payload of gate instructions, builds a Qiskit circuit, "
        "and executes it on AerSimulator. Returns probability distribution, "
        "optional statevector, and circuit metrics."
    ),
)
@limiter.limit("15/minute")
def simulate_circuit_v1(
    request: Request,
    body: V1CircuitRunRequest,
    current_user: DBmodels.User = Depends(get_current_user),
):
    """
    V1 Enterprise circuit simulation endpoint.
    Supports configurable shots, noise models, and returns structured results.
    """
    t_start = time.perf_counter()

    # Validate qubit bounds across all gates
    for i, gate in enumerate(body.gates):
        for q in gate.qubits:
            if q >= body.num_qubits:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Gate '{gate.name}' (instruction {i}) references qubit {q}, "
                        f"but circuit only has {body.num_qubits} qubits (0–{body.num_qubits - 1})."
                    ),
                )

    try:
        result = quantum_engine.run_circuit_v1(
            circuit_data=body.gates,
            num_qubits=body.num_qubits,
            shots=body.shots,
            use_noise=body.use_noise,
        )

        t_elapsed = (time.perf_counter() - t_start) * 1000
        logger.info(
            f"V1 simulation completed: {body.num_qubits} qubits, "
            f"{len(body.gates)} gates, {body.shots} shots, "
            f"{t_elapsed:.1f}ms total"
        )

        return result

    except CircuitBuildError as e:
        logger.warning(f"Circuit build error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except SimulationError as e:
        logger.error(f"Simulation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected simulation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.post(
    "/v1/circuit/export",
    response_model=ExportResponse,
    summary="Export circuit as OpenQASM 3.0",
    description=(
        "Translates a JSON gate instruction payload into a raw OpenQASM 3.0 string. "
        "Supports all standard single-qubit, phase, parameterized, and multi-qubit gates."
    ),
)
@limiter.limit("30/minute")
def export_circuit_v1(
    request: Request,
    body: CircuitExportRequest,
    current_user: DBmodels.User = Depends(get_current_user),
):
    """
    V1 Enterprise QASM export endpoint.
    Returns a standards-compliant OpenQASM 3.0 string.
    """
    # Validate qubit bounds
    for i, gate in enumerate(body.gates):
        for q in gate.qubits:
            if q >= body.num_qubits:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Gate '{gate.name}' (instruction {i}) references qubit {q}, "
                        f"but circuit only has {body.num_qubits} qubits (0–{body.num_qubits - 1})."
                    ),
                )

    try:
        qasm_str = quantum_engine.export_qasm3(
            circuit_data=body.gates,
            num_qubits=body.num_qubits,
        )

        return ExportResponse(
            qasm=qasm_str,
            version="3.0",
            num_qubits=body.num_qubits,
            num_gates=len(body.gates),
        )

    except CircuitBuildError as e:
        logger.warning(f"Export build error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Export error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ---------------------------------------------------------------------------
# Phase 4 Sharing & Viral Loop Endpoints
# ---------------------------------------------------------------------------
import secrets

class CircuitCreateRequest(BaseModel):
    name: str
    circuit_data: str
    is_interactive: bool = False

@router.post("/v1/circuits")
@limiter.limit("15/minute")
def save_circuit(
    request: Request,
    body: CircuitCreateRequest,
    current_user: DBmodels.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Persist a circuit configuration to the database.
    """
    circuit = DBmodels.Circuit(
        user_id=current_user.id,
        name=body.name,
        circuit_data=body.circuit_data,
        is_interactive=body.is_interactive
    )
    db.add(circuit)
    db.commit()
    db.refresh(circuit)
    
    return {
        "status": "success",
        "id": circuit.id,
        "name": circuit.name,
        "circuit_data": circuit.circuit_data,
        "is_public": circuit.is_public,
        "share_slug": circuit.share_slug
    }

@router.post("/v1/circuits/{circuit_id}/share")
@limiter.limit("10/minute")
def share_circuit(
    request: Request,
    circuit_id: int,
    current_user: DBmodels.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Expose a circuit publicly by generating a secure sharing slug.
    """
    circuit = db.query(DBmodels.Circuit).filter(DBmodels.Circuit.id == circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")
        
    if circuit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to share this circuit")
        
    if not circuit.share_slug:
        # Generate clean, URL-safe unique token
        circuit.share_slug = secrets.token_urlsafe(12)
        
    circuit.is_public = True
    db.commit()
    
    return {
        "status": "success",
        "share_slug": circuit.share_slug,
        "is_public": circuit.is_public
    }


@router.post("/v1/circuits/{circuit_id}/unshare")
@limiter.limit("10/minute")
def unshare_circuit(
    request: Request,
    circuit_id: int,
    current_user: DBmodels.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke public access to a circuit.
    """
    circuit = db.query(DBmodels.Circuit).filter(DBmodels.Circuit.id == circuit_id).first()
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuit not found")
        
    if circuit.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this circuit")
        
    circuit.is_public = False
    db.commit()
    
    return {
        "status": "success",
        "is_public": circuit.is_public
    }


@router.get("/v1/public/circuits/{share_slug}")
@limiter.limit("30/minute")
def get_public_circuit(
    request: Request,
    share_slug: str,
    db: Session = Depends(get_db)
):
    """
    Public unauthenticated endpoint to fetch shared circuit configuration.
    """
    circuit = db.query(DBmodels.Circuit).filter(
        DBmodels.Circuit.share_slug == share_slug,
        DBmodels.Circuit.is_public == True
    ).first()
    
    if not circuit:
        raise HTTPException(status_code=404, detail="Public shared circuit not found or access revoked")
        
    return {
        "id": circuit.id,
        "name": circuit.name or "Untitled Circuit",
        "circuit_data": circuit.circuit_data,
        "is_interactive": circuit.is_interactive,
        "created_at": circuit.created_at,
        "author_name": circuit.user.name if circuit.user else "QuantCAI Innovator"
    }

