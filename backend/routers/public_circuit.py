import time
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.quantum import QuantumEngine, CircuitBuildError, SimulationError
from schemas_circuit import CircuitRunRequest, SimulationResultResponse
from metering_middleware import verify_api_key_and_meter, apply_transaction_charges

logger = logging.getLogger("quantcai.routers.public_circuit")
router = APIRouter(prefix="/api/v1/public/circuit", tags=["Public API Simulation"])

quantum_engine = QuantumEngine()

@router.post(
    "/simulate",
    response_model=SimulationResultResponse,
    summary="Simulate a quantum circuit via public API Key",
    description="Protected simulation endpoint. Charges credits per transaction.",
)
async def simulate_public_circuit(
    request: Request,
    body: CircuitRunRequest,
    api_key_info: dict = Depends(verify_api_key_and_meter),
):
    """
    Public simulation endpoint for API Key developers.
    Validates limits and deducts precise micro-charges on successful completion.
    """
    t_start = time.perf_counter()
    api_key_id = api_key_info["id"]
    user_id = api_key_info["user_id"]

    # Validate qubit bounds across all gates
    for i, gate in enumerate(body.gates):
        for q in gate.qubits:
            if q >= body.num_qubits:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Gate '{gate.name}' (instruction {i}) references qubit {q}, "
                        f"but circuit only has {body.num_qubits} qubits (0–{body.num_qubits - 1})."
                    ),
                )

    try:
        # Run Qiskit simulation synchronously
        result = quantum_engine.run_circuit_v1(
            circuit_data=body.gates,
            num_qubits=body.num_qubits,
            shots=body.shots,
            use_noise=body.use_noise,
        )

        t_elapsed = (time.perf_counter() - t_start) * 1000

        # Successful response: deduct micro-charge
        await apply_transaction_charges(user_id=user_id, api_key_id=api_key_id, shots=body.shots)

        logger.info(
            f"Public simulation completed successfully: User={user_id}, Key={api_key_id}, "
            f"Qubits={body.num_qubits}, Shots={body.shots}, Elapsed={t_elapsed:.1f}ms"
        )

        return result

    except CircuitBuildError as e:
        logger.warning(f"Public simulation circuit build error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except SimulationError as e:
        logger.error(f"Public simulation execution error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected public simulation error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Simulation failed: {str(e)}")
