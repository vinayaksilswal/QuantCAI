from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import logging
import json
from slowapi import Limiter
from slowapi.util import get_remote_address

from core import database as db
import models as DBmodels
from core.auth import get_current_user
from services.quantum import QuantumEngine

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

class QuantumStateRequest(BaseModel):
    current_state: dict
    gate: str

class CircuitRunRequest(BaseModel):
    circuit: list # List of gate objects {name, qubits, params}
    num_qubits: int = 5
    use_noise: bool = False



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
    """Run a full quantum circuit"""
    try:
        result = quantum_engine.run_circuit(body.circuit, body.num_qubits, body.use_noise)
        return result
    except Exception as e:
        logger.error(f"Error running circuit: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


