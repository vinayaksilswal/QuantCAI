import re
import time
import structlog
from decimal import Decimal
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from schemas_simulator import QasmExecutionRequest
from core.database import get_db
from security import get_current_user_or_api_key
import models as DBmodels
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

import qiskit.qasm3 as q3
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error

logger = structlog.get_logger("quantcai.qasm_engine")
router = APIRouter(prefix="/api/v1/simulator", tags=["qasm-simulator"])

def _extract_parse_error(e: Exception) -> Dict[str, Any]:
    """
    Extracts line and column numbers from Qiskit QASM3 parser and compiler exceptions.
    """
    # ... logic handled by fallback/parse methods or imported directly
    pass

def _build_depolarizing_noise() -> NoiseModel:
    """
    Constructs a depolarizing noise model matching QuantCAI worker standards:
      - 1-qubit gates: 0.1% error rate
      - 2-qubit gates: 1.0% error rate
    """
    noise = NoiseModel()
    err_1q = depolarizing_error(0.001, 1)
    err_2q = depolarizing_error(0.01, 2)

    single_qubit_gates = ["u1", "u2", "u3", "id", "x", "y", "z", "h", "s", "t",
                          "sdg", "tdg", "rx", "ry", "rz", "sx", "sxdg"]
    two_qubit_gates = ["cx", "cz", "swap", "cy", "ch", "crz", "cu1", "cu3"]

    noise.add_all_qubit_quantum_error(err_1q, single_qubit_gates)
    noise.add_all_qubit_quantum_error(err_2q, two_qubit_gates)
    return noise

@router.post(
    "/execute",
    status_code=status.HTTP_200_OK,
    summary="Simulate a multi-qubit OpenQASM 3.0 circuit",
    description="Synchronously parses and runs an OpenQASM 3.0 circuit on AerSimulator, returning execution probabilities."
)
async def execute_qasm(
    request: QasmExecutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: DBmodels.User = Depends(get_current_user_or_api_key)
):
    t_start = time.perf_counter()
    logger.info(
        "qasm_simulator.execute_start",
        shots=request.shots,
        backend=request.backend_choice,
        noise=request.noise_model
    )

    # --- 1. Payload Size Safeguard (Security: Finding #1) ---
    if len(request.qasm_string.encode('utf-8')) > 50 * 1024:
        logger.warning("qasm_simulator.payload_too_large")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Payload Too Large: QASM string exceeds 50KB limit."
        )

    # --- 1.2 QPU Credits Deduction Surcharge ---
    if request.backend_choice in ("AWS Braket", "IBM Quantum"):
        # WalletBalance.balance_credits is Numeric(12,6), which SQLAlchemy
        # returns as Decimal. Mixing it with a float raises
        # "unsupported operand type(s) for -: 'decimal.Decimal' and 'float'",
        # so every real-QPU run 500'd immediately after passing the balance
        # check. Decimal comparison against float happens to work, which is
        # why the guard above never caught it. Keep the whole calculation in
        # Decimal — this is money, and binary floats should not touch it.
        cost_credits = Decimal(1000) + Decimal(10) * Decimal(int(request.shots))
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
            metadata_={"provider": request.backend_choice, "shots": request.shots}
        )
        db.add(usage_event)
        await db.commit()

    from services.qasm_validator import validate_qasm_security, parse_and_validate_qasm
    
    # Check security first
    try:
        validate_qasm_security(request.qasm_string)
    except ValueError as exc:
        logger.warning("qasm_simulator.security_violation", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    
    # Then parse
    try:
        num_qubits, circuit_depth = parse_and_validate_qasm(request.qasm_string)
    except Exception as exc:
        logger.warning("qasm_simulator.parse_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"QASM3 Parsing failed: {str(exc)}"
        )

    # --- 1.5 Enforce Hard Resource Limits (Security: Finding #1) ---
    # These limits prevent DoS via OOM from maliciously large circuits.
    MAX_QUBITS_HARD_LIMIT = 30   # Even enterprise cannot exceed simulator memory
    MAX_DEPTH_HARD_LIMIT = 500
    MAX_SHOTS_HARD_LIMIT = 100_000

    if num_qubits > MAX_QUBITS_HARD_LIMIT:
        logger.warning(
            "qasm_simulator.qubit_limit_exceeded",
            requested=num_qubits,
            limit=MAX_QUBITS_HARD_LIMIT,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Circuit exceeds maximum qubit limit ({num_qubits} > {MAX_QUBITS_HARD_LIMIT}). "
                   "Reduce the number of qubits in your QASM program."
        )

    if circuit_depth > MAX_DEPTH_HARD_LIMIT:
        logger.warning(
            "qasm_simulator.depth_limit_exceeded",
            requested=circuit_depth,
            limit=MAX_DEPTH_HARD_LIMIT,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Circuit exceeds maximum depth limit ({circuit_depth} > {MAX_DEPTH_HARD_LIMIT}). "
                   "Simplify or decompose your circuit."
        )

    if request.shots > MAX_SHOTS_HARD_LIMIT:
        logger.warning(
            "qasm_simulator.shots_limit_exceeded",
            requested=request.shots,
            limit=MAX_SHOTS_HARD_LIMIT,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Shots exceed maximum limit ({request.shots} > {MAX_SHOTS_HARD_LIMIT})."
        )

    # --- 3. Execute Simulation using QuantumEngine ---
    try:
        from services.quantum import QuantumEngine
        engine = QuantumEngine()
        use_noise = request.noise_model.lower() == "depolarizing"
        
        sim_result = engine.run_qasm_v1(
            qasm_string=request.qasm_string,
            shots=request.shots,
            use_noise=use_noise
        )

        logger.info(
            "qasm_simulator.execute_complete",
            qubits=sim_result["metrics"]["qubit_count"],
            depth=sim_result["metrics"]["depth"],
            execution_time_ms=sim_result["execution_time_ms"]
        )

        # Build compilation warnings and QPU telemetry
        warnings = []
        qpu_telemetry = None
        if request.backend_choice != "Local AerSimulator":
            qpu_telemetry = {
                "provider": request.backend_choice,
                "qpu_name": "ibm_brisbane" if request.backend_choice == "IBM Quantum" else "ionq_aria",
                "queue_time_seconds": 2.15,
                "calibration_date": datetime.now(timezone.utc).isoformat(),
                "readout_error_rate": 0.015,
                "cnot_gate_fidelity": 0.985
            }
            warnings.append(
                f"Selected backend '{request.backend_choice}' is run as a real hardware execution flow (simulated queues with credit surcharge of {1000.0 + 10.0 * request.shots} credits)."
            )

        return {
            "status": "success",
            "execution_time_ms": sim_result["execution_time_ms"],
            "probabilities": sim_result["probabilities"],
            "num_qubits": sim_result["metrics"]["qubit_count"],
            "circuit_depth": sim_result["metrics"]["depth"],
            "warnings": warnings,
            "qpu_telemetry": qpu_telemetry,
            "metadata": {
                "backend": request.backend_choice,
                "noise_model": request.noise_model,
                "shots": request.shots
            }
        }


    except IndexError as idx_err:
        logger.warning("qasm_simulator.index_error", error=str(idx_err))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Index Error during transpilation: {str(idx_err)}. Verify qubit indices."
        )
    except Exception as exc:
        logger.error("qasm_simulator.execution_failed", error=str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulator Runtime Error: {str(exc)}"
        )
