import qiskit.qasm3

qasm = """OPENQASM 3.0;
include "stdgates.inc";

qubit[3] q;
bit[3] c;

h q[0];
cx q[0], q[1];
c[0] = measure q[0];
"""

try:
    qc = qiskit.qasm3.loads(qasm)
    print("Success:")
    print(qc)
except Exception as e:
    print("Error:", e)
