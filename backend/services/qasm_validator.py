import re

FORBIDDEN_QASM_PATTERNS = [
    re.compile(r"\brecursive\b", re.IGNORECASE),
]

def validate_qasm_security(qasm_str: str) -> None:
    """
    Reject QASM strings containing forbidden constructs like recursive definitions.
    """
    for line_no, raw_line in enumerate(qasm_str.splitlines(), start=1):
        line = raw_line.split("//")[0].strip()  # strip inline comments
        if not line:
            continue
        for pattern in FORBIDDEN_QASM_PATTERNS:
            if pattern.search(line):
                raise ValueError(
                    f"Forbidden construct detected on line {line_no}: "
                    f"'{pattern.pattern.strip()}' statements are not allowed for security reasons"
                )

def parse_and_validate_qasm(qasm_str: str) -> tuple[int, int]:
    """
    Attempt to parse the QASM 3.0 string with Qiskit.
    Returns (num_qubits, circuit_depth) on success; raises ValueError on failure.
    """
    try:
        import qiskit.qasm3
        qc = qiskit.qasm3.loads(qasm_str)
        return qc.num_qubits, qc.depth()
    except Exception as exc:
        raise ValueError(f"QASM3 Parse Error: {exc}") from exc
