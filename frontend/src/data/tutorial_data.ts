
export type TutorialStep = {
    title: string;
    description: string;
    targetGate: string; // name of gate, e.g., 'H'
    targetWire: number;
    targetStep: number;
    hint?: string;
};

export type TutorialScenario = {
    id: string;
    title: string;
    steps: TutorialStep[];
};

export const tutorialScenarios: TutorialScenario[] = [
    {
        id: "bell-state",
        title: "Create a Bell State",
        steps: [
            {
                title: "Step 1: Superposition",
                description: "Drag a Hadamard (H) gate to Qubit 0. This creates a superposition state (|0> + |1>).",
                targetGate: "H",
                targetWire: 0,
                targetStep: 0,
                hint: "Find the 'H' gate in the Single Qubit section."
            },
            {
                title: "Step 2: Entanglement",
                description: "Drag a CNOT (CX) gate to Qubit 0 (Control). It will automatically target Qubit 1.",
                targetGate: "CX",
                targetWire: 0,
                targetStep: 1, // Next step
                hint: "CNOT creates entanglement between the two qubits."
            }
        ]
    },
    {
        id: "teleportation",
        title: "Quantum Teleportation",
        steps: [
            {
                title: "Step 1: Entangle Pair",
                description: "Create an entangled pair between Alice (q1) and Bob (q2). Place H on q[1].",
                targetGate: "H",
                targetWire: 1,
                targetStep: 0
            },
            {
                title: "Step 2: CNOT",
                description: "Place CNOT control on q[1], target q[2].",
                targetGate: "CX",
                targetWire: 1,
                targetStep: 1
            },
            // ... truncated for brevity in this initial pass
        ]
    }
];
