from qiskit import QuantumCircuit

qasm = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q -> c;"""

try:
    qc = QuantumCircuit.from_qasm_str(qasm)
    print("SUCCESS")
    print("Qubits:", qc.num_qubits)
    print("Depth:", qc.depth())
except Exception as e:
    print("FAILED")
    print(e)
