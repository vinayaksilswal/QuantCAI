import { useDroppable } from '@dnd-kit/core';
import { PlacedGate } from '@/types/circuit';
import { useSubscription } from '@/context/SubscriptionContext';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useState, useEffect } from 'react';

interface CircuitGridProps {
    placedGates: PlacedGate[];
    numWires: number;
    numSteps: number;
    onRemoveGate?: (uid: string) => void;
    onUpdateGateParams?: (uid: string, params: number[]) => void;
    activeDebugStep?: number;
}

const WIRE_ROW_HEIGHT = 56; // px — h-14 = 56px
const WIRE_GAP = 12; // px — gap-3 = 12px


export const CircuitGrid = ({ placedGates, numWires, numSteps, onRemoveGate, onUpdateGateParams, activeDebugStep }: CircuitGridProps) => {
    const { tier } = useSubscription();
    const wires = Array.from({ length: numWires }, (_, i) => i);
    const steps = Array.from({ length: numSteps }, (_, i) => i);

    return (
        <div className="min-w-[800px] select-none relative">
            {/* Step Header Row */}
            <div className="flex mb-2 items-center h-6">
                <div className="w-16 flex-shrink-0" />
                <div className="flex-1 flex gap-2">
                    {steps.map(step => (
                        <div key={step} className={`w-12 flex-shrink-0 text-center text-[10px] font-mono transition-colors ${activeDebugStep !== undefined && step === activeDebugStep ? 'text-cyan-400 font-bold bg-cyan-500/10 rounded' : (activeDebugStep !== undefined && step > activeDebugStep ? 'text-slate-700' : 'text-slate-600')}`}>
                            {step}
                        </div>
                    ))}
                </div>
            </div>

            {/* Wire Rows */}
            {wires.map((wire) => {
                return (
                    <div key={wire} className={`flex mb-3 items-center h-14`}>
                        {/* Wire Label */}
                        <div className="w-16 flex-shrink-0 text-slate-400 font-mono text-sm px-2 flex items-center gap-1">
                            <span className="text-cyan-500/60">q</span>
                            <span className="text-slate-500">[{wire}]</span>
                        </div>

                        {/* Grid Cells */}
                        <div className="flex-1 flex gap-2 relative items-center">
                            {/* Wire Line */}
                            <div className={`absolute top-1/2 left-0 right-0 h-[1px] -z-0 bg-gradient-to-r from-slate-700 via-slate-600 to-slate-700`} />

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
                                        onUpdateGateParams={onUpdateGateParams}
                                        isDisabled={activeDebugStep !== undefined && step > activeDebugStep}
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
    onUpdateGateParams?: (uid: string, params: number[]) => void;
    isDisabled?: boolean;
}

const DroppableCell = ({ id, wire, step, gate, placedGates, onRemoveGate, onUpdateGateParams, isDisabled }: DroppableCellProps) => {
    const { setNodeRef, isOver } = useDroppable({
        id: id,
    });

    const Icon = gate?.icon;
    const isParametric = gate && ['rx', 'ry', 'rz'].includes(gate.name.toLowerCase());
    const [paramVal, setParamVal] = useState(gate?.params?.[0]?.toString() || "1.5708");

    useEffect(() => {
        if (gate?.params?.[0] !== undefined) {
            setParamVal(gate.params[0].toString());
        }
    }, [gate?.params]);

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

    const handleParamChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setParamVal(e.target.value);
    };

    const handleParamSubmit = () => {
        if (gate && onUpdateGateParams) {
            onUpdateGateParams(gate.uid, [parseFloat(paramVal) || 0]);
        }
    };

    return (
        <div
            ref={setNodeRef}
            onContextMenu={handleContextMenu}
            className={`
                relative z-10 w-12 h-12 rounded-md border-2 transition-all duration-150
                flex items-center justify-center shrink-0
                ${isDisabled ? 'opacity-30 grayscale' : ''}
                ${isOver && !isDisabled ? 'border-cyan-400 bg-cyan-500/15 shadow-lg shadow-cyan-500/20' : 'border-transparent hover:border-slate-700/50'}
                ${gate && !isOver ? `bg-gradient-to-br ${gate.color} shadow-lg shadow-black/30 scale-[0.92] rounded-lg ring-1 ring-white/10` : ''}
                ${isTarget && !gate ? 'bg-transparent' : ''}
            `}
        >
            {/* Gate content */}
            {gate && Icon && (
                isParametric ? (
                    <Popover>
                        <PopoverTrigger asChild>
                            <div className="relative group cursor-pointer w-full h-full flex items-center justify-center">
                                <Icon className="w-6 h-6 text-white drop-shadow-sm" />
                                {gate.category === 'multi' && (
                                    <span className="absolute -top-3 -right-4 text-[9px] font-mono font-bold bg-black/70 text-white px-1 rounded-sm ring-1 ring-white/20">
                                        {gate.name}
                                    </span>
                                )}
                            </div>
                        </PopoverTrigger>
                        <PopoverContent className="w-48 bg-slate-900 border-slate-700 p-3" side="top">
                            <div className="space-y-2">
                                <label className="text-xs text-slate-400">Angle θ (radians)</label>
                                <div className="flex gap-2">
                                    <input 
                                        type="number" 
                                        step="0.1"
                                        value={paramVal}
                                        onChange={handleParamChange}
                                        className="w-full bg-slate-800 border border-slate-700 rounded text-xs text-slate-200 p-1 focus:outline-none focus:border-cyan-500"
                                    />
                                    <button 
                                        onClick={handleParamSubmit}
                                        className="bg-cyan-600 hover:bg-cyan-500 text-white text-xs px-2 rounded"
                                    >
                                        Set
                                    </button>
                                </div>
                            </div>
                        </PopoverContent>
                    </Popover>
                ) : (
                    <div className="relative group">
                        <Icon className="w-6 h-6 text-white drop-shadow-sm" />
                        {gate.category === 'multi' && (
                            <span className="absolute -top-3 -right-4 text-[9px] font-mono font-bold bg-black/70 text-white px-1 rounded-sm ring-1 ring-white/20">
                                {gate.name}
                            </span>
                        )}
                    </div>
                )
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
