"""
QuantCAI — Circuit Builder V1 Schemas
======================================
Pydantic models for the enterprise-grade circuit builder API.
Supports multi-qubit gate instructions with parameter validation.
"""

from __future__ import annotations

from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator


class GateInstruction(BaseModel):
    """A single quantum gate instruction."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Gate name (e.g., 'h', 'x', 'cx', 'ccx', 'rx')",
    )
    qubits: list[int] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="Qubit indices this gate acts on. "
                    "For single-qubit: [target]. "
                    "For CX: [control, target]. "
                    "For CCX: [control1, control2, target].",
    )
    params: list[float] = Field(
        default_factory=list,
        max_length=3,
        description="Rotation parameters in radians (for Rx, Ry, Rz).",
    )

    @field_validator("name")
    @classmethod
    def normalize_gate_name(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("qubits")
    @classmethod
    def validate_qubit_indices(cls, v: list[int]) -> list[int]:
        for idx in v:
            if idx < 0:
                raise ValueError(f"Qubit index must be non-negative, got {idx}")
        if len(v) != len(set(v)):
            raise ValueError(f"Duplicate qubit indices are not allowed: {v}")
        return v


class CircuitRunRequest(BaseModel):
    """Request body for POST /api/v1/circuit/simulate."""

    num_qubits: int = Field(
        default=5,
        ge=1,
        le=29,
        description="Number of qubits in the circuit (1–29).",
    )
    shots: int = Field(
        default=1024,
        ge=1,
        le=100000,
        description="Number of measurement shots.",
    )
    gates: list[GateInstruction] = Field(
        ...,
        min_length=0,
        description="Ordered list of gate instructions.",
    )
    use_noise: bool = Field(
        default=False,
        description="Enable depolarizing noise model.",
    )

    @field_validator("gates")
    @classmethod
    def validate_gate_qubit_bounds(cls, v: list[GateInstruction], info) -> list[GateInstruction]:
        # Note: num_qubits may not be available here during individual field validation,
        # so we do cross-field validation in the router layer.
        return v


class CircuitExportRequest(BaseModel):
    """Request body for POST /api/v1/circuit/export."""

    num_qubits: int = Field(
        default=5,
        ge=1,
        le=29,
        description="Number of qubits in the circuit.",
    )
    gates: list[GateInstruction] = Field(
        ...,
        min_length=0,
        description="Ordered list of gate instructions.",
    )


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class CircuitMetrics(BaseModel):
    """Metrics about the compiled circuit."""

    depth: int
    gate_count: dict[str, int]
    qubit_count: int


class StatevectorEntry(BaseModel):
    """A single non-zero entry in the statevector."""

    basis: str
    amplitude: dict[str, float]  # {"real": ..., "imag": ...}
    probability: float
    phase: float


class SimulationResultResponse(BaseModel):
    """Response for POST /api/v1/circuit/simulate."""

    type: str  # "ideal" or "noisy"
    probabilities: dict[str, float]
    statevector: Optional[list[StatevectorEntry]] = None
    metrics: CircuitMetrics
    execution_time_ms: Optional[float] = None


class ExportResponse(BaseModel):
    """Response for POST /api/v1/circuit/export."""

    qasm: str
    version: str = "3.0"
    num_qubits: int
    num_gates: int
