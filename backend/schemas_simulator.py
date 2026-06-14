from pydantic import BaseModel, Field, field_validator

class QasmExecutionRequest(BaseModel):
    qasm_string: str = Field(
        ...,
        min_length=10,
        description="Raw OpenQASM 3.0 circuit code string"
    )
    shots: int = Field(
        default=1024,
        ge=1,
        le=100000,
        description="Number of simulation shots"
    )
    backend_choice: str = Field(
        default="Local AerSimulator",
        description="Selected simulation backend"
    )
    noise_model: str = Field(
        default="Ideal",
        description="Noise model: Ideal or Depolarizing"
    )

    @field_validator("qasm_string")
    @classmethod
    def validate_openqasm_header(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped.upper().startswith("OPENQASM"):
            raise ValueError("QASM code must begin with an 'OPENQASM' header")
        return v
