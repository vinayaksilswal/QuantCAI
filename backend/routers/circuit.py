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

class CircuitSaveRequest(BaseModel):
    name: str
    circuit_data: list
    is_interactive: bool = False

class CircuitResponse(BaseModel):
    id: int
    name: str
    circuit_data: list
    created_at: str
    
    class Config:
        from_attributes = True

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

@router.post("/circuit/save")
@limiter.limit("30/minute")
def save_circuit(request: Request, body: CircuitSaveRequest, db: Session = Depends(get_db), current_user: DBmodels.User = Depends(get_current_user)):
    """Save a circuit to history"""
    try:
        circuit_json = json.dumps(body.circuit_data)
        new_circuit = DBmodels.Circuit(
            user_id=current_user.id,
            name=body.name,
            circuit_data=circuit_json,
            is_interactive=body.is_interactive
        )
        db.add(new_circuit)
        db.commit()
        db.refresh(new_circuit)
        logger.info(f"Circuit saved: {new_circuit.id} for user {current_user.email}")
        return {"id": new_circuit.id, "message": "Circuit saved successfully"}
    except Exception as e:
        logger.error(f"Error saving circuit: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/circuit/history", response_model=List[CircuitResponse])
def get_circuit_history(limit: int = 10, db: Session = Depends(get_db), current_user: DBmodels.User = Depends(get_current_user)):
    """Get user's circuit history"""
    try:
        circuits = db.query(DBmodels.Circuit)\
            .filter(DBmodels.Circuit.user_id == current_user.id)\
            .order_by(DBmodels.Circuit.created_at.desc())\
            .limit(limit)\
            .all()
        
        result = []
        for c in circuits:
            c_dict = {
                "id": c.id,
                "name": c.name,
                "created_at": c.created_at.isoformat(),
                "circuit_data": json.loads(c.circuit_data)
            }
            result.append(c_dict)
        return result
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
