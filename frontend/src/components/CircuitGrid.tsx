import { useDroppable } from '@dnd-kit/core';
import { PlacedGate } from '@/types/circuit';
import { useSubscription } from '@/context/SubscriptionContext';
import { Lock } from 'lucide-react';

interface CircuitGridProps {
    placedGates: PlacedGate[];
    numWires: number;
    numSteps: number;
    onRemoveGate?: (uid: string) => void;
}

const WIRE_ROW_HEIGHT = 56; // px — h-14 = 56px
const WIRE_GAP = 12; // px — gap-3 = 12px


export const CircuitGrid = ({ placedGates, numWires, numSteps, onRemoveGate }: CircuitGridProps) => {
    const { tier } = useSubscription();
    const isFree = tier === 'FREE';
    const wires = Array.from({ length: numWires }, (_, i) => i);
    const steps = Array.from({ length: numSteps }, (_, i) => i);

    return (
        <div className="min-w-[800px] select-none relative">
            {/* Step Header Row */}
            <div className="flex mb-2 items-center h-6">
                <div className="w-16 flex-shrink-0" />
                <div className="flex-1 flex gap-2">
                    {steps.map(step => (
                        <div key={step} className="w-12 flex-shrink-0 text-center text-[10px] font-mono text-slate-600">
                            {step}
                        </div>
                    ))}
                </div>
            </div>

            {/* Wire Rows */}
            {wires.map((wire) => {
                const isWireLocked = isFree && wire >= 5;
                return (
                    <div key={wire} className={`flex mb-3 items-center h-14 ${isWireLocked ? 'opacity-35 select-none pointer-events-none' : ''}`}>
                        {/* Wire Label */}
                        <div className="w-16 flex-shrink-0 text-slate-400 font-mono text-sm px-2 flex items-center gap-1">
                            {isWireLocked ? (
                                <Lock className="w-3.5 h-3.5 text-red-500/70" />
                            ) : (
                                <span className="text-cyan-500/60">q</span>
                            )}
                            <span className={isWireLocked ? "text-slate-600" : "text-slate-500"}>[{wire}]</span>
                        </div>

                        {/* Grid Cells */}
                        <div className="flex-1 flex gap-2 relative items-center">
                            {/* Wire Line */}
                            <div className={`absolute top-1/2 left-0 right-0 h-[1px] -z-0 ${isWireLocked ? 'bg-red-500/20' : 'bg-gradient-to-r from-slate-700 via-slate-600 to-slate-700'}`} />

                            {steps.map((step) => {
                                const gateOnWire = placedGates.find(g => g.wire === wire && g.step === step);

                                return (
                                    <DroppableCell
                                        key={`${wire}-${step}`}
                                        id={`cell-${wire}-${step}`}
                                        wire={wire}
                                        step={step}
                                        gate={gateOnWire}
                                        placedGates={placedGates}
                                        onRemoveGate={onRemoveGate}
                                    />
                                );
                            })}
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

interface DroppableCellProps {
    id: string;
    wire: number;
    step: number;
    gate?: PlacedGate;
    placedGates: PlacedGate[];
    onRemoveGate?: (uid: string) => void;
}

const DroppableCell = ({ id, wire, step, gate, placedGates, onRemoveGate }: DroppableCellProps) => {
    const { setNodeRef, isOver } = useDroppable({
        id: id,
    });

    const Icon = gate?.icon;

    // Check if this cell is part of a multi-qubit operation initiated elsewhere
    const controllerGate = placedGates.find(g =>
        g.step === step &&
        g.targetWire === wire &&
        g.wire !== wire
    );

    const isController = gate && gate.targetWire !== undefined && gate.targetWire !== gate.wire;
    const isTarget = !!controllerGate;

    // Calculate connection line height for multi-qubit gates
    const getConnectionStyle = () => {
        if (!isController || !gate?.targetWire) return {};

        const wireDiff = gate.targetWire - wire;
        const rowSpan = Math.abs(wireDiff);
        // Each row is WIRE_ROW_HEIGHT (56px) + WIRE_GAP (12px) apart
        const totalHeight = rowSpan * (WIRE_ROW_HEIGHT + WIRE_GAP);

        if (wireDiff > 0) {
            // Target is BELOW controller
            return {
                top: '50%',
                height: `${totalHeight}px`,
            };
        } else {
            // Target is ABOVE controller
            return {
                bottom: '50%',
                height: `${totalHeight}px`,
            };
        }
    };

    const handleContextMenu = (e: React.MouseEvent) => {
        e.preventDefault();
        if (gate && onRemoveGate) {
            onRemoveGate(gate.uid);
        }
    };

    return (
        <div
            ref={setNodeRef}
            onContextMenu={handleContextMenu}
            className={`
                relative z-10 w-12 h-12 rounded-md border-2 transition-all duration-150
                flex items-center justify-center shrink-0
                ${isOver ? 'border-cyan-400 bg-cyan-500/15 shadow-lg shadow-cyan-500/20' : 'border-transparent hover:border-slate-700/50'}
                ${gate && !isOver ? `bg-gradient-to-br ${gate.color} shadow-lg shadow-black/30 scale-[0.92] rounded-lg ring-1 ring-white/10` : ''}
                ${isTarget && !gate ? 'bg-transparent' : ''}
            `}
        >
            {/* Gate content */}
            {gate && Icon && (
                <div className="relative group">
                    <Icon className="w-6 h-6 text-white drop-shadow-sm" />
                    {gate.category === 'multi' && (
                        <span className="absolute -top-3 -right-4 text-[9px] font-mono font-bold bg-black/70 text-white px-1 rounded-sm ring-1 ring-white/20">
                            {gate.name}
                        </span>
                    )}
                </div>
            )}

            {/* Target Marker — pulsing dot for CX/CZ target */}
            {isTarget && (
                <div className="relative">
                    <div className="w-5 h-5 rounded-full bg-cyan-400 ring-2 ring-cyan-300/60 shadow-lg shadow-cyan-400/40" />
                    <div className="absolute inset-0 w-5 h-5 rounded-full bg-cyan-400/40 animate-ping" />
                </div>
            )}

            {/* Connection Line — controller draws the line to target */}
            {isController && (
                <div
                    className="absolute left-1/2 w-[3px] -translate-x-1/2 -z-10 rounded-full"
                    style={{
                        ...getConnectionStyle(),
                        background: 'linear-gradient(180deg, #22d3ee, #a78bfa, #22d3ee)',
                        boxShadow: '0 0 8px rgba(34, 211, 238, 0.4)',
                    }}
                />
            )}

            {/* Connection Line — from target back to controller (if target is above) */}
            {isTarget && controllerGate && (
                <div
                    className="absolute left-1/2 w-[3px] -translate-x-1/2 -z-10 rounded-full"
                    style={{
                        ...((() => {
                            const wireDiff = controllerGate.wire - wire;
                            const rowSpan = Math.abs(wireDiff);
                            const totalHeight = rowSpan * (WIRE_ROW_HEIGHT + WIRE_GAP);
                            if (wireDiff > 0) {
                                return { top: '50%', height: `${totalHeight}px` };
                            } else {
                                return { bottom: '50%', height: `${totalHeight}px` };
                            }
                        })()),
                        background: 'transparent', // Controller already draws the line
                    }}
                />
            )}
        </div>
    );
};
