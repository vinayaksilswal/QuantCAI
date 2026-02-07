export type GateType = {
    id: string;
    name: string; // e.g. "H", "CNOT", "X"
    label: string;
    icon: any; // Lucide icon or custom SVG
    color: string;
    description: string;
    category: 'single' | 'multi' | 'phase' | 'measurement';
    qubits: number; // Number of qubits this gate affects (1, 2, 3)
};

export type PlacedGate = GateType & {
    uid: string;
    wire: number; // The primary wire (target for single, control for CNOT usually)
    step: number;
    targetWire?: number; // For multi-qubit gates, the second wire (if applicable)
    params?: number[]; // For parameterized gates
};
