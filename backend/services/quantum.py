"""
QuantCAI — Quantum Engine Service (Enterprise Grade)
=====================================================
Handles circuit building, simulation execution, and OpenQASM 3.0 export.
Supports all standard single-qubit, phase, and multi-qubit gates.
"""

import logging
import time
import math
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector, DensityMatrix
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit.circuit.library import RXGate, RYGate, RZGate

logger = logging.getLogger(__name__)


class CircuitBuildError(Exception):
    """Raised when a circuit cannot be built from the provided gate instructions."""
    pass


class SimulationError(Exception):
    """Raised when the simulation fails."""
    pass


class QuantumEngine:
    def __init__(self):
        self.simulator = AerSimulator()

    # ------------------------------------------------------------------
    # Gate Application Map
    # ------------------------------------------------------------------
    SINGLE_QUBIT_GATES = {"h", "x", "y", "z", "s", "sdg", "t", "tdg"}
    PARAMETERIZED_GATES = {"rx", "ry", "rz"}
    TWO_QUBIT_GATES = {"cx", "cnot", "cz", "swap"}
    THREE_QUBIT_GATES = {"ccx", "toffoli"}

    def _apply_gate(self, qc: QuantumCircuit, name: str, qubits: list[int], params: list[float]) -> None:
        """Apply a single gate instruction to the circuit."""
        try:
            # Single Qubit Gates
            if name == "h":
                qc.h(qubits[0])
            elif name == "x":
                qc.x(qubits[0])
            elif name == "y":
                qc.y(qubits[0])
            elif name == "z":
                qc.z(qubits[0])
            elif name == "s":
                qc.s(qubits[0])
            elif name == "sdg":
                qc.sdg(qubits[0])
            elif name == "t":
                qc.t(qubits[0])
            elif name == "tdg":
                qc.tdg(qubits[0])

            # Parameterized Gates
            elif name == "rx":
                theta = float(params[0]) if params else math.pi / 2
                qc.rx(theta, qubits[0])
            elif name == "ry":
                theta = float(params[0]) if params else math.pi / 2
                qc.ry(theta, qubits[0])
            elif name == "rz":
                theta = float(params[0]) if params else math.pi / 2
                qc.rz(theta, qubits[0])

            # Multi-Qubit Gates
            elif name in ("cx", "cnot"):
                if len(qubits) >= 2:
                    qc.cx(qubits[0], qubits[1])
                else:
                    raise CircuitBuildError(f"CX gate requires 2 qubits, got {len(qubits)}")
            elif name == "cz":
                if len(qubits) >= 2:
                    qc.cz(qubits[0], qubits[1])
                else:
                    raise CircuitBuildError(f"CZ gate requires 2 qubits, got {len(qubits)}")
            elif name == "swap":
                if len(qubits) >= 2:
                    qc.swap(qubits[0], qubits[1])
                else:
                    raise CircuitBuildError(f"SWAP gate requires 2 qubits, got {len(qubits)}")
            elif name in ("ccx", "toffoli"):
                if len(qubits) >= 3:
                    qc.ccx(qubits[0], qubits[1], qubits[2])
                else:
                    raise CircuitBuildError(f"CCX gate requires 3 qubits, got {len(qubits)}")

            # Measure
            elif name == "measure":
                qc.measure_all()
            else:
                raise CircuitBuildError(f"Unknown gate: '{name}'")
        except CircuitBuildError:
            raise
        except Exception as e:
            raise CircuitBuildError(f"Error applying gate '{name}' on qubits {qubits}: {e}") from e

    def build_circuit(self, circuit_data: list, num_qubits: int) -> QuantumCircuit:
        """
        Constructs a Qiskit QuantumCircuit from the frontend JSON representation.
        Validates qubit bounds before applying gates.
        """
        qc = QuantumCircuit(num_qubits)

        for i, gate in enumerate(circuit_data):
            if isinstance(gate, dict):
                name = gate.get("name", "").lower().strip()
                qubits = gate.get("qubits", [])
                params = gate.get("params", [])
            else:
                # Support Pydantic model objects
                name = gate.name.lower().strip()
                qubits = list(gate.qubits)
                params = list(gate.params) if gate.params else []

            # Validate qubit bounds
            for q in qubits:
                if q < 0 or q >= num_qubits:
                    raise CircuitBuildError(
                        f"Gate '{name}' (instruction {i}) references qubit {q}, "
                        f"but circuit only has {num_qubits} qubits (0–{num_qubits - 1})."
                    )

            self._apply_gate(qc, name, qubits, params)

        return qc

    def run_circuit(self, circuit_data: list, num_qubits: int = 5, use_noise: bool = False):
        """
        Builds and runs a quantum circuit.
        Returns statevector (ideal) or probabilities (noisy/ideal).
        """
        try:
            t_start = time.perf_counter()

            qc = self.build_circuit(circuit_data, num_qubits)

            # Analysis Metrics
            depth = qc.depth()
            gate_count = dict(qc.count_ops())

            result_data = {
                "metrics": {
                    "depth": depth,
                    "gate_count": gate_count,
                    "qubit_count": num_qubits
                }
            }

            # Noise Model
            noise_model = None
            if use_noise:
                # Add basic depolarizing noise
                noise_model = NoiseModel()
                error_1 = depolarizing_error(0.01, 1) # 1% error for 1-qubit gates
                error_2 = depolarizing_error(0.05, 2) # 5% error for 2-qubit gates

                noise_model.add_all_qubit_quantum_error(error_1, ['h', 'x', 'y', 'z', 's', 't', 'rx', 'ry', 'rz'])
                noise_model.add_all_qubit_quantum_error(error_2, ['cx', 'cz', 'swap'])

                # For noisy simulation, we need measurement statistics, not statevector
                qc.measure_all()

                # Run Simulation
                transpiled_qc = transpile(qc, self.simulator)
                result = self.simulator.run(transpiled_qc, noise_model=noise_model, shots=1024).result()
                counts = result.get_counts()

                # Convert counts to probabilities
                total_shots = sum(counts.values())
                probs = {k: v/total_shots for k, v in counts.items()}

                result_data["type"] = "noisy"
                result_data["probabilities"] = probs

            else:
                # Ideal Statevector Simulation
                qc_for_sv = qc.copy()
                qc_for_sv.save_statevector()
                transpiled_qc = transpile(qc_for_sv, self.simulator)
                result = self.simulator.run(transpiled_qc).result()
                statevector = result.get_statevector()

                # Format Complex Statevector
                sv_dict = []
                probs = {}
                for i, amp in enumerate(statevector):
                    if abs(amp) > 1e-10: # Filter zero amplitudes
                        binary_string = format(i, f'0{num_qubits}b')
                        prob = abs(amp) ** 2
                        probs[binary_string] = prob
                        sv_dict.append({
                            "basis": binary_string,
                            "amplitude": {"real": float(amp.real), "imag": float(amp.imag)},
                            "probability": prob,
                            "phase": float(np.angle(amp))
                        })

                result_data["type"] = "ideal"
                result_data["statevector"] = sv_dict
                result_data["probabilities"] = probs # Duplicated for easy chart plotting

            t_elapsed_ms = (time.perf_counter() - t_start) * 1000
            result_data["execution_time_ms"] = round(t_elapsed_ms, 2)

            return result_data

        except CircuitBuildError:
            raise
        except Exception as e:
            logger.error(f"Error running circuit: {str(e)}")
            raise

    def run_circuit_v1(self, circuit_data: list, num_qubits: int = 5, shots: int = 1024, use_noise: bool = False):
        """
        V1 Enterprise endpoint: Builds and runs a quantum circuit with configurable shots.
        Returns a structured response compatible with SimulationResultResponse.
        """
        try:
            t_start = time.perf_counter()

            qc = self.build_circuit(circuit_data, num_qubits)

            # Analysis Metrics
            depth = qc.depth()
            gate_count = dict(qc.count_ops())

            metrics = {
                "depth": depth,
                "gate_count": gate_count,
                "qubit_count": num_qubits
            }

            # Noise Model
            noise_model = None
            if use_noise:
                noise_model = NoiseModel()
                error_1 = depolarizing_error(0.01, 1)
                error_2 = depolarizing_error(0.05, 2)
                noise_model.add_all_qubit_quantum_error(error_1, ['h', 'x', 'y', 'z', 's', 't', 'rx', 'ry', 'rz'])
                noise_model.add_all_qubit_quantum_error(error_2, ['cx', 'cz', 'swap'])

                qc.measure_all()
                transpiled_qc = transpile(qc, self.simulator)
                result = self.simulator.run(transpiled_qc, noise_model=noise_model, shots=shots).result()
                counts = result.get_counts()
                total_shots = sum(counts.values())
                probs = {k: v / total_shots for k, v in counts.items()}

                t_elapsed_ms = (time.perf_counter() - t_start) * 1000

                return {
                    "type": "noisy",
                    "probabilities": probs,
                    "statevector": None,
                    "metrics": metrics,
                    "execution_time_ms": round(t_elapsed_ms, 2),
                }
            else:
                # Ideal Statevector Simulation
                qc_for_sv = qc.copy()
                qc_for_sv.save_statevector()
                transpiled_qc = transpile(qc_for_sv, self.simulator)
                result = self.simulator.run(transpiled_qc).result()
                statevector = result.get_statevector()

                sv_dict = []
                probs = {}
                for i, amp in enumerate(statevector):
                    if abs(amp) > 1e-10:
                        binary_string = format(i, f'0{num_qubits}b')
                        prob = abs(amp) ** 2
                        probs[binary_string] = prob
                        sv_dict.append({
                            "basis": binary_string,
                            "amplitude": {"real": float(amp.real), "imag": float(amp.imag)},
                            "probability": prob,
                            "phase": float(np.angle(amp))
                        })

                t_elapsed_ms = (time.perf_counter() - t_start) * 1000

                return {
                    "type": "ideal",
                    "probabilities": probs,
                    "statevector": sv_dict,
                    "metrics": metrics,
                    "execution_time_ms": round(t_elapsed_ms, 2),
                }

        except CircuitBuildError:
            raise
        except Exception as e:
            logger.error(f"Error running v1 circuit: {str(e)}")
            raise SimulationError(f"Simulation failed: {e}") from e

    def export_qasm3(self, circuit_data: list, num_qubits: int) -> str:
        """
        Generate an OpenQASM 3.0 string from the gate instruction list.
        Produces standards-compliant QASM 3.0 output.
        """
        lines = [
            'OPENQASM 3.0;',
            'include "stdgates.inc";',
            '',
            f'qubit[{num_qubits}] q;',
            f'bit[{num_qubits}] c;',
            '',
        ]

        for gate in circuit_data:
            if isinstance(gate, dict):
                name = gate.get("name", "").lower().strip()
                qubits = gate.get("qubits", [])
                params = gate.get("params", [])
            else:
                name = gate.name.lower().strip()
                qubits = list(gate.qubits)
                params = list(gate.params) if gate.params else []

            # Single-qubit gates
            if name == "h":
                lines.append(f"h q[{qubits[0]}];")
            elif name == "x":
                lines.append(f"x q[{qubits[0]}];")
            elif name == "y":
                lines.append(f"y q[{qubits[0]}];")
            elif name == "z":
                lines.append(f"z q[{qubits[0]}];")
            elif name == "s":
                lines.append(f"s q[{qubits[0]}];")
            elif name == "sdg":
                lines.append(f"sdg q[{qubits[0]}];")
            elif name == "t":
                lines.append(f"t q[{qubits[0]}];")
            elif name == "tdg":
                lines.append(f"tdg q[{qubits[0]}];")

            # Parameterized gates
            elif name == "rx":
                theta = params[0] if params else math.pi / 2
                lines.append(f"rx({theta:.6f}) q[{qubits[0]}];")
            elif name == "ry":
                theta = params[0] if params else math.pi / 2
                lines.append(f"ry({theta:.6f}) q[{qubits[0]}];")
            elif name == "rz":
                theta = params[0] if params else math.pi / 2
                lines.append(f"rz({theta:.6f}) q[{qubits[0]}];")

            # Multi-qubit gates
            elif name in ("cx", "cnot"):
                lines.append(f"cx q[{qubits[0]}], q[{qubits[1]}];")
            elif name == "cz":
                lines.append(f"cz q[{qubits[0]}], q[{qubits[1]}];")
            elif name == "swap":
                lines.append(f"swap q[{qubits[0]}], q[{qubits[1]}];")
            elif name in ("ccx", "toffoli"):
                lines.append(f"ccx q[{qubits[0]}], q[{qubits[1]}], q[{qubits[2]}];")

        # Add measurement
        lines.append("")
        for i in range(num_qubits):
            lines.append(f"c[{i}] = measure q[{i}];")

        lines.append("")
        return "\n".join(lines)

    def calculate_next_state(self, current_state: dict, gate: str):
        """
        Calculates the next state for a single qubit interactive tool.
        """
        try:
            # Reconstruct basic input state
            alpha = complex(current_state.get("alpha_real", current_state.get("alpha", 1)),
                           current_state.get("alpha_imag", 0))
            beta = complex(current_state.get("beta_real", current_state.get("beta", 0)),
                          current_state.get("beta_imag", 0))

            sv = [alpha, beta]

            qc = QuantumCircuit(1)
            qc.initialize(sv, 0)

            # Normalize gate name
            g = gate.lower()
            if "x" in g and "not" in g: qc.x(0)
            elif "y" in g: qc.y(0)
            elif "z" in g: qc.z(0)
            elif "h" in g: qc.h(0)
            elif "s" in g: qc.s(0)
            elif "t" in g: qc.t(0)

            new_sv = Statevector.from_instruction(qc)
            new_alpha = new_sv[0]
            new_beta = new_sv[1]

            return {
                "alpha_real": float(new_alpha.real),
                "alpha_imag": float(new_alpha.imag),
                "beta_real": float(new_beta.real),
                "beta_imag": float(new_beta.imag),
                "probability_zero": float(abs(new_alpha)**2),
                "probability_one": float(abs(new_beta)**2)
            }
        except Exception as e:
            logger.error(f"Error calculating next state: {str(e)}")
            raise
