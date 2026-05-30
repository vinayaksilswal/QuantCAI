import { useDroppable } from '@dnd-kit/core';
import { PlacedGate } from '@/types/circuit'; // Updated import
// import { X } from 'lucide-react'; // Unused

interface CircuitGridProps {
    placedGates: PlacedGate[];
    numWires: number;
    numSteps: number;
}

export const CircuitGrid = ({ placedGates, numWires, numSteps }: CircuitGridProps) => {
    const wires = Array.from({ length: numWires }, (_, i) => i);
    const steps = Array.from({ length: numSteps }, (_, i) => i);

    return (
        <div className="min-w-[800px] select-none relative">


            {wires.map((wire) => (
                <div key={wire} className="flex mb-6 items-center h-12">
                    <div className="w-16 flex-shrink-0 text-slate-400 font-mono text-sm px-2">
                        q[{wire}]
                    </div>
                    <div className="flex-1 flex gap-2 relative items-center">
                        {/* Wire Line */}
                        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-700 -z-0" />

                        {steps.map((step) => {
                            // Check for multi-qubit gate parts
                            // 1. Is there a gate acting on this wire at this step?
                            const gateOnWire = placedGates.find(g => g.wire === wire && g.step === step);

                            // 2. Is this wire a 'target' of a gate on another wire? (Simplification: gate.targetWire)
                            // We need to handle this in data structure. 
                            // If PlacedGate has wire & targetWire, the 'target' cell needs to show something too?
                            // Or we just draw the line.

                            return (
                                <DroppableCell
                                    key={`${wire}-${step}`}
                                    id={`cell-${wire}-${step}`}
                                    wire={wire}
                                    step={step}
                                    gate={gateOnWire}
                                    placedGates={placedGates}
                                />
                            );
                        })}
                    </div>
                </div>
            ))}
        </div>
    );
};

interface DroppableCellProps {
    id: string;
    wire: number;
    step: number;
    gate?: PlacedGate;
    placedGates: PlacedGate[];
}

const DroppableCell = ({ id, wire, step, gate, placedGates }: DroppableCellProps) => {
    const { setNodeRef, isOver } = useDroppable({
        id: id,
    });

    const Icon = gate?.icon;

    // Check if this cell is part of a multi-qubit operation initiated elsewhere
    const controllerGate = placedGates.find(g =>
        g.step === step && // Same step
        g.targetWire === wire && // This is the target
        g.wire !== wire // Originating elsewhere
    );

    // If I am a controller (gate.targetWire is set), I need a line to the target.
    // If I am a target (controllerGate exists), I need to show connection.

    const isController = gate && gate.targetWire !== undefined && gate.targetWire !== gate.wire;
    const isTarget = !!controllerGate;

    return (
        <div
            ref={setNodeRef}
            className={`
                relative z-10 w-12 h-12 rounded-sm border-2 transition-all 
                flex items-center justify-center shrink-0
                ${isOver ? 'border-blue-400 bg-blue-500/20' : 'border-transparent hover:border-slate-700'}
                ${gate && !isOver ? `bg-gradient-to-br ${gate.color} shadow-lg scale-90 rounded-md` : ''}
                ${isTarget ? 'bg-slate-800' : ''} 
            `}
        >
            {/* Draw gate content */}
            {gate && Icon && (
                <div className="relative">
                    <Icon className="w-6 h-6 text-white" />
                    {gate.category === 'multi' && (
                        <span className="absolute -top-3 -right-3 text-[10px] bg-black/50 px-1 rounded">
                            {gate.name}
                        </span>
                    )}
                </div>
            )}

            {/* Target Marker (e.g. for CNOT target X, or just a dot if user dragging raw CNOT) */}
            {isTarget && (
                <div className="w-4 h-4 rounded-full bg-blue-500 ring-2 ring-blue-300 animate-pulse" />
            )}

            {/* Connection Line Calculation handled simply via absolute diff */}
            {(isController || isTarget) && (
                <div className={`absolute left-1/2 w-0.5 bg-blue-400 -z-10`} style={{
                    top: isController ? (gate!.targetWire! > wire ? '50%' : `calc(${(gate!.targetWire! - wire) * 100}% + 24px)`) : undefined,
                    height: isController ? `calc(${Math.abs(gate!.targetWire! - wire) * 72}px)` : undefined,
                    // 72px approx row height (48px box + 24px margin)
                    // This is brittle css math, but functional for MVP.
                }} />
            )}

            {/* If I am target, draw line UP or DOWN to controller? 
                Actually, simpler: Controller draws the full line to target. 
                React renders top-down, so it doesn't matter who draws it as long as z-index is right.
                Above logic attempts to have Controller draw it.
            */}

            {/* If I am controller, check if I need to draw UP or DOWN.
                If target > wire (below), top=50%, height = diff
                If target < wire (above), top = negative diff, height = diff
             */}

            {isController && (
                <div
                    className="absolute left-1/2 w-1 bg-gradient-to-b from-blue-400 to-purple-500 -z-10 opacity-70"
                    style={{
                        top: gate!.targetWire! > wire ? '50%' : `calc(50% - ${Math.abs(gate!.targetWire! - wire) * 72}px)`,
                        height: `${Math.abs(gate!.targetWire! - wire) * 72}px`
                    }}
                />
            )}

        </div>
    );
};
