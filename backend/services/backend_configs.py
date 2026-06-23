"""
QuantCAI Enterprise — Mock Hardware Backend Configurations
===========================================================
Realistic hardware specs for IBM Eagle, IonQ Forte, QuEra Aquila,
and NVIDIA cuQuantum simulators. These profiles drive:
  - Coupling map visualization (D3.js frontend)
  - Noise model construction (thermal relaxation)
  - Hardware-aware transpilation
  - Cost estimation and billing
"""

from __future__ import annotations
from typing import Any

# ---------------------------------------------------------------------------
# IBM Eagle 127-qubit Heavy-Hex Topology
# ---------------------------------------------------------------------------
# Heavy-hex lattice: each qubit connects to 2-3 neighbors.
# This is a representative subset of the real ibm_washington / ibm_eagle topology.
def _build_ibm_eagle_coupling_map() -> list[list[int]]:
    """Build realistic 127-qubit heavy-hex coupling map edges."""
    edges = [
        # Row 0 (qubits 0-13, heavy-hex pattern)
        [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7],
        [7, 8], [8, 9], [9, 10], [10, 11], [11, 12], [12, 13],
        # Cross connections row 0 -> row 1
        [0, 14], [4, 15], [8, 16], [12, 17],
        # Row 1 (qubits 14-25)
        [14, 18], [15, 19], [16, 20], [17, 21],
        [18, 19], [19, 20], [20, 21],
        # Cross connections row 1 -> row 2
        [18, 22], [19, 23], [20, 24], [21, 25],
        # Row 2 (qubits 22-35)
        [22, 26], [23, 27], [24, 28], [25, 29],
        [26, 27], [27, 28], [28, 29], [29, 30],
        [30, 31], [31, 32], [32, 33], [33, 34], [34, 35],
        # Cross connections row 2 -> row 3
        [26, 36], [30, 37], [34, 38],
        # Row 3 (qubits 36-49)
        [36, 39], [37, 40], [38, 41],
        [39, 40], [40, 41], [41, 42],
        [42, 43], [43, 44], [44, 45], [45, 46],
        [46, 47], [47, 48], [48, 49],
        # Cross connections row 3 -> row 4
        [39, 50], [43, 51], [47, 52],
        # Row 4 (qubits 50-63)
        [50, 53], [51, 54], [52, 55],
        [53, 54], [54, 55], [55, 56],
        [56, 57], [57, 58], [58, 59], [59, 60],
        [60, 61], [61, 62], [62, 63],
        # Cross connections row 4 -> row 5
        [53, 64], [57, 65], [61, 66],
        # Row 5 (qubits 64-77)
        [64, 67], [65, 68], [66, 69],
        [67, 68], [68, 69], [69, 70],
        [70, 71], [71, 72], [72, 73], [73, 74],
        [74, 75], [75, 76], [76, 77],
        # Cross connections row 5 -> row 6
        [67, 78], [71, 79], [75, 80],
        # Row 6 (qubits 78-91)
        [78, 81], [79, 82], [80, 83],
        [81, 82], [82, 83], [83, 84],
        [84, 85], [85, 86], [86, 87], [87, 88],
        [88, 89], [89, 90], [90, 91],
        # Cross connections row 6 -> row 7
        [81, 92], [85, 93], [89, 94],
        # Row 7 (qubits 92-105)
        [92, 95], [93, 96], [94, 97],
        [95, 96], [96, 97], [97, 98],
        [98, 99], [99, 100], [100, 101], [101, 102],
        [102, 103], [103, 104], [104, 105],
        # Cross connections row 7 -> row 8
        [95, 106], [99, 107], [103, 108],
        # Row 8 (qubits 106-119)
        [106, 109], [107, 110], [108, 111],
        [109, 110], [110, 111], [111, 112],
        [112, 113], [113, 114], [114, 115], [115, 116],
        [116, 117], [117, 118], [118, 119],
        # Cross connections row 8 -> row 9
        [109, 120], [113, 121], [117, 122],
        # Row 9 (qubits 120-126)
        [120, 123], [121, 124], [122, 125],
        [123, 124], [124, 125], [125, 126],
    ]
    return edges


def _build_all_to_all_coupling(n_qubits: int) -> list[list[int]]:
    """Build all-to-all coupling map for trapped-ion backends."""
    edges = []
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            edges.append([i, j])
    return edges


def _build_linear_coupling(n_qubits: int) -> list[list[int]]:
    """Build linear nearest-neighbor coupling map."""
    return [[i, i + 1] for i in range(n_qubits - 1)]


# ---------------------------------------------------------------------------
# Backend Configuration Registry
# ---------------------------------------------------------------------------
BACKEND_CONFIGS: dict[str, dict[str, Any]] = {

    "ibm_eagle_127q": {
        "id": "ibm_eagle_127q",
        "name": "IBM 127-qubit Eagle",
        "provider": "IBM Quantum",
        "technology": "Superconducting",
        "qubits": 127,
        "t1_us": 120.5,
        "t2_us": 85.3,
        "gate_time_cx_ns": 500,
        "gate_time_sx_ns": 35,
        "gate_time_rz_ns": 0,       # Virtual gate (no time)
        "readout_error": 0.02,
        "cx_error": 0.01,
        "sx_error": 0.0003,
        "coupling_map": _build_ibm_eagle_coupling_map(),
        "topology": "heavy_hex",
        "basis_gates": ["cx", "id", "rz", "sx", "x"],
        "max_shots": 100_000,
        "max_circuits": 300,
        # Pricing: duration-based (IBM Qiskit Runtime model)
        "pricing_model": "duration",
        "session_cost_per_min": 1.60,
        "per_shot_cost": 0.00096,
        "task_fee": 0.0,
        "status": "online",
        "queue_length": 12,
        "avg_queue_time_min": 4.2,
    },

    "ionq_forte_36q": {
        "id": "ionq_forte_36q",
        "name": "IonQ Forte",
        "provider": "IonQ (via Amazon Braket)",
        "technology": "Trapped Ion",
        "qubits": 36,
        "t1_us": 10_000_000,       # ~10 seconds
        "t2_us": 1_000_000,        # ~1 second
        "gate_time_2q_us": 600,    # 600 µs
        "gate_time_1q_us": 10,     # 10 µs
        "readout_error": 0.005,
        "two_qubit_error": 0.006,
        "single_qubit_error": 0.0003,
        "coupling_map": "all_to_all",
        "topology": "all_to_all",
        "basis_gates": ["gpi", "gpi2", "ms"],
        "max_shots": 10_000,
        "max_circuits": 200,
        # Pricing: per-shot (Amazon Braket model)
        "pricing_model": "per_shot",
        "per_shot_cost": 0.08,
        "task_fee": 0.30,
        "session_cost_per_min": 0.0,
        "status": "online",
        "queue_length": 3,
        "avg_queue_time_min": 1.5,
    },

    "quera_aquila_256q": {
        "id": "quera_aquila_256q",
        "name": "QuEra Aquila (Neutral Atom)",
        "provider": "QuEra (via Amazon Braket)",
        "technology": "Neutral Atom",
        "qubits": 256,
        "t1_us": 4_000_000,        # ~4 seconds
        "t2_us": 2_500_000,        # ~2.5 seconds
        "gate_time_2q_us": 500,
        "gate_time_1q_us": 1,
        "readout_error": 0.03,
        "two_qubit_error": 0.05,
        "single_qubit_error": 0.003,
        "coupling_map": "programmable",
        "topology": "programmable",
        "basis_gates": ["cz", "rx", "rz"],
        "max_shots": 1000,
        "max_circuits": 100,
        # Pricing: per-shot
        "pricing_model": "per_shot",
        "per_shot_cost": 0.01,
        "task_fee": 0.30,
        "session_cost_per_min": 0.0,
        "status": "maintenance",
        "queue_length": 0,
        "avg_queue_time_min": 0,
    },

    "simulator_statevector": {
        "id": "simulator_statevector",
        "name": "NVIDIA cuQuantum (StateVector)",
        "provider": "QuantCAI Cloud",
        "technology": "GPU Simulator",
        "qubits": 32,
        "t1_us": None,
        "t2_us": None,
        "readout_error": 0.0,
        "coupling_map": "all_to_all",
        "topology": "all_to_all",
        "basis_gates": ["cx", "id", "rz", "sx", "x", "h", "s", "t",
                        "sdg", "tdg", "rx", "ry", "cz", "swap", "ccx"],
        "max_shots": 1_000_000,
        "max_circuits": 1000,
        "simulation_method": "statevector",
        # Pricing: per-minute GPU billing
        "pricing_model": "per_minute",
        "cost_per_minute": 0.12,
        "min_billing_seconds": 3,
        "per_shot_cost": 0.0,
        "task_fee": 0.0,
        "session_cost_per_min": 0.0,
        "status": "online",
        "queue_length": 0,
        "avg_queue_time_min": 0,
    },

    "simulator_tensor_network": {
        "id": "simulator_tensor_network",
        "name": "NVIDIA cuQuantum (TensorNetwork)",
        "provider": "QuantCAI Cloud",
        "technology": "GPU Simulator",
        "qubits": 100,
        "t1_us": None,
        "t2_us": None,
        "readout_error": 0.0,
        "coupling_map": "all_to_all",
        "topology": "all_to_all",
        "basis_gates": ["cx", "id", "rz", "sx", "x", "h", "s", "t",
                        "sdg", "tdg", "rx", "ry", "cz", "swap", "ccx"],
        "max_shots": 100_000,
        "max_circuits": 500,
        "simulation_method": "tensor_network",
        # Pricing: per-minute GPU billing (higher cost)
        "pricing_model": "per_minute",
        "cost_per_minute": 0.28,
        "min_billing_seconds": 3,
        "per_shot_cost": 0.0,
        "task_fee": 0.0,
        "session_cost_per_min": 0.0,
        "status": "online",
        "queue_length": 0,
        "avg_queue_time_min": 0,
    },

    "local_simulator": {
        "id": "local_simulator",
        "name": "Local Simulator (Qiskit Aer)",
        "provider": "Local",
        "technology": "CPU Simulator",
        "qubits": 29,
        "t1_us": None,
        "t2_us": None,
        "readout_error": 0.0,
        "coupling_map": "all_to_all",
        "topology": "all_to_all",
        "basis_gates": ["cx", "id", "rz", "sx", "x", "h", "s", "t",
                        "sdg", "tdg", "rx", "ry", "cz", "swap", "ccx",
                        "u1", "u2", "u3"],
        "max_shots": 65_536,
        "max_circuits": 100,
        "simulation_method": "automatic",
        "pricing_model": "free",
        "cost_per_minute": 0.0,
        "per_shot_cost": 0.0,
        "task_fee": 0.0,
        "session_cost_per_min": 0.0,
        "status": "online",
        "queue_length": 0,
        "avg_queue_time_min": 0,
    },
}


def get_backend_config(backend_id: str) -> dict[str, Any]:
    """Retrieve backend configuration by ID. Raises KeyError if not found."""
    if backend_id not in BACKEND_CONFIGS:
        raise KeyError(
            f"Unknown backend '{backend_id}'. "
            f"Available: {list(BACKEND_CONFIGS.keys())}"
        )
    return BACKEND_CONFIGS[backend_id]


def list_backends() -> list[dict[str, Any]]:
    """Return all backends as a list with summary info (no coupling map data)."""
    result = []
    for bid, cfg in BACKEND_CONFIGS.items():
        summary = {
            "id": cfg["id"],
            "name": cfg["name"],
            "provider": cfg["provider"],
            "technology": cfg["technology"],
            "qubits": cfg["qubits"],
            "topology": cfg["topology"],
            "basis_gates": cfg["basis_gates"],
            "pricing_model": cfg["pricing_model"],
            "status": cfg["status"],
            "queue_length": cfg.get("queue_length", 0),
        }
        result.append(summary)
    return result


def get_coupling_map_data(backend_id: str) -> dict[str, Any]:
    """
    Return coupling map data formatted for D3.js visualization.
    Returns nodes with T1/T2 metadata and edges with error rates.
    """
    cfg = get_backend_config(backend_id)
    coupling = cfg["coupling_map"]

    if coupling == "all_to_all":
        n = min(cfg["qubits"], 36)  # Cap visualization at 36 for all-to-all
        nodes = []
        for i in range(n):
            nodes.append({
                "id": i,
                "t1": cfg.get("t1_us"),
                "t2": cfg.get("t2_us"),
                "readoutError": cfg.get("readout_error", 0.0),
            })
        # For all-to-all, only show a subset of edges for visualization
        edges = []
        for i in range(n):
            for j in range(i + 1, min(i + 4, n)):
                edges.append({
                    "source": i,
                    "target": j,
                    "cxError": cfg.get("two_qubit_error", cfg.get("cx_error", 0.01)),
                    "cxTime": cfg.get("gate_time_2q_us", cfg.get("gate_time_cx_ns", 500)),
                })
        return {
            "nodes": nodes,
            "edges": edges,
            "topology": cfg["topology"],
            "totalQubits": cfg["qubits"],
        }

    elif coupling == "programmable":
        # QuEra: programmable topology, show a grid-like arrangement
        n = min(cfg["qubits"], 64)  # Cap for visualization
        nodes = [
            {
                "id": i,
                "t1": cfg.get("t1_us"),
                "t2": cfg.get("t2_us"),
                "readoutError": cfg.get("readout_error", 0.0),
            }
            for i in range(n)
        ]
        # Generate a grid topology for visualization
        cols = 8
        edges = []
        for i in range(n):
            if (i + 1) % cols != 0 and i + 1 < n:
                edges.append({
                    "source": i, "target": i + 1,
                    "cxError": cfg.get("two_qubit_error", 0.05),
                    "cxTime": cfg.get("gate_time_2q_us", 500),
                })
            if i + cols < n:
                edges.append({
                    "source": i, "target": i + cols,
                    "cxError": cfg.get("two_qubit_error", 0.05),
                    "cxTime": cfg.get("gate_time_2q_us", 500),
                })
        return {
            "nodes": nodes,
            "edges": edges,
            "topology": "programmable_grid",
            "totalQubits": cfg["qubits"],
        }

    else:
        # IBM Eagle or similar: explicit coupling map
        nodes = []
        qubit_ids = set()
        for edge in coupling:
            qubit_ids.add(edge[0])
            qubit_ids.add(edge[1])

        for qid in sorted(qubit_ids):
            nodes.append({
                "id": qid,
                "t1": cfg.get("t1_us", 120.5),
                "t2": cfg.get("t2_us", 85.3),
                "readoutError": cfg.get("readout_error", 0.02),
            })

        edges = [
            {
                "source": e[0],
                "target": e[1],
                "cxError": cfg.get("cx_error", 0.01),
                "cxTime": cfg.get("gate_time_cx_ns", 500),
            }
            for e in coupling
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "topology": cfg["topology"],
            "totalQubits": cfg["qubits"],
        }
