import { useState } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { Target, RotateCw, Zap, Shuffle, ArrowRight, Activity, GitCommit, Move, Maximize, Search } from 'lucide-react';
import { GateType } from '@/types/circuit';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

export const gates: GateType[] = [
    // Single Qubit Gates
    { id: 'h', name: 'H', label: 'Hadamard', icon: Shuffle, color: 'from-blue-500 to-blue-600', description: 'Creates superposition. |0⟩ → (|0⟩+|1⟩)/√2', category: 'single', qubits: 1 },
    { id: 'x', name: 'X', label: 'Pauli-X', icon: Target, color: 'from-red-500 to-red-600', description: 'Bit flip (NOT gate). |0⟩ → |1⟩', category: 'single', qubits: 1 },
    { id: 'y', name: 'Y', label: 'Pauli-Y', icon: RotateCw, color: 'from-green-500 to-green-600', description: 'Bit and phase flip.', category: 'single', qubits: 1 },

    // Phase Qubit Gates
    { id: 'z', name: 'Z', label: 'Pauli-Z', icon: Zap, color: 'from-purple-500 to-purple-600', description: 'Phase flip. |1⟩ → -|1⟩', category: 'phase', qubits: 1 },
    { id: 's', name: 'S', label: 'Phase S', icon: Activity, color: 'from-purple-400 to-purple-500', description: '90° phase shift (√Z).', category: 'phase', qubits: 1 },
    { id: 't', name: 'T', label: 'Phase T', icon: Activity, color: 'from-purple-300 to-purple-400', description: '45° phase shift (√S).', category: 'phase', qubits: 1 },
    { id: 'rx', name: 'RX', label: 'RX(π/2)', icon: RotateCw, color: 'from-indigo-500 to-indigo-600', description: 'Rotation around X axis by π/2.', category: 'phase', qubits: 1 },
    { id: 'ry', name: 'RY', label: 'RY(π/2)', icon: RotateCw, color: 'from-indigo-400 to-indigo-500', description: 'Rotation around Y axis by π/2.', category: 'phase', qubits: 1 },
    { id: 'rz', name: 'RZ', label: 'RZ(π/2)', icon: RotateCw, color: 'from-indigo-300 to-indigo-400', description: 'Rotation around Z axis by π/2.', category: 'phase', qubits: 1 },

    // Multi Qubit Gates
    { id: 'cx', name: 'CX', label: 'CNOT', icon: ArrowRight, color: 'from-orange-500 to-orange-600', description: 'Controlled-NOT. Flips target if control is |1⟩.', category: 'multi', qubits: 2 },
    { id: 'cz', name: 'CZ', label: 'Controlled-Z', icon: GitCommit, color: 'from-teal-500 to-teal-600', description: 'Controlled phase flip.', category: 'multi', qubits: 2 },
    { id: 'swap', name: 'SWAP', label: 'Swap', icon: Move, color: 'from-pink-500 to-pink-600', description: 'Swaps states of two qubits.', category: 'multi', qubits: 2 },
    { id: 'ccx', name: 'CCX', label: 'Toffoli', icon: Maximize, color: 'from-orange-600 to-red-600', description: 'Controlled-Controlled-NOT (Toffoli).', category: 'multi', qubits: 3 },
];

const CATEGORY_CONFIG = {
    single: { label: 'SINGLE QUBIT GATES', order: 0 },
    phase: { label: 'PHASE QUBIT GATES', order: 1 },
    multi: { label: 'MULTI QUBIT GATES', order: 2 },
} as const;

export const GatePalette = () => {
    const [searchQuery, setSearchQuery] = useState('');

    const filteredGates = searchQuery.trim()
        ? gates.filter(g =>
            g.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            g.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
            g.description.toLowerCase().includes(searchQuery.toLowerCase())
        )
        : gates;

    // Group by category in specified order
    const categories = Object.entries(CATEGORY_CONFIG)
        .sort(([, a], [, b]) => a.order - b.order)
        .map(([cat, config]) => ({
            key: cat,
            label: config.label,
            gates: filteredGates.filter(g => g.category === cat),
        }))
        .filter(c => c.gates.length > 0);

    return (
        <div className="space-y-4">
            {/* Search */}
            <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                <input
                    type="text"
                    placeholder="Search gates..."
                    value={searchQuery}
                    onChange={e => setSearchQuery(e.target.value)}
                    className="w-full pl-8 pr-3 py-2 bg-slate-800/60 border border-slate-700/50 rounded-lg text-xs text-slate-300 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all"
                />
            </div>

            {/* Gate Categories */}
            {categories.map(({ key, label, gates: catGates }) => (
                <div key={key}>
                    <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.15em] mb-2.5 flex items-center gap-2">
                        <span className="h-px flex-1 bg-slate-800" />
                        {label}
                        <span className="h-px flex-1 bg-slate-800" />
                    </h3>
                    <div className="grid grid-cols-3 gap-1.5">
                        {catGates.map(gate => (
                            <DraggableGate key={gate.id} gate={gate} />
                        ))}
                    </div>
                </div>
            ))}

            {filteredGates.length === 0 && (
                <div className="text-center py-4 text-xs text-slate-600">
                    No gates match "{searchQuery}"
                </div>
            )}
        </div>
    );
};

const DraggableGate = ({ gate }: { gate: GateType }) => {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
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
                        p-1.5 rounded-lg bg-gradient-to-br ${gate.color} 
                        flex flex-col items-center justify-center gap-0.5
                        cursor-grab active:cursor-grabbing shadow-lg 
                        border border-white/10
                        hover:scale-110 hover:shadow-xl hover:shadow-cyan-500/10
                        active:scale-95
                        transition-all duration-150 h-14
                        ${isDragging ? 'opacity-50 scale-95' : ''}
                        group relative overflow-hidden
                    `}>
                        {/* Neon glow on hover */}
                        <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-colors rounded-lg" />
                        <Icon className="w-5 h-5 text-white relative z-10" />
                        <span className="text-[9px] font-bold font-mono text-white/90 relative z-10">{gate.name}</span>
                    </div>
                </TooltipTrigger>
                <TooltipContent side="right" className="bg-slate-900 border-slate-700 max-w-[200px]">
                    <p className="font-bold text-cyan-300 text-sm">{gate.label}</p>
                    <p className="text-xs text-slate-400 mt-1">{gate.description}</p>
                    <p className="text-[10px] text-slate-600 mt-1.5 font-mono">
                        {gate.qubits === 1 ? '1 qubit' : `${gate.qubits} qubits`}
                    </p>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    );
};
