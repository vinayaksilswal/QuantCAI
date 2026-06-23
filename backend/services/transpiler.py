"""
QuantCAI Enterprise — Hardware-Aware Transpiler Service
========================================================
Wraps Qiskit's transpiler to provide hardware-aware circuit compilation
with coupling map constraints, basis gate decomposition, and SWAP routing.
Reports transpilation overhead metrics for the UI.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

logger = logging.getLogger("quantcai.transpiler")


def transpile_circuit(
    circuit: Any,
    backend_id: str,
    optimization_level: int = 1,
) -> dict[str, Any]:
    """
    Transpile a QuantumCircuit to the target backend's constraints.

    Args:
        circuit: Qiskit QuantumCircuit object
        backend_id: Target backend ID
        optimization_level: 0 (no optimization) to 3 (heavy optimization)

    Returns:
        {
            "transpiled_circuit": QuantumCircuit,
            "original_depth": int,
            "original_gates": int,
            "transpiled_depth": int,
            "transpiled_gates": int,
            "added_swaps": int,
            "basis_gates_used": list[str],
            "optimization_level": int,
            "transpile_time_ms": float,
        }
    """
    from qiskit import transpile
    from qiskit.transpiler import CouplingMap
    from services.backend_configs import get_backend_config

    cfg = get_backend_config(backend_id)

    # Record original circuit metrics
    original_depth = circuit.depth()
    original_ops = dict(circuit.count_ops())
    original_gate_count = sum(original_ops.values())

    # Build coupling map
    coupling_map = None
    raw_coupling = cfg.get("coupling_map")
    if raw_coupling and raw_coupling not in ("all_to_all", "programmable"):
        coupling_map = CouplingMap(raw_coupling)
    elif raw_coupling == "all_to_all":
        # For all-to-all backends, limit coupling map to circuit qubit count
        n = circuit.num_qubits
        edges = []
        for i in range(n):
            for j in range(i + 1, n):
                edges.append([i, j])
        if edges:
            coupling_map = CouplingMap(edges)

    # Get basis gates
    basis_gates = cfg.get("basis_gates")

    # Clamp optimization level
    optimization_level = max(0, min(3, optimization_level))

    # Transpile
    t_start = time.perf_counter()
    try:
        transpiled = transpile(
            circuit,
            coupling_map=coupling_map,
            basis_gates=basis_gates,
            optimization_level=optimization_level,
        )
    except Exception as e:
        logger.error(f"Transpilation failed for backend '{backend_id}': {e}")
        # Fallback: transpile without coupling constraints
        transpiled = transpile(
            circuit,
            basis_gates=basis_gates,
            optimization_level=optimization_level,
        )
    t_ms = (time.perf_counter() - t_start) * 1000

    # Compute transpiled metrics
    transpiled_depth = transpiled.depth()
    transpiled_ops = dict(transpiled.count_ops())
    transpiled_gate_count = sum(transpiled_ops.values())

    # Count SWAP gates inserted
    added_swaps = transpiled_ops.get("swap", 0)
    # SWAPs are often decomposed into 3 CX gates, count those too
    if "swap" not in transpiled_ops and coupling_map is not None:
        # Estimate SWAPs from excess CX gates
        original_cx = original_ops.get("cx", 0) + original_ops.get("cnot", 0)
        transpiled_cx = transpiled_ops.get("cx", 0)
        # Each SWAP = 3 CX, so excess CX / 3 ≈ added SWAPs
        estimated_swap_cx = max(0, transpiled_cx - original_cx)
        added_swaps = estimated_swap_cx // 3

    result = {
        "transpiled_circuit": transpiled,
        "original_depth": original_depth,
        "original_gates": original_gate_count,
        "original_ops": original_ops,
        "transpiled_depth": transpiled_depth,
        "transpiled_gates": transpiled_gate_count,
        "transpiled_ops": transpiled_ops,
        "added_swaps": added_swaps,
        "depth_increase": transpiled_depth - original_depth,
        "gate_increase": transpiled_gate_count - original_gate_count,
        "basis_gates_used": list(transpiled_ops.keys()),
        "optimization_level": optimization_level,
        "transpile_time_ms": round(t_ms, 2),
        "backend_id": backend_id,
    }

    logger.info(
        f"Transpiled for '{backend_id}' (opt={optimization_level}): "
        f"depth {original_depth}→{transpiled_depth}, "
        f"gates {original_gate_count}→{transpiled_gate_count}, "
        f"swaps={added_swaps}, time={t_ms:.1f}ms"
    )

    return result


def compute_distance_matrix(backend_id: str) -> dict[str, Any]:
    """
    Compute the shortest path distance matrix for a backend's coupling map.
    Used for routing optimization and SWAP cost estimation.

    Returns:
        {
            "distances": list[list[int|float]],  # NxN matrix
            "n_qubits": int,
            "avg_distance": float,
            "max_distance": int,
        }
    """
    from qiskit.transpiler import CouplingMap
    from services.backend_configs import get_backend_config

    cfg = get_backend_config(backend_id)
    raw_coupling = cfg.get("coupling_map")

    if raw_coupling in ("all_to_all", "programmable"):
        n = min(cfg["qubits"], 36)
        # All-to-all: distance is always 1
        distances = [[0 if i == j else 1 for j in range(n)] for i in range(n)]
        return {
            "distances": distances,
            "n_qubits": n,
            "avg_distance": 1.0,
            "max_distance": 1,
        }

    coupling_map = CouplingMap(raw_coupling)
    n = coupling_map.size()
    dist_matrix = coupling_map.distance_matrix

    # Convert numpy array to list, replacing inf with -1
    distances = []
    total_dist = 0
    max_dist = 0
    count = 0
    for i in range(n):
        row = []
        for j in range(n):
            d = int(dist_matrix[i][j]) if dist_matrix[i][j] != float("inf") else -1
            row.append(d)
            if i != j and d > 0:
                total_dist += d
                max_dist = max(max_dist, d)
                count += 1
        distances.append(row)

    avg_dist = total_dist / count if count > 0 else 0

    return {
        "distances": distances,
        "n_qubits": n,
        "avg_distance": round(avg_dist, 2),
        "max_distance": max_dist,
    }
