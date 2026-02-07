import json
import logging
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector, DensityMatrix
from qiskit_aer.noise import NoiseModel, depolarizing_error
from qiskit.circuit.library import RXGate, RYGate, RZGate

logger = logging.getLogger(__name__)

class QuantumEngine:
    def __init__(self):
        self.simulator = AerSimulator()

    def build_circuit(self, circuit_data: list, num_qubits: int) -> QuantumCircuit:
        """
        Constructs a Qiskit QuantumCircuit from the frontend JSON representation.
        """
        qc = QuantumCircuit(num_qubits)
        
        for gate in circuit_data:
            name = gate.get("name", "").lower()
            targets = gate.get("qubits", [])
            params = gate.get("params", [])
            
            # Basic Gates
            if name == "h":
                qc.h(targets[0])
            elif name == "x":
                qc.x(targets[0])
            elif name == "y":
                qc.y(targets[0])
            elif name == "z":
                qc.z(targets[0])
            elif name == "s":
                qc.s(targets[0])
            elif name == "sdg":
                qc.sdg(targets[0])
            elif name == "t":
                qc.t(targets[0])
            elif name == "tdg":
                qc.tdg(targets[0])
            
            # Multi-Qubit Gates
            elif name == "cx" or name == "cnot":
                # Frontend might send [control, target] or just target with control implied?
                # Assuming [control, target] based on standard Qiskit consistency
                if len(targets) >= 2:
                    qc.cx(targets[0], targets[1])
            elif name == "cz":
                if len(targets) >= 2:
                    qc.cz(targets[0], targets[1])
            elif name == "swap":
                if len(targets) >= 2:
                    qc.swap(targets[0], targets[1])
            elif name == "ccx" or name == "toffoli":
                if len(targets) >= 3:
                    qc.ccx(targets[0], targets[1], targets[2])
            
            # Parameterized Gates
            elif name == "rx":
                theta = float(params[0]) if params else 0.0
                qc.rx(theta, targets[0])
            elif name == "ry":
                theta = float(params[0]) if params else 0.0
                qc.ry(theta, targets[0])
            elif name == "rz":
                theta = float(params[0]) if params else 0.0
                qc.rz(theta, targets[0])
            
            # Measure (if specialized, though usually we measure all at end)
            elif name == "measure":
                 qc.measure_all()
        
        return qc

    def run_circuit(self, circuit_data: list, num_qubits: int = 5, use_noise: bool = False):
        """
        Builds and runs a quantum circuit.
        Returns statevector (ideal) or probabilities (noisy/ideal).
        """
        try:
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

            return result_data

        except Exception as e:
            logger.error(f"Error running circuit: {str(e)}")
            raise

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
