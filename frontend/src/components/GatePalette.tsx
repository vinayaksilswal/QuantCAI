import { useDraggable } from '@dnd-kit/core';
import { Target, RotateCw, Zap, Shuffle, ArrowRight, Activity, GitCommit, Move, Maximize } from 'lucide-react';
import { GateType } from '@/types/circuit';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

export const gates: GateType[] = [
    // Single Qubit
    { id: 'h', name: 'H', label: 'Hadamard', icon: Shuffle, color: 'from-blue-500 to-blue-600', description: 'Creates superposition. |0> -> (|0>+|1>)/√2', category: 'single', qubits: 1 },
    { id: 'x', name: 'X', label: 'Pauli-X', icon: Target, color: 'from-red-500 to-red-600', description: 'Bit flip (NOT gate). |0> -> |1>', category: 'single', qubits: 1 },
    { id: 'y', name: 'Y', label: 'Pauli-Y', icon: RotateCw, color: 'from-green-500 to-green-600', description: 'Bit and phase flip.', category: 'single', qubits: 1 },
    { id: 'z', name: 'Z', label: 'Pauli-Z', icon: Zap, color: 'from-purple-500 to-purple-600', description: 'Phase flip. |1> -> -|1>', category: 'phase', qubits: 1 },
    { id: 's', name: 'S', label: 'Phase S', icon: Activity, color: 'from-purple-400 to-purple-500', description: '90 degree phase shift.', category: 'phase', qubits: 1 },
    { id: 't', name: 'T', label: 'Phase T', icon: Activity, color: 'from-purple-300 to-purple-400', description: '45 degree phase shift.', category: 'phase', qubits: 1 },

    // Multi Qubit
    { id: 'cx', name: 'CX', label: 'CNOT', icon: ArrowRight, color: 'from-orange-500 to-orange-600', description: 'Controlled-NOT. Flips target if control is |1>.', category: 'multi', qubits: 2 },
    { id: 'cz', name: 'CZ', label: 'Controlled-Z', icon: GitCommit, color: 'from-teal-500 to-teal-600', description: 'Controlled phase flip.', category: 'multi', qubits: 2 },
    { id: 'swap', name: 'SWAP', label: 'Swap', icon: Move, color: 'from-pink-500 to-pink-600', description: 'Swaps states of two qubits.', category: 'multi', qubits: 2 },
    { id: 'ccx', name: 'CCX', label: 'Toffoli', icon: Maximize, color: 'from-orange-600 to-red-600', description: 'Controlled-Controlled-NOT.', category: 'multi', qubits: 3 },

    // Parameterized (Simplified for drag-drop, defaults to pi/2 or similar, needs modal to edit)
    { id: 'rx', name: 'RX', label: 'RX', icon: RotateCw, color: 'from-indigo-500 to-indigo-600', description: 'Rotation around X axis.', category: 'single', qubits: 1 },
    { id: 'ry', name: 'RY', label: 'RY', icon: RotateCw, color: 'from-indigo-500 to-indigo-600', description: 'Rotation around Y axis.', category: 'single', qubits: 1 },
    { id: 'rz', name: 'RZ', label: 'RZ', icon: RotateCw, color: 'from-indigo-500 to-indigo-600', description: 'Rotation around Z axis.', category: 'single', qubits: 1 },
];

export const GatePalette = () => {
    // Group by category
    const categories = {
        'single': gates.filter(g => g.category === 'single'),
        'phase': gates.filter(g => g.category === 'phase'),
        'multi': gates.filter(g => g.category === 'multi'),
    };

    return (
        <div className="space-y-4">
            {Object.entries(categories).map(([cat, catGates]) => (
                <div key={cat}>
                    <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">{cat} Qubit Gates</h3>
                    <div className="grid grid-cols-3 gap-2">
                        {catGates.map(gate => (
                            <DraggableGate key={gate.id} gate={gate} />
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
};

const DraggableGate = ({ gate }: { gate: GateType }) => {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({
        id: `gate-${gate.id}`,
        data: gate
    });

    const style = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: 999,
    } : undefined;

    const Icon = gate.icon;

    return (
        <TooltipProvider>
            <Tooltip>
                <TooltipTrigger asChild>
                    <div ref={setNodeRef} style={style} {...listeners} {...attributes} className={`
                        p-2 rounded-lg bg-gradient-to-br ${gate.color} 
                        flex flex-col items-center justify-center gap-1
                        cursor-grab active:cursor-grabbing shadow-lg 
                        border border-white/10
                        hover:scale-105 transition-transform h-16
                    `}>
                        <Icon className="w-5 h-5 text-white" />
                        <span className="text-[10px] font-bold font-mono text-white/90">{gate.name}</span>
                    </div>
                </TooltipTrigger>
                <TooltipContent side="right" className="bg-slate-900 border-slate-700">
                    <p className="font-bold text-blue-200">{gate.label}</p>
                    <p className="text-xs text-slate-400">{gate.description}</p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
};
