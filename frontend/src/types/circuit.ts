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
    thirdWire?: number; // For CCX (Toffoli), the third wire
    params?: number[]; // For parameterized gates
};

// V1 Enterprise Types

export type ExecutionBackend = 'local' | 'aws_braket' | 'ibm_quantum';

export interface CircuitTelemetry {
    circuitDepth: number;
    totalGates: number;
    estimatedQPUCost: string; // formatted string like "$0.0015"
    activeQubits: number;
}

export interface GateInstructionPayload {
    name: string;
    qubits: number[];
    params: number[];
}

export interface V1SimulateRequest {
    num_qubits: number;
    shots: number;
    gates: GateInstructionPayload[];
    use_noise: boolean;
}

export interface V1ExportRequest {
    num_qubits: number;
    gates: GateInstructionPayload[];
}

export interface CircuitMetrics {
    depth: number;
    gate_count: Record<string, number>;
    qubit_count: number;
}

export interface StatevectorEntry {
    basis: string;
    amplitude: { real: number; imag: number };
    probability: number;
    phase: number;
}

export interface V1SimulationResult {
    type: 'ideal' | 'noisy';
    probabilities: Record<string, number>;
    statevector?: StatevectorEntry[] | null;
    metrics: CircuitMetrics;
    execution_time_ms?: number;
}

export interface V1ExportResult {
    qasm: string;
    version: string;
    num_qubits: number;
    num_gates: number;
}
