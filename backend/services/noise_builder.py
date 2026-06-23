"""
QuantCAI Enterprise — Advanced Noise Model Builder
====================================================
Constructs Qiskit Aer NoiseModel instances calibrated to specific
hardware backend profiles. Supports:
  - Thermal relaxation (T1/T2 decoherence)
  - Depolarizing errors
  - Readout (SPAM) errors
  - Composite models combining all error sources
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional

logger = logging.getLogger("quantcai.noise_builder")


def build_noise_model(
    backend_id: str,
    custom_t1: Optional[float] = None,
    custom_t2: Optional[float] = None,
    custom_gate_time: Optional[float] = None,
) -> Any:
    """
    Build a comprehensive NoiseModel for the given backend.

    Uses the backend's calibration data (T1, T2, gate times, readout errors)
    to construct a realistic noise model. Custom overrides are supported.

    Args:
        backend_id: One of the registered backend IDs
        custom_t1: Override T1 in microseconds
        custom_t2: Override T2 in microseconds
        custom_gate_time: Override gate time in nanoseconds

    Returns:
        qiskit_aer.noise.NoiseModel instance
    """
    from qiskit_aer.noise import NoiseModel, thermal_relaxation_error, depolarizing_error, ReadoutError
    from services.backend_configs import get_backend_config

    cfg = get_backend_config(backend_id)

    # Simulators don't have noise
    if cfg.get("technology") in ("GPU Simulator", "CPU Simulator"):
        logger.info(f"Backend '{backend_id}' is a simulator — returning None noise model")
        return None

    noise = NoiseModel()

    # -----------------------------------------------------------------------
    # Thermal Relaxation Parameters
    # -----------------------------------------------------------------------
    t1_us = custom_t1 or cfg.get("t1_us", 100.0)
    t2_us = custom_t2 or cfg.get("t2_us", 80.0)

    # Enforce physical constraint: T2 <= 2*T1
    if t2_us > 2 * t1_us:
        t2_us = 2 * t1_us
        logger.warning(
            f"T2 ({t2_us}µs) exceeds 2*T1 ({2*t1_us}µs), clamped to physical limit"
        )

    # Convert to nanoseconds for consistency with gate times
    t1_ns = t1_us * 1000
    t2_ns = t2_us * 1000

    # -----------------------------------------------------------------------
    # Single-qubit gate thermal relaxation
    # -----------------------------------------------------------------------
    gate_time_1q_ns = custom_gate_time or cfg.get(
        "gate_time_sx_ns",
        cfg.get("gate_time_1q_us", 0.01) * 1000  # Convert µs → ns
    )

    if gate_time_1q_ns > 0 and t1_ns > 0:
        err_1q = thermal_relaxation_error(t1_ns, t2_ns, gate_time_1q_ns)
        single_gates = ["u1", "u2", "u3", "id", "x", "y", "z", "h", "s", "t",
                        "sdg", "tdg", "rx", "ry", "rz", "sx", "sxdg"]
        noise.add_all_qubit_quantum_error(err_1q, single_gates)

        logger.info(
            f"Added 1Q thermal relaxation: T1={t1_us}µs, T2={t2_us}µs, "
            f"gate_time={gate_time_1q_ns}ns"
        )

    # -----------------------------------------------------------------------
    # Two-qubit gate thermal relaxation
    # -----------------------------------------------------------------------
    gate_time_2q_ns = cfg.get(
        "gate_time_cx_ns",
        cfg.get("gate_time_2q_us", 0.6) * 1000
    )

    if gate_time_2q_ns > 0 and t1_ns > 0:
        err_2q_single = thermal_relaxation_error(t1_ns, t2_ns, gate_time_2q_ns)
        err_2q = err_2q_single.tensor(err_2q_single)
        two_qubit_gates = ["cx", "cz", "swap", "cy", "ch", "crz"]
        noise.add_all_qubit_quantum_error(err_2q, two_qubit_gates)

        logger.info(
            f"Added 2Q thermal relaxation: gate_time={gate_time_2q_ns}ns"
        )

    # -----------------------------------------------------------------------
    # Depolarizing errors (additive to thermal)
    # -----------------------------------------------------------------------
    sx_error = cfg.get("sx_error", cfg.get("single_qubit_error", 0.0003))
    cx_error = cfg.get("cx_error", cfg.get("two_qubit_error", 0.01))

    if sx_error > 0:
        dep_1q = depolarizing_error(sx_error, 1)
        noise.add_all_qubit_quantum_error(
            dep_1q, ["x", "y", "z", "h", "s", "t", "rx", "ry", "rz", "sx"]
        )

    if cx_error > 0:
        dep_2q = depolarizing_error(cx_error, 2)
        noise.add_all_qubit_quantum_error(dep_2q, ["cx", "cz", "swap"])

    # -----------------------------------------------------------------------
    # Readout (SPAM) errors
    # -----------------------------------------------------------------------
    readout_err_rate = cfg.get("readout_error", 0.02)
    n_qubits = cfg.get("qubits", 127)

    if readout_err_rate > 0:
        # Asymmetric readout error: P(1|0) and P(0|1)
        p_meas_0_given_1 = readout_err_rate       # Probability of reading 0 when state is 1
        p_meas_1_given_0 = readout_err_rate * 0.8  # Slightly lower false positive

        readout_error = ReadoutError([
            [1 - p_meas_1_given_0, p_meas_1_given_0],
            [p_meas_0_given_1, 1 - p_meas_0_given_1],
        ])

        # Add readout error to reasonable number of qubits for simulation
        for qubit in range(min(n_qubits, 32)):
            noise.add_readout_error(readout_error, [qubit])

        logger.info(
            f"Added readout error: P(1|0)={p_meas_1_given_0:.4f}, "
            f"P(0|1)={p_meas_0_given_1:.4f} for {min(n_qubits, 32)} qubits"
        )

    logger.info(f"Noise model built for backend '{backend_id}'")
    return noise


def build_simple_depolarizing_noise(
    error_1q: float = 0.001,
    error_2q: float = 0.01,
) -> Any:
    """
    Build a simple depolarizing noise model (legacy compatibility).
    """
    from qiskit_aer.noise import NoiseModel, depolarizing_error

    noise = NoiseModel()
    err_1q = depolarizing_error(error_1q, 1)
    err_2q = depolarizing_error(error_2q, 2)

    single_gates = ["u1", "u2", "u3", "id", "x", "y", "z", "h", "s", "t",
                    "sdg", "tdg", "rx", "ry", "rz", "sx", "sxdg"]
    two_qubit_gates = ["cx", "cz", "swap", "cy", "ch"]

    noise.add_all_qubit_quantum_error(err_1q, single_gates)
    noise.add_all_qubit_quantum_error(err_2q, two_qubit_gates)

    return noise


def build_thermal_noise(
    t1_us: float = 50.0,
    t2_us: float = 70.0,
    gate_time_1q_ns: float = 50.0,
    gate_time_2q_ns: float = 300.0,
    num_qubits: int = 5,
) -> Any:
    """
    Build a thermal relaxation noise model (legacy compatibility).
    """
    from qiskit_aer.noise import NoiseModel, thermal_relaxation_error

    noise = NoiseModel()
    t1_ns = t1_us * 1000
    t2_ns = t2_us * 1000

    # Enforce T2 <= 2*T1
    if t2_ns > 2 * t1_ns:
        t2_ns = 2 * t1_ns

    err_1q = thermal_relaxation_error(t1_ns, t2_ns, gate_time_1q_ns)
    single_gates = ["u1", "u2", "u3", "id", "x", "y", "z", "h", "s", "t",
                    "sdg", "tdg", "rx", "ry", "rz", "sx", "sxdg"]
    noise.add_all_qubit_quantum_error(err_1q, single_gates)

    err_2q_single = thermal_relaxation_error(t1_ns, t2_ns, gate_time_2q_ns)
    err_2q = err_2q_single.tensor(err_2q_single)
    noise.add_all_qubit_quantum_error(err_2q, ["cx", "cz", "swap"])

    return noise


def calculate_decoherence_probabilities(
    t1_us: float, t2_us: float, gate_time_ns: float
) -> dict[str, float]:
    """
    Calculate thermal relaxation probabilities for a given gate.

    Returns:
        p1: probability of energy decay  (1 - exp(-t_g / T1))
        p2: probability of dephasing     (1 - exp(-t_g / T2))
    """
    t1_ns = t1_us * 1000
    t2_ns = t2_us * 1000

    p1 = 1.0 - math.exp(-gate_time_ns / t1_ns) if t1_ns > 0 else 0.0
    p2 = 1.0 - math.exp(-gate_time_ns / t2_ns) if t2_ns > 0 else 0.0

    return {"p1": p1, "p2": p2, "t1_us": t1_us, "t2_us": t2_us, "gate_time_ns": gate_time_ns}
