"""
QuantAI Enterprise Knowledge Base & Dynamic Context Engine
===========================================================
Provides deep platform knowledge, learning curriculum, enterprise sales playbook,
and dynamic prompt assembly for multi-persona AI copilot.
"""

import json
from typing import Optional, Dict, Any

# ---------------------------------------------------------------------------
# 1. PLATFORM KNOWLEDGE — Complete structured data about all platform features
# ---------------------------------------------------------------------------

PLATFORM_KNOWLEDGE = {
    "name": "QuantCAI",
    "tagline": "Learn, Build, and Secure Quantum Computing",
    "website": "https://quantcai.in",
    "support_email": "quantc.info@gmail.com",

    "navigation": {
        "/": "Landing page — overview of QuantCAI platform",
        "/learn": "Learning hub — introduction to quantum computing with interactive content",
        "/quantum-computing": "Deep-dive into quantum computing fundamentals",
        "/learn/qubits": "Module: Understanding Qubits — superposition, measurement, Dirac notation",
        "/learn/gates": "Module: Quantum Gates — Hadamard, Pauli-X/Y/Z, CNOT, phase gates",
        "/learn/pqc": "Module: Post-Quantum Cryptography — NIST standards, ML-KEM, ML-DSA, SLH-DSA",
        "/quantum-states": "Interactive Quantum States Visualizer — Bloch sphere, real-time gate effects",
        "/circuit-builder": "Multi-Qubit Circuit Builder — drag-and-drop, up to 8 qubits, OpenQASM export",
        "/quantum-simulator": "Quantum Simulator — write OpenQASM 2.0, run on remote simulator",
        "/tools": "Tools hub — links to all interactive tools",
        "/pqc-scanner": "PQC Vulnerability Scanner — scan domains for quantum-vulnerable cryptography",
        "/repo-scanner": "Repository Scanner — scan GitHub repos for hardcoded cryptographic vulnerabilities",
        "/enterprise": "Enterprise page — on-prem deployment, compliance suite, custom SLAs",
        "/community": "Community forum and discussions",
        "/vision": "QuantCAI vision and roadmap",
        "/profile": "User profile and subscription management",
    },

    "tools": {
        "quantum_states_visualizer": {
            "name": "Interactive Quantum States Visualizer",
            "route": "/quantum-states",
            "description": "Explore quantum superposition and entanglement through real-time Bloch sphere visualization. Apply gates (H, X, Y, Z, S, T) and see how they transform the qubit state vector.",
            "use_cases": ["Learning superposition", "Visualizing gate effects", "Understanding Bloch sphere representation"],
            "capabilities": ["Real-time Bloch sphere", "Gate application", "State vector display", "Probability readout"],
        },
        "circuit_builder": {
            "name": "Multi-Qubit Circuit Builder",
            "route": "/circuit-builder",
            "description": "Design and simulate complex quantum circuits with multiple qubits. Drag and drop gates, run experiments, and save your work. Supports up to 8 qubits with full OpenQASM 2.0 export.",
            "use_cases": ["Building quantum circuits", "Learning gate sequences", "Experimenting with entanglement", "Generating OpenQASM code"],
            "capabilities": ["Drag-and-drop gate placement", "Up to 8 qubits", "Real-time circuit metrics", "Probability distribution visualization",
                             "Statevector view", "Live QASM code", "Circuit templates", "Share circuits via URL", "GPU cost estimation"],
            "gate_library": {
                "single_qubit": ["H (Hadamard)", "X (Pauli-X / NOT)", "Y (Pauli-Y)", "Z (Pauli-Z)", "S (Phase)", "T (π/8)", "RX", "RY", "RZ"],
                "multi_qubit": ["CX (CNOT)", "CZ (Controlled-Z)", "SWAP"],
            },
            "templates": ["Bell State", "GHZ State", "Quantum Teleportation", "Grover's Search", "Bernstein-Vazirani",
                          "Quantum Fourier Transform", "Deutsch-Jozsa", "Superdense Coding"],
        },
        "quantum_simulator": {
            "name": "Quantum Simulator",
            "route": "/quantum-simulator",
            "description": "Write OpenQASM 2.0 circuits, configure parameters, and execute them on a remote quantum simulator. For users who prefer code over drag-and-drop.",
            "use_cases": ["Running custom QASM code", "Testing algorithms", "Advanced circuit design"],
            "capabilities": ["OpenQASM 2.0 editor", "Configurable shots", "Remote execution", "Result visualization"],
        },
        "pqc_scanner": {
            "name": "PQC Vulnerability Scanner",
            "route": "/pqc-scanner",
            "description": "Evaluate domains against Post-Quantum Cryptography vulnerability metrics. Receive instant NIST-aligned risk reports with TLS version analysis, certificate inspection, cipher suite evaluation, and PQC readiness scoring.",
            "use_cases": ["Security assessment", "Compliance checking", "Risk analysis", "Migration planning"],
            "capabilities": ["TLS version detection", "Certificate chain analysis", "Cipher suite evaluation",
                             "PQC readiness score (0-100)", "Vulnerability classification", "Remediation recommendations",
                             "FIPS 203/204/205 alignment", "HNDL risk assessment"],
            "risk_levels": {
                "CRITICAL": "Quantum-vulnerable algorithms in active use (RSA-2048, ECC-256) with no PQC fallback",
                "HIGH": "Legacy TLS versions or weak key exchange mechanisms",
                "MEDIUM": "Partial PQC adoption — hybrid configurations needed",
                "LOW": "Strong cryptographic posture with modern algorithms",
                "SAFE": "Full PQC compliance achieved",
            },
        },
        "repo_scanner": {
            "name": "Repository Scanner",
            "route": "/repo-scanner",
            "description": "Scan GitHub repositories for hardcoded cryptographic patterns and quantum-vulnerable dependencies.",
            "use_cases": ["Code audit", "Dependency scanning", "Cryptographic hygiene"],
            "capabilities": ["GitHub integration", "Pattern matching", "Dependency analysis"],
        },
    },

    "pricing_tiers": {
        "free": {
            "name": "Free",
            "price": "$0",
            "features": ["5 AI tutor queries/day", "10 AI chat messages/day", "Basic circuit builder", "3 PQC scans/day", "Community access"],
            "limitations": ["Limited AI interactions", "No circuit optimization", "No internal network scanning"],
        },
        "pro": {
            "name": "Pro",
            "price": "$9.99/month",
            "features": ["Unlimited AI queries", "Advanced circuit builder", "Unlimited PQC scans", "Priority support",
                         "Circuit optimization", "Full learning path access", "Wallet credits for API"],
            "limitations": ["No on-prem deployment", "No CLI scanner", "No custom SLAs"],
        },
        "enterprise": {
            "name": "Enterprise",
            "price": "Custom pricing",
            "features": ["Everything in Pro", "On-premises deployment", "CLI scanner for internal networks",
                         "Custom SLAs", "Dedicated support", "RBAC and SSO", "Audit logging",
                         "LQM Compliance AI advisor", "Unlimited API access", "Team management"],
            "contact": "quantc.info@gmail.com",
        },
    },
}

# ---------------------------------------------------------------------------
# 2. LEARNING CURRICULUM — Structured learning path with deep content knowledge
# ---------------------------------------------------------------------------

LEARNING_CURRICULUM = {
    "path_order": ["learn", "quantum-computing", "learn/qubits", "learn/gates", "learn/pqc"],

    "modules": {
        "learn": {
            "title": "Welcome to QuantCAI — Introduction",
            "route": "/learn",
            "topics": [
                "What is quantum computing and why it matters",
                "Visual drag-and-drop learning approach",
                "Real-time superposition and entanglement visualization",
                "Pre-built circuit templates for beginners",
            ],
            "quiz": {
                "question": "What is the fundamental unit of quantum information that can exist in a superposition of states?",
                "options": ["Classical Bit", "Qubit", "Quantum Byte", "Trit"],
                "correct_index": 1,
                "correct_answer": "Qubit",
                "explanation": "A qubit (quantum bit) is the fundamental unit of quantum information. Unlike classical bits that are either 0 or 1, qubits can exist in a superposition of both states simultaneously.",
                "teaching_hint": "Ask the student what they know about the difference between classical and quantum information before revealing the answer.",
            },
            "next_module": "quantum-computing",
            "suggested_tools": ["quantum_states_visualizer"],
            "key_analogies": [
                "A qubit is like a coin spinning in the air — it's both heads AND tails until you catch it (measure it).",
                "Quantum computing is like exploring every path in a maze simultaneously instead of one at a time.",
            ],
        },

        "quantum-computing": {
            "title": "Quantum Computing Fundamentals",
            "route": "/quantum-computing",
            "topics": [
                "Classical vs quantum computing paradigm",
                "Quantum bits and measurement",
                "Wave-particle duality",
                "Quantum parallelism",
                "Decoherence and error correction",
            ],
            "next_module": "learn/qubits",
            "suggested_tools": ["quantum_states_visualizer", "circuit_builder"],
        },

        "learn/qubits": {
            "title": "Understanding Qubits",
            "route": "/learn/qubits",
            "topics": [
                "Qubit mathematical representation: |ψ⟩ = α|0⟩ + β|1⟩",
                "Superposition: being in multiple states at once",
                "Measurement: collapsing the quantum state",
                "Dirac notation (bra-ket)",
                "Bloch sphere representation",
                "Probability amplitudes: |α|² + |β|² = 1",
            ],
            "quiz": {
                "question": "What quantum phenomenon allows a qubit to be in a linear combination of |0⟩ and |1⟩ states simultaneously?",
                "options": ["Quantum Decoherence", "Quantum Superposition", "Quantum Entanglement", "Classical Teleportation"],
                "correct_index": 1,
                "correct_answer": "Quantum Superposition",
                "explanation": "Superposition is the principle that allows a qubit to exist in a linear combination of |0⟩ and |1⟩ simultaneously, described mathematically as |ψ⟩ = α|0⟩ + β|1⟩ where α and β are complex probability amplitudes.",
                "teaching_hint": "Guide the student to think about what makes quantum different from classical — it's not about being 0 OR 1, but both at once.",
            },
            "next_module": "learn/gates",
            "suggested_tools": ["quantum_states_visualizer"],
            "key_analogies": [
                "A qubit in superposition is like being at a fork in the road and taking BOTH paths at the same time.",
                "Measurement is like opening Schrödinger's box — the cat is either alive or dead once you look.",
            ],
        },

        "learn/gates": {
            "title": "Quantum Gates",
            "route": "/learn/gates",
            "topics": [
                "Single-qubit gates: Hadamard (H), Pauli-X/Y/Z, Phase (S, T)",
                "The Hadamard gate: creating superposition from |0⟩",
                "Pauli-X: the quantum NOT gate",
                "Multi-qubit gates: CNOT (CX), CZ, SWAP",
                "CNOT and entanglement: creating Bell states",
                "Gate matrices and unitary transformations",
                "Universal gate sets",
            ],
            "quiz": {
                "question": "Which quantum gate is primarily used to put a qubit into a state of equal superposition?",
                "options": ["X (Pauli-X) Gate", "H (Hadamard) Gate", "Z (Pauli-Z) Gate", "CNOT Gate"],
                "correct_index": 1,
                "correct_answer": "H (Hadamard) Gate",
                "explanation": "The Hadamard gate transforms |0⟩ to (|0⟩+|1⟩)/√2, creating an equal superposition. It is one of the most fundamental gates in quantum computing.",
                "teaching_hint": "Ask the student to think about what gate takes a definite state (|0⟩) and makes it uncertain — that's the gateway to quantum parallelism.",
            },
            "next_module": "learn/pqc",
            "suggested_tools": ["circuit_builder", "quantum_states_visualizer"],
            "exercises": [
                "Build a Bell State: Apply H to q[0], then CNOT from q[0] to q[1]",
                "Create a GHZ state: Extend the Bell State pattern to 3 qubits",
                "Experiment: Apply X gate before and after H — what changes?",
            ],
        },

        "learn/pqc": {
            "title": "Post-Quantum Cryptography",
            "route": "/learn/pqc",
            "topics": [
                "The quantum threat to current cryptography",
                "Shor's algorithm: breaking RSA and ECC",
                "NIST Post-Quantum Cryptography standards",
                "FIPS 203: ML-KEM (Module-Lattice Key Encapsulation)",
                "FIPS 204: ML-DSA (Module-Lattice Digital Signature)",
                "FIPS 205: SLH-DSA (Stateless Hash-Based Digital Signature)",
                "Migration strategies: hybrid approaches",
                "CNSA 2.0 timeline and requirements",
            ],
            "quiz": {
                "question": "Which cryptographic standard specifies ML-KEM for quantum-safe key exchange?",
                "options": ["FIPS 197", "FIPS 203", "FIPS 204", "FIPS 140-3"],
                "correct_index": 1,
                "correct_answer": "FIPS 203",
                "explanation": "FIPS 203 standardizes ML-KEM (Module-Lattice-Based Key Encapsulation Mechanism), the quantum-safe replacement for RSA and ECC key exchange.",
                "teaching_hint": "Help the student connect the dots: FIPS 203 = key exchange (ML-KEM), FIPS 204 = signatures (ML-DSA), FIPS 205 = hash-based signatures (SLH-DSA).",
            },
            "next_module": None,
            "suggested_tools": ["pqc_scanner"],
            "key_analogies": [
                "Current encryption is like a lock that's very hard to pick — but quantum computers have the master key (Shor's algorithm).",
                "PQC is like building locks that even the master key can't open — based on mathematical problems quantum computers can't solve efficiently.",
            ],
        },
    },
}

# ---------------------------------------------------------------------------
# 3. ENTERPRISE PLAYBOOK — Sales intelligence and enterprise guidance
# ---------------------------------------------------------------------------

ENTERPRISE_PLAYBOOK = {
    "cli_scanner": {
        "name": "QuantCAI PQC Scanner CLI",
        "description": "Command-line tool for scanning internal networks, CIDR ranges, and private infrastructure for quantum-vulnerable cryptography. Deployable on-premises behind firewalls.",
        "use_cases": [
            "Internal network TLS auditing",
            "Certificate chain analysis across private infrastructure",
            "CI/CD pipeline integration for automated cryptographic compliance",
            "Air-gapped environment scanning",
            "Bulk domain/IP range scanning (CIDR notation)",
        ],
        "installation": "pip install quantcai-scanner",
        "example_commands": [
            "quantcai-scanner scan --target example.com",
            "quantcai-scanner scan --target 192.168.1.0/24 --output json",
            "quantcai-scanner scan --target internal.corp.net --port 443 --timeout 10",
        ],
        "licensing": "Enterprise license required. Contact quantc.info@gmail.com for pricing based on scope (number of hosts, scan frequency).",
        "differentiators": [
            "Unlike our web scanner, the CLI can scan internal/private networks",
            "Supports CIDR range notation for bulk scanning",
            "Can be integrated into CI/CD pipelines",
            "Generates machine-readable JSON reports for SIEM integration",
            "Deployable in air-gapped environments",
        ],
    },

    "on_prem_deployment": {
        "description": "Full QuantCAI platform deployed on-premises within the enterprise's own infrastructure using Docker Compose or Helm charts.",
        "components": ["Backend API", "Frontend UI", "Redis cache", "PostgreSQL database", "Celery worker", "Scanner engine"],
        "requirements": ["Docker + Docker Compose or Kubernetes", "4+ CPU cores", "8GB+ RAM", "PostgreSQL 14+", "Redis 7+"],
        "benefits": ["Data sovereignty", "No external data transfer", "Custom branding", "Internal network access", "Compliance with data residency requirements"],
    },

    "compliance_standards": {
        "FIPS 203": "ML-KEM — Quantum-safe key encapsulation. Our scanner checks if targets support ML-KEM hybrid key exchange.",
        "FIPS 204": "ML-DSA — Quantum-safe digital signatures. Scanner audits certificate signature algorithms.",
        "FIPS 205": "SLH-DSA — Hash-based digital signatures as alternative to lattice-based approaches.",
        "CNSA 2.0": "NSA's Commercial National Security Algorithm Suite 2.0 — timeline for quantum-safe migration by 2035.",
    },

    "buying_signals": [
        "Questions about internal network scanning",
        "Mentions of compliance requirements (NIST, CNSA, SOC2, ISO 27001)",
        "Asks about on-premises deployment",
        "Questions about team management or RBAC",
        "Mentions of CI/CD integration",
        "Asks about SLAs or dedicated support",
        "Questions about licensing or pricing",
        "Mentions 'our organization' or 'our company' or 'our infrastructure'",
    ],

    "ctas": {
        "demo": {
            "text": "Request a Custom Demo",
            "action": "navigate_to_page",
            "args": {"path": "/enterprise"},
        },
        "email": {
            "text": "Email Enterprise Team",
            "action": "open_email",
            "args": {"to": "quantc.info@gmail.com", "subject": "QuantCAI Enterprise Inquiry"},
        },
        "register_org": {
            "text": "Register Your Organization",
            "action": "navigate_to_page",
            "args": {"path": "/signup?plan=enterprise"},
        },
    },
}


# ---------------------------------------------------------------------------
# 4. DYNAMIC PROMPT ASSEMBLY — build_context_prompt()
# ---------------------------------------------------------------------------

def _get_current_module(route: str) -> Optional[dict]:
    """Look up the learning module for a given route."""
    # Normalize route
    clean = route.strip("/")
    if clean in LEARNING_CURRICULUM["modules"]:
        return LEARNING_CURRICULUM["modules"][clean]
    # Try matching partial routes
    for key, module in LEARNING_CURRICULUM["modules"].items():
        if module["route"].strip("/") == clean:
            return module
    return None


def _get_learning_path_position(route: str) -> str:
    """Return a string showing where the user is in the learning path."""
    path_order = LEARNING_CURRICULUM["path_order"]
    clean = route.strip("/")
    if clean in path_order:
        idx = path_order.index(clean)
        total = len(path_order)
        modules = []
        for i, mod_key in enumerate(path_order):
            mod = LEARNING_CURRICULUM["modules"].get(mod_key, {})
            marker = "→ " if i == idx else "  "
            status = "✅" if i < idx else ("📍" if i == idx else "⬜")
            modules.append(f"{marker}{status} {mod.get('title', mod_key)}")
        return "Learning Path Progress:\n" + "\n".join(modules)
    return ""


def build_context_prompt(
    route: Optional[str],
    tier: str,
    client_context: Optional[Dict[str, Any]] = None,
    user_role: Optional[str] = None,
) -> str:
    """
    Assemble a rich, context-specific system prompt based on the user's
    current state. This is appended to the base persona prompt.
    """
    sections = []
    route = route or "/"
    client_context = client_context or {}

    # -- Platform awareness (always included) --
    sections.append(
        "You are QuantAI, the AI assistant for the QuantCAI platform (https://quantcai.in). "
        "QuantCAI is an interactive quantum computing education and post-quantum cryptography compliance platform. "
        "You have deep knowledge of every page, tool, and feature on the platform."
    )

    # -- User tier awareness --
    tier_info = PLATFORM_KNOWLEDGE["pricing_tiers"].get(tier.lower(), {})
    if tier_info:
        sections.append(
            f"The user is on the '{tier_info.get('name', tier)}' plan. "
            f"Their plan includes: {', '.join(tier_info.get('features', [])[:5])}."
        )
        limitations = tier_info.get("limitations", [])
        if limitations:
            sections.append(
                f"Their plan does NOT include: {', '.join(limitations)}. "
                "If they ask about features not in their plan, explain the value and suggest upgrading."
            )

    # -- Route-specific context --
    # LEARNING PAGES
    if any(route.startswith(r) for r in ["/learn", "/quantum-computing"]):
        module = _get_current_module(route)
        if module:
            sections.append(f"\n--- CURRENT PAGE CONTEXT ---")
            sections.append(f"The user is currently on: {module['title']} ({module['route']})")
            sections.append(f"Topics covered on this page: {', '.join(module.get('topics', []))}")

            path_pos = _get_learning_path_position(route)
            if path_pos:
                sections.append(path_pos)

            # Quiz awareness
            quiz = module.get("quiz")
            if quiz:
                sections.append(
                    f"\nThis page has a quiz question: \"{quiz['question']}\"\n"
                    f"The correct answer is: {quiz['correct_answer']} (index {quiz['correct_index']})\n"
                    f"Teaching approach: {quiz.get('teaching_hint', 'Use Socratic method.')}\n"
                    f"IMPORTANT: Do NOT directly reveal the answer. Instead, guide the student "
                    f"to the correct answer using hints, analogies, and leading questions."
                )

            # Quiz state from client
            quiz_state = client_context.get("quiz_state")
            if quiz_state == "correct":
                sections.append("The student answered the quiz correctly! Congratulate them and suggest moving to the next module.")
            elif quiz_state == "incorrect":
                sections.append("The student answered the quiz incorrectly. Help them understand why their answer was wrong without directly giving the correct answer.")
            elif quiz_state == "unanswered":
                sections.append("The student has not attempted the quiz yet. Encourage them to try it after discussing the topic.")

            # Next steps
            next_mod = module.get("next_module")
            if next_mod and next_mod in LEARNING_CURRICULUM["modules"]:
                next_title = LEARNING_CURRICULUM["modules"][next_mod]["title"]
                next_route = LEARNING_CURRICULUM["modules"][next_mod]["route"]
                sections.append(f"Next module in the learning path: {next_title} ({next_route})")

            # Suggested tools
            suggested = module.get("suggested_tools", [])
            if suggested:
                tool_names = [PLATFORM_KNOWLEDGE["tools"].get(t, {}).get("name", t) for t in suggested]
                sections.append(f"Suggest the student try these tools for hands-on practice: {', '.join(tool_names)}")

            # Analogies
            analogies = module.get("key_analogies", [])
            if analogies:
                sections.append(f"Helpful analogies you can use: {' | '.join(analogies)}")

            # Exercises
            exercises = module.get("exercises", [])
            if exercises:
                sections.append(f"Suggested exercises: {' | '.join(exercises)}")

        sections.append(
            "\nAs a tutor on this learning page, your job is to:\n"
            "1. Teach using the Socratic method — ask what they know, build incrementally\n"
            "2. Reference the specific content on this page\n"
            "3. Use analogies to make abstract concepts tangible\n"
            "4. Suggest hands-on activities with platform tools\n"
            "5. Guide through quizzes without giving away answers\n"
            "6. Encourage progression through the learning path\n"
            "7. Use the navigate_to_page tool to guide users to relevant pages\n"
            "8. Use the suggest_learning_path tool to recommend the next step"
        )

    # CIRCUIT BUILDER
    elif route.startswith("/circuit-builder"):
        sections.append(f"\n--- CURRENT PAGE CONTEXT ---")
        sections.append("The user is on the Multi-Qubit Circuit Builder.")

        circuit_state = client_context.get("circuit_state", {})
        if circuit_state:
            sections.append(f"Current circuit state: {json.dumps(circuit_state)}")

        qubit_count = client_context.get("qubit_count")
        if qubit_count:
            sections.append(f"Active qubits: {qubit_count}")

        gate_count = client_context.get("gate_count")
        if gate_count is not None:
            sections.append(f"Total gates placed: {gate_count}")

        circuit_depth = client_context.get("circuit_depth")
        if circuit_depth is not None:
            sections.append(f"Circuit depth: {circuit_depth}")

        active_qasm = client_context.get("active_qasm")
        if active_qasm:
            sections.append(f"Current QASM code:\n```qasm\n{active_qasm}\n```")

        sections.append(
            f"\nAvailable gate library: "
            f"Single-qubit: {', '.join(PLATFORM_KNOWLEDGE['tools']['circuit_builder']['gate_library']['single_qubit'])} | "
            f"Multi-qubit: {', '.join(PLATFORM_KNOWLEDGE['tools']['circuit_builder']['gate_library']['multi_qubit'])}"
        )
        sections.append(
            f"Available templates: {', '.join(PLATFORM_KNOWLEDGE['tools']['circuit_builder']['templates'])}"
        )

        sections.append(
            "\nAs a circuit builder assistant, your job is to:\n"
            "1. Help design and optimize quantum circuits\n"
            "2. Explain what each gate does in the context of the user's circuit\n"
            "3. Suggest improvements or optimizations\n"
            "4. Use the manage_circuit tool to build circuits step by step\n"
            "5. Use the show_circuit_template tool to load predefined circuits\n"
            "6. Explain measurement results and probability distributions\n"
            "7. Help debug QASM syntax errors\n"
            "8. Relate circuit concepts back to theory from the learning modules"
        )

    # QUANTUM SIMULATOR
    elif route.startswith("/quantum-simulator") or route.startswith("/sandbox"):
        sections.append(f"\n--- CURRENT PAGE CONTEXT ---")
        sections.append("The user is on the Quantum Simulator (OpenQASM 2.0 code editor).")

        active_qasm = client_context.get("active_qasm")
        if active_qasm:
            sections.append(f"Current QASM code in editor:\n```qasm\n{active_qasm}\n```")

        sections.append(
            "\nAs a simulator assistant, your job is to:\n"
            "1. Help write valid OpenQASM 2.0 code\n"
            "2. Debug QASM syntax errors\n"
            "3. Explain circuit behavior and expected results\n"
            "4. Optimize gate sequences for efficiency\n"
            "5. Generate QASM code for requested algorithms"
        )

    # QUANTUM STATES VISUALIZER
    elif route.startswith("/quantum-states"):
        sections.append(f"\n--- CURRENT PAGE CONTEXT ---")
        sections.append("The user is on the Interactive Quantum States Visualizer (Bloch Sphere).")

        qubit_state = client_context.get("qubit_state")
        if qubit_state:
            sections.append(f"Current qubit state: α={qubit_state.get('alpha', '?')}, β={qubit_state.get('beta', '?')}")

        sections.append(
            "\nAs a visualizer assistant, your job is to:\n"
            "1. Explain the Bloch sphere representation\n"
            "2. Describe how each gate transforms the state\n"
            "3. Use the apply_gate_to_visualizer tool to demonstrate gate effects\n"
            "4. Connect visualizations to the math (amplitudes, probabilities, phase)\n"
            "5. Guide through a sequence of gate applications to build intuition"
        )

    # PQC SCANNER
    elif route.startswith("/pqc-scanner") or route.startswith("/repo-scanner"):
        sections.append(f"\n--- CURRENT PAGE CONTEXT ---")
        sections.append("The user is on the PQC Vulnerability Scanner.")

        scan_results = client_context.get("scan_results")
        if scan_results:
            sections.append(f"Latest scan results: {json.dumps(scan_results)}")

        scan_target = client_context.get("scan_target")
        if scan_target:
            sections.append(f"Last scanned target: {scan_target}")

        sections.append(
            f"\nPQC risk levels: {json.dumps(PLATFORM_KNOWLEDGE['tools']['pqc_scanner']['risk_levels'])}"
        )
        sections.append(
            f"\nCompliance standards: {json.dumps(ENTERPRISE_PLAYBOOK['compliance_standards'])}"
        )

        sections.append(
            "\nAs a security analyst, your job is to:\n"
            "1. Help users understand PQC scanner results\n"
            "2. Explain risk levels and what they mean practically\n"
            "3. Provide remediation recommendations based on scan findings\n"
            "4. Use the run_pqc_scan tool to scan domains when requested\n"
            "5. Explain NIST PQC standards (FIPS 203/204/205)\n"
            "6. Discuss migration strategies from RSA/ECC to ML-KEM/ML-DSA\n"
            "7. For enterprise needs (internal scanning, CI/CD integration), "
            "explain the CLI scanner and guide to the Enterprise page"
        )

    # ENTERPRISE PAGE
    elif route.startswith("/enterprise"):
        sections.append(f"\n--- CURRENT PAGE CONTEXT ---")
        sections.append("The user is on the Enterprise page.")
        sections.append(f"\nCLI Scanner details: {json.dumps(ENTERPRISE_PLAYBOOK['cli_scanner'])}")
        sections.append(f"\nOn-Prem deployment: {json.dumps(ENTERPRISE_PLAYBOOK['on_prem_deployment'])}")
        sections.append(f"\nCompliance standards: {json.dumps(ENTERPRISE_PLAYBOOK['compliance_standards'])}")

        sections.append(
            "\nAs an enterprise advisor, your job is to:\n"
            "1. Explain QuantCAI's enterprise offerings in detail\n"
            "2. Answer questions about the CLI scanner, on-prem deployment, compliance\n"
            "3. Discuss licensing models and custom SLAs\n"
            "4. Guide users to contact quantc.info@gmail.com for custom demos and pricing\n"
            "5. Use the recommend_enterprise_action tool to show CTAs (email, demo, register)\n"
            "6. Highlight differentiators vs. the free/pro plans"
        )

    # DEFAULT / OTHER PAGES
    else:
        sections.append(
            f"\nThe user is currently on: {PLATFORM_KNOWLEDGE['navigation'].get(route, route)}\n"
            "Provide helpful, contextual assistance based on what they might be looking at."
        )

    # -- Enterprise detection for ANY page --
    if tier.lower() == "enterprise" or user_role in ("enterprise_user", "root"):
        sections.append(
            "\n--- ENTERPRISE USER DETECTED ---\n"
            "This is an enterprise user. You are the LQM (Large Quantitative Model) Compliance Advisor.\n"
            "Focus on professional, enterprise-grade responses about PQC compliance, "
            "cryptographic risk management, and organizational migration strategies.\n"
            "You can reference CLI scanner capabilities, on-prem deployment options, and compliance standards."
        )

    # -- Cross-sell / upsell intelligence --
    if tier.lower() == "free":
        sections.append(
            "\n--- UPGRADE AWARENESS ---\n"
            "When the user asks about features not available on the free plan, briefly explain "
            "the feature's value and mention that it's available on Pro ($9.99/mo) or Enterprise plans. "
            "Be helpful first, sell second. Never block help — always answer the question, then mention the upgrade path."
        )

    # -- Always include available tools --
    sections.append(
        "\n--- AVAILABLE TOOLS ---\n"
        "You have these tools to control the UI and help users:\n"
        "- open_tool(tool_name): Opens a tool. Values: 'quantum-states', 'circuit-builder', 'pqc-scanner'\n"
        "- manage_circuit(action, params): Build circuits. Actions: 'add_gate', 'clear', 'run'\n"
        "- navigate_to_page(path, section): Navigate to any page. Paths: /learn, /learn/qubits, /learn/gates, /learn/pqc, /circuit-builder, /quantum-states, /pqc-scanner, /enterprise, /tools, /quantum-simulator\n"
        "- suggest_learning_path(current_topic): Recommend next learning step in the curriculum\n"
        "- explain_quiz_hint(page, question_index): Give a Socratic hint for a quiz question\n"
        "- show_circuit_template(template_name): Load a circuit template. Templates: bell-state, ghz-state, teleportation, grovers, bernstein-vazirani, qft, deutsch-jozsa, superdense-coding\n"
        "- run_pqc_scan(target_url): Scan a domain for PQC vulnerabilities\n"
        "- apply_gate_to_visualizer(gate): Apply a gate to the Bloch sphere visualizer\n"
        "- recommend_enterprise_action(action_type): Show enterprise CTAs. Types: 'demo', 'email', 'register_org'\n"
        "\nUse tools proactively to make the experience interactive. Don't just describe — demonstrate!"
    )

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# 5. DYNAMIC SUGGESTION GENERATION
# ---------------------------------------------------------------------------

def get_suggestions_for_route(route: str, tier: str, client_context: Optional[Dict[str, Any]] = None) -> list:
    """Return contextual suggestion chips for the AI assistant UI."""
    route = route or "/"
    client_context = client_context or {}

    if route.startswith("/learn/pqc"):
        return ["What is ML-KEM?", "How does Shor's algorithm break RSA?", "Scan a domain for PQC readiness"]
    elif route.startswith("/learn/gates"):
        return ["Build a Bell State circuit", "What does the Hadamard gate do?", "Show me gate matrices"]
    elif route.startswith("/learn/qubits"):
        return ["Explain superposition with an analogy", "What is the Bloch sphere?", "Show me on the visualizer"]
    elif route.startswith("/learn") or route.startswith("/quantum-computing"):
        return ["What is a qubit?", "Start the learning path", "Show me the circuit builder"]
    elif route.startswith("/circuit-builder"):
        suggestions = ["Explain my circuit", "Build a Bell State", "Optimize gate count"]
        if client_context.get("gate_count", 0) > 0:
            suggestions[0] = "Analyze my current circuit"
        return suggestions
    elif route.startswith("/quantum-states"):
        return ["What is superposition?", "Apply Hadamard gate", "Explain the Bloch sphere"]
    elif route.startswith("/quantum-simulator") or route.startswith("/sandbox"):
        return ["Write a Bell State in QASM", "Debug my code", "Explain OpenQASM syntax"]
    elif route.startswith("/pqc-scanner") or route.startswith("/repo-scanner"):
        suggestions = ["What is PQC?", "Explain FIPS 203", "How to migrate from RSA?"]
        if client_context.get("scan_results"):
            suggestions = ["Interpret my scan results", "What should I fix first?", "Generate remediation plan"]
        return suggestions
    elif route.startswith("/enterprise"):
        return ["Tell me about the CLI scanner", "On-prem deployment options", "Contact the team"]
    elif route == "/tools":
        return ["What tools are available?", "Help me choose a tool", "Start learning quantum computing"]
    else:
        if tier.lower() == "enterprise":
            return ["Run a PQC compliance scan", "Review our cryptographic posture", "Generate migration roadmap"]
        return ["Teach me quantum computing", "Build a quantum circuit", "What is PQC?"]


def get_welcome_message(route: str, tier: str, client_context: Optional[Dict[str, Any]] = None) -> str:
    """Return a context-aware welcome message for the AI assistant."""
    route = route or "/"
    client_context = client_context or {}

    if tier.lower() == "enterprise":
        if route.startswith("/pqc-scanner"):
            return "I'm your LQM Compliance Advisor. I can help interpret scan results, assess your PQC readiness, and draft remediation strategies. Paste a domain or share your latest scan."
        elif route.startswith("/enterprise"):
            return "Welcome to QuantCAI Enterprise. I can walk you through our on-prem deployment, CLI scanner for internal networks, compliance capabilities, and custom SLA options."
        else:
            return "I'm the LQM — your enterprise PQC compliance advisor. Ask me about cryptographic risk assessment, migration planning, or compliance standards."

    module = _get_current_module(route)
    if module:
        return f"I can see you're studying **{module['title']}**. Ask me anything about the topics here, or I can quiz you to test your understanding!"

    if route.startswith("/circuit-builder"):
        gate_count = client_context.get("gate_count", 0)
        if gate_count > 0:
            return f"I can see your circuit has **{gate_count} gates**. Want me to analyze it, suggest optimizations, or explain what it does?"
        return "Ready to build quantum circuits! I can help you design, explain, and optimize. Try asking me to build a Bell State or load a template."

    if route.startswith("/quantum-states"):
        return "Welcome to the Bloch Sphere Visualizer! I can apply gates and explain how they transform the quantum state. Try asking me to demonstrate superposition."

    if route.startswith("/quantum-simulator") or route.startswith("/sandbox"):
        return "I can help you write, debug, and understand OpenQASM 2.0 code. Paste your code or describe the circuit you want to build."

    if route.startswith("/pqc-scanner"):
        return "I can help assess domains for quantum-vulnerable cryptography. Enter a domain to scan, or ask me about PQC standards and migration strategies."

    if route.startswith("/tools"):
        return "Here are all the quantum tools available. I can help you choose the right one or guide you through using any of them."

    return ("I'm your Quantum Computing assistant. I can teach you quantum concepts, build circuits, "
            "scan for PQC vulnerabilities, and help you navigate the platform. What would you like to explore?")
