import { gates } from '@/components/GatePalette';
import { GateType, PlacedGate } from '@/types/circuit';

export interface CircuitTemplate {
    category: string;
    label: string;
    qubits: number;
    fn: () => PlacedGate[];
}

function generateUID(prefix: string) {
    return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

function getGate(id: string): GateType {
    const gate = gates.find(g => g.id === id);
    if (!gate) throw new Error(`Gate ${id} not found in palette`);
    return gate;
}

// ─── Existing Templates ──────────────────────────────────────────────

function createBellState(): PlacedGate[] {
    const h = getGate('h');
    const cx = getGate('cx');
    return [
        { ...h, uid: generateUID('bell-h'), wire: 0, step: 0 },
        { ...cx, uid: generateUID('bell-cx'), wire: 0, targetWire: 1, step: 1 },
    ];
}

function createQuantumTeleportation(): PlacedGate[] {
    const h = getGate('h');
    const cx = getGate('cx');
    const rx = getGate('rx');
    const cz = getGate('cz');
    return [
        { ...rx, uid: generateUID('t-rx'), wire: 0, step: 0, params: [Math.PI / 3] },
        { ...h, uid: generateUID('t-h1'), wire: 1, step: 0 },
        { ...cx, uid: generateUID('t-cx1'), wire: 1, targetWire: 2, step: 1 },
        { ...cx, uid: generateUID('t-cx2'), wire: 0, targetWire: 1, step: 2 },
        { ...h, uid: generateUID('t-h2'), wire: 0, step: 3 },
        { ...cx, uid: generateUID('t-cx3'), wire: 1, targetWire: 2, step: 4 },
        { ...cz, uid: generateUID('t-cz1'), wire: 0, targetWire: 2, step: 5 },
    ];
}

function createGroversSearch(): PlacedGate[] {
    const h = getGate('h');
    const cz = getGate('cz');
    const x = getGate('x');
    return [
        { ...h, uid: generateUID('g-h0'), wire: 0, step: 0 },
        { ...h, uid: generateUID('g-h1'), wire: 1, step: 0 },
        { ...cz, uid: generateUID('g-cz'), wire: 0, targetWire: 1, step: 1 },
        { ...h, uid: generateUID('g-h2'), wire: 0, step: 2 },
        { ...h, uid: generateUID('g-h3'), wire: 1, step: 2 },
        { ...x, uid: generateUID('g-x0'), wire: 0, step: 3 },
        { ...x, uid: generateUID('g-x1'), wire: 1, step: 3 },
        { ...cz, uid: generateUID('g-cz2'), wire: 0, targetWire: 1, step: 4 },
        { ...x, uid: generateUID('g-x2'), wire: 0, step: 5 },
        { ...x, uid: generateUID('g-x3'), wire: 1, step: 5 },
        { ...h, uid: generateUID('g-h4'), wire: 0, step: 6 },
        { ...h, uid: generateUID('g-h5'), wire: 1, step: 6 },
    ];
}

// ─── New: Information Theory ─────────────────────────────────────────

function createSuperdenseCoding(): PlacedGate[] {
    const h = getGate('h');
    const cx = getGate('cx');
    const x = getGate('x');
    const z = getGate('z');
    
    // Entanglement (Alice & Bob)
    return [
        { ...h, uid: generateUID('sd-h0'), wire: 0, step: 0 },
        { ...cx, uid: generateUID('sd-cx0'), wire: 0, targetWire: 1, step: 1 },
        // Encode "11"
        { ...x, uid: generateUID('sd-x0'), wire: 0, step: 2 },
        { ...z, uid: generateUID('sd-z0'), wire: 0, step: 3 },
        // Decode
        { ...cx, uid: generateUID('sd-cx1'), wire: 0, targetWire: 1, step: 4 },
        { ...h, uid: generateUID('sd-h1'), wire: 0, step: 5 },
    ];
}

function createGHZState(): PlacedGate[] {
    const h = getGate('h');
    const cx = getGate('cx');
    return [
        { ...h, uid: generateUID('ghz-h0'), wire: 0, step: 0 },
        { ...cx, uid: generateUID('ghz-cx0'), wire: 0, targetWire: 1, step: 1 },
        { ...cx, uid: generateUID('ghz-cx1'), wire: 1, targetWire: 2, step: 2 },
    ];
}

function createWState(): PlacedGate[] {
    const ry = getGate('ry');
    const h = getGate('h');
    const cx = getGate('cx');
    const x = getGate('x');
    const theta = 2 * Math.acos(1 / Math.sqrt(3));
    return [
        { ...ry, uid: generateUID('w-ry'), wire: 0, step: 0, params: [theta] },
        { ...h, uid: generateUID('w-h'), wire: 1, step: 1 },
        { ...cx, uid: generateUID('w-cx0'), wire: 1, targetWire: 2, step: 2 },
        { ...cx, uid: generateUID('w-cx1'), wire: 0, targetWire: 1, step: 3 },
        { ...x, uid: generateUID('w-x'), wire: 0, step: 4 },
        { ...cx, uid: generateUID('w-cx2'), wire: 0, targetWire: 2, step: 5 },
    ];
}

// ─── New: Algorithmic Speedups (Classic Algorithms) ─────────────────

function createDeutschJozsa(): PlacedGate[] {
    const h = getGate('h');
    const x = getGate('x');
    const cx = getGate('cx');
    return [
        { ...x, uid: generateUID('dj-x'), wire: 2, step: 0 },
        { ...h, uid: generateUID('dj-h0'), wire: 0, step: 1 },
        { ...h, uid: generateUID('dj-h1'), wire: 1, step: 1 },
        { ...h, uid: generateUID('dj-h2'), wire: 2, step: 1 },
        // Balanced Oracle: CNOTs
        { ...cx, uid: generateUID('dj-cx0'), wire: 0, targetWire: 2, step: 2 },
        { ...cx, uid: generateUID('dj-cx1'), wire: 1, targetWire: 2, step: 3 },
        // Measure
        { ...h, uid: generateUID('dj-h3'), wire: 0, step: 4 },
        { ...h, uid: generateUID('dj-h4'), wire: 1, step: 4 },
    ];
}

function createBernsteinVazirani(): PlacedGate[] {
    const h = getGate('h');
    const x = getGate('x');
    const cx = getGate('cx');
    // Secret string s = 101
    return [
        { ...x, uid: generateUID('bv-x'), wire: 3, step: 0 },
        { ...h, uid: generateUID('bv-h0'), wire: 0, step: 1 },
        { ...h, uid: generateUID('bv-h1'), wire: 1, step: 1 },
        { ...h, uid: generateUID('bv-h2'), wire: 2, step: 1 },
        { ...h, uid: generateUID('bv-h3'), wire: 3, step: 1 },
        // Oracle for s=101
        { ...cx, uid: generateUID('bv-cx0'), wire: 0, targetWire: 3, step: 2 },
        { ...cx, uid: generateUID('bv-cx2'), wire: 2, targetWire: 3, step: 3 },
        // Measure
        { ...h, uid: generateUID('bv-h4'), wire: 0, step: 4 },
        { ...h, uid: generateUID('bv-h5'), wire: 1, step: 4 },
        { ...h, uid: generateUID('bv-h6'), wire: 2, step: 4 },
    ];
}

function createQFT3(): PlacedGate[] {
    const h = getGate('h');
    const cz = getGate('cz'); // using CZ as a proxy for CPhase
    const swap = getGate('swap');
    return [
        { ...h, uid: generateUID('qft-h0'), wire: 2, step: 0 },
        { ...cz, uid: generateUID('qft-cz0'), wire: 1, targetWire: 2, step: 1 },
        { ...cz, uid: generateUID('qft-cz1'), wire: 0, targetWire: 2, step: 2 },
        { ...h, uid: generateUID('qft-h1'), wire: 1, step: 3 },
        { ...cz, uid: generateUID('qft-cz2'), wire: 0, targetWire: 1, step: 4 },
        { ...h, uid: generateUID('qft-h2'), wire: 0, step: 5 },
        { ...swap, uid: generateUID('qft-swap'), wire: 0, targetWire: 2, step: 6 },
    ];
}

function createShor(): PlacedGate[] {
    const h = getGate('h');
    const x = getGate('x');
    const cx = getGate('cx');
    // Simplified period-finding circuit for N=15, 2x3 multiplier
    // Requires at least 5 qubits
    return [
        { ...h, uid: generateUID('shor-h0'), wire: 0, step: 0 },
        { ...h, uid: generateUID('shor-h1'), wire: 1, step: 0 },
        { ...h, uid: generateUID('shor-h2'), wire: 2, step: 0 },
        { ...x, uid: generateUID('shor-x'), wire: 4, step: 0 }, // Setup eigenstate
        // Modular exponentiation (simplified mock)
        { ...cx, uid: generateUID('shor-cx0'), wire: 2, targetWire: 3, step: 1 },
        { ...cx, uid: generateUID('shor-cx1'), wire: 2, targetWire: 4, step: 2 },
        // Inverse QFT on first 3 qubits (mock)
        { ...h, uid: generateUID('shor-h3'), wire: 0, step: 3 },
        { ...h, uid: generateUID('shor-h4'), wire: 1, step: 4 },
        { ...h, uid: generateUID('shor-h5'), wire: 2, step: 5 },
    ];
}

// ─── New: Advanced Subroutines ───────────────────────────────────────

function createQPE(): PlacedGate[] {
    const h = getGate('h');
    const x = getGate('x');
    const cx = getGate('cx');
    // 3 counting, 1 eigenstate
    return [
        { ...x, uid: generateUID('qpe-x'), wire: 3, step: 0 },
        { ...h, uid: generateUID('qpe-h0'), wire: 0, step: 1 },
        { ...h, uid: generateUID('qpe-h1'), wire: 1, step: 1 },
        { ...h, uid: generateUID('qpe-h2'), wire: 2, step: 1 },
        // Controlled unitaries (mock using CX)
        { ...cx, uid: generateUID('qpe-cu0'), wire: 2, targetWire: 3, step: 2 },
        { ...cx, uid: generateUID('qpe-cu1'), wire: 1, targetWire: 3, step: 3 },
        { ...cx, uid: generateUID('qpe-cu2'), wire: 0, targetWire: 3, step: 4 },
        // Inverse QFT (mock)
        { ...h, uid: generateUID('qpe-hq0'), wire: 0, step: 5 },
        { ...h, uid: generateUID('qpe-hq1'), wire: 1, step: 6 },
        { ...h, uid: generateUID('qpe-hq2'), wire: 2, step: 7 },
    ];
}

function createBitFlipErrorCorrection(): PlacedGate[] {
    const h = getGate('h');
    const cx = getGate('cx');
    const ccx = getGate('ccx');
    return [
        // Prepare arbitrary state
        { ...h, uid: generateUID('bf-h'), wire: 0, step: 0 },
        // Encode
        { ...cx, uid: generateUID('bf-en0'), wire: 0, targetWire: 1, step: 1 },
        { ...cx, uid: generateUID('bf-en1'), wire: 0, targetWire: 2, step: 2 },
        // Error (mock error on wire 1)
        { ...getGate('x'), uid: generateUID('bf-err'), wire: 1, step: 3 },
        // Decode / Syndrome
        { ...cx, uid: generateUID('bf-de0'), wire: 0, targetWire: 1, step: 4 },
        { ...cx, uid: generateUID('bf-de1'), wire: 0, targetWire: 2, step: 5 },
        // Correct
        { ...ccx, uid: generateUID('bf-ccx'), wire: 1, targetWire: 0, thirdWire: 2, step: 6 },
    ];
}

// ─── New: Enterprise Ansätze ─────────────────────────────────────────

function createVQEHardwareEfficient(): PlacedGate[] {
    const ry = getGate('ry');
    const cx = getGate('cx');
    return [
        { ...ry, uid: generateUID('vqe-ry0'), wire: 0, step: 0, params: [Math.PI/4] },
        { ...ry, uid: generateUID('vqe-ry1'), wire: 1, step: 0, params: [Math.PI/4] },
        { ...ry, uid: generateUID('vqe-ry2'), wire: 2, step: 0, params: [Math.PI/4] },
        { ...ry, uid: generateUID('vqe-ry3'), wire: 3, step: 0, params: [Math.PI/4] },
        { ...cx, uid: generateUID('vqe-cx0'), wire: 0, targetWire: 1, step: 1 },
        { ...cx, uid: generateUID('vqe-cx1'), wire: 1, targetWire: 2, step: 2 },
        { ...cx, uid: generateUID('vqe-cx2'), wire: 2, targetWire: 3, step: 3 },
        { ...cx, uid: generateUID('vqe-cx3'), wire: 3, targetWire: 0, step: 4 },
    ];
}

function createQAOA(): PlacedGate[] {
    const h = getGate('h');
    const cx = getGate('cx');
    const rz = getGate('rz');
    const rx = getGate('rx');
    return [
        { ...h, uid: generateUID('qaoa-h0'), wire: 0, step: 0 },
        { ...h, uid: generateUID('qaoa-h1'), wire: 1, step: 0 },
        { ...h, uid: generateUID('qaoa-h2'), wire: 2, step: 0 },
        // Cost Hamiltonian
        { ...cx, uid: generateUID('qaoa-cx0'), wire: 0, targetWire: 1, step: 1 },
        { ...rz, uid: generateUID('qaoa-rz0'), wire: 1, step: 2, params: [Math.PI/3] },
        { ...cx, uid: generateUID('qaoa-cx1'), wire: 0, targetWire: 1, step: 3 },
        // Mixer Hamiltonian
        { ...rx, uid: generateUID('qaoa-rx0'), wire: 0, step: 4, params: [Math.PI/2] },
        { ...rx, uid: generateUID('qaoa-rx1'), wire: 1, step: 4, params: [Math.PI/2] },
        { ...rx, uid: generateUID('qaoa-rx2'), wire: 2, step: 4, params: [Math.PI/2] },
    ];
}

export const TEMPLATES: CircuitTemplate[] = [
    // Information Theory
    { category: 'Information Theory', label: 'Bell State', qubits: 2, fn: createBellState },
    { category: 'Information Theory', label: 'Quantum Teleportation', qubits: 3, fn: createQuantumTeleportation },
    { category: 'Information Theory', label: 'Superdense Coding', qubits: 2, fn: createSuperdenseCoding },
    { category: 'Information Theory', label: 'GHZ State (3-Qubit)', qubits: 3, fn: createGHZState },
    { category: 'Information Theory', label: 'W State (3-Qubit)', qubits: 3, fn: createWState },
    
    // Algorithmic Speedups
    { category: 'Algorithmic Speedups', label: 'Deutsch-Jozsa (Balanced)', qubits: 3, fn: createDeutschJozsa },
    { category: 'Algorithmic Speedups', label: 'Bernstein-Vazirani', qubits: 4, fn: createBernsteinVazirani },
    { category: 'Algorithmic Speedups', label: '3-Qubit QFT', qubits: 3, fn: createQFT3 },
    { category: 'Algorithmic Speedups', label: "Grover's Search (2 Qubits)", qubits: 2, fn: createGroversSearch },
    { category: 'Algorithmic Speedups', label: "Shor's Algorithm (Simplified)", qubits: 5, fn: createShor },
    
    // Advanced Subroutines
    { category: 'Advanced Subroutines', label: 'Quantum Phase Estimation', qubits: 4, fn: createQPE },
    { category: 'Advanced Subroutines', label: '3-Qubit Bit-Flip Error Correction', qubits: 3, fn: createBitFlipErrorCorrection },
    
    // Enterprise Ansätze
    { category: 'Enterprise Ansätze', label: 'VQE Hardware-Efficient Ansatz', qubits: 4, fn: createVQEHardwareEfficient },
    { category: 'Enterprise Ansätze', label: 'QAOA Ansatz', qubits: 3, fn: createQAOA },
];
