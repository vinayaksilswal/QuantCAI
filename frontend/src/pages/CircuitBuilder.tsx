import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { api } from '@/lib/api';
import { useAI } from '@/hooks/useAI';
import { Navbar } from '@/components/Navbar';

import { DndContext, DragEndEvent, DragOverlay, DragStartEvent, useSensor, useSensors, PointerSensor } from '@dnd-kit/core';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useAuth } from '@/hooks/useAuth';
import { useSubscription } from '@/context/SubscriptionContext';
import { Play, RotateCcw, Download, Zap, ChevronDown, Server } from 'lucide-react';
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

import { GatePalette, gates } from '@/components/GatePalette';
import { CircuitGrid } from '@/components/CircuitGrid';
import { CircuitResults } from '@/components/CircuitResults';
import { TelemetryBar } from '@/components/TelemetryBar';
import { GateType, PlacedGate, ExecutionBackend, GateInstructionPayload } from '@/types/circuit';
import { TutorialOverlay } from '@/components/TutorialOverlay';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";


// ─── QASM 3.0 Client-Side Generator ──────────────────────────────────
function generateQASM3(placedGates: PlacedGate[], numWires: number): string {
    const lines: string[] = [
        'OPENQASM 3.0;',
        'include "stdgates.inc";',
        '',
        `qubit[${numWires}] q;`,
        `bit[${numWires}] c;`,
        '',
    ];

    const sortedGates = [...placedGates].sort((a, b) => a.step - b.step);

    sortedGates.forEach(g => {
        const name = g.name.toLowerCase();
        const params = g.params || [];

        if (g.category === 'multi' && g.targetWire !== undefined) {
            if (name === 'cx') lines.push(`cx q[${g.wire}], q[${g.targetWire}];`);
            else if (name === 'cz') lines.push(`cz q[${g.wire}], q[${g.targetWire}];`);
            else if (name === 'swap') lines.push(`swap q[${g.wire}], q[${g.targetWire}];`);
            else if (name === 'ccx' && g.thirdWire !== undefined) {
                lines.push(`ccx q[${g.wire}], q[${g.targetWire}], q[${g.thirdWire}];`);
            } else if (name === 'ccx') {
                // Fallback: if thirdWire not set, use next available
                const third = Math.max(g.wire, g.targetWire) + 1;
                if (third < numWires) {
                    lines.push(`ccx q[${g.wire}], q[${g.targetWire}], q[${third}];`);
                }
            }
        } else if (['rx', 'ry', 'rz'].includes(name)) {
            const theta = params[0] !== undefined ? params[0] : (Math.PI / 2);
            lines.push(`${name}(${theta.toFixed(6)}) q[${g.wire}];`);
        } else {
            lines.push(`${name} q[${g.wire}];`);
        }
    });

    lines.push('');
    for (let i = 0; i < numWires; i++) {
        lines.push(`c[${i}] = measure q[${i}];`);
    }
    lines.push('');

    return lines.join('\n');
}

// ─── Build Backend Payload ───────────────────────────────────────────
function buildGatePayload(placedGates: PlacedGate[]): GateInstructionPayload[] {
    const sortedGates = [...placedGates].sort((a, b) => a.step - b.step);
    return sortedGates.map(g => {
        const qubits = [g.wire];
        if (g.targetWire !== undefined) qubits.push(g.targetWire);
        if (g.thirdWire !== undefined) qubits.push(g.thirdWire);
        return {
            name: g.name.toLowerCase(),
            qubits,
            params: g.params || [],
        };
    });
}

// ─── Bell State Initial Gates ────────────────────────────────────────
function createBellState(): PlacedGate[] {
    const hGate = gates.find(g => g.id === 'h')!;
    const cxGate = gates.find(g => g.id === 'cx')!;

    return [
        {
            ...hGate,
            uid: `bell-h-${Date.now()}`,
            wire: 0,
            step: 0,
        },
        {
            ...cxGate,
            uid: `bell-cx-${Date.now()}`,
            wire: 0,
            step: 1,
            targetWire: 1,
        },
    ];
}

// ─── Execution Backend Config ────────────────────────────────────────
const BACKENDS: { value: ExecutionBackend; label: string; available: boolean }[] = [
    { value: 'local', label: 'Local Simulator', available: true },
    { value: 'aws_braket', label: 'AWS Braket', available: false },
    { value: 'ibm_quantum', label: 'IBM Quantum', available: false },
];

// ─── Main Component ─────────────────────────────────────────────────
const CircuitBuilder = () => {
    const { user } = useAuth();
    const { circuitActions, ackCircuitAction, updateClientContext } = useAI();
    const { tier } = useSubscription();
    const numWires = tier === 'FREE' ? 6 : 10;

    const [placedGates, setPlacedGates] = useState<PlacedGate[]>(() => createBellState());

    // Sync active circuit state to AI Context
    useEffect(() => {
        const calculateDepth = (gates: PlacedGate[]) => {
            if (gates.length === 0) return 0;
            return Math.max(...gates.map(g => g.step)) + 1;
        };

        const circuitGraph = placedGates.map(g => ({
            uid: g.uid,
            name: g.name,
            wire: g.wire,
            step: g.step,
            targetWire: g.targetWire,
            thirdWire: g.thirdWire,
            params: g.params
        }));

        updateClientContext('circuit-builder', {
            circuit_graph: circuitGraph,
            total_qubits: numWires,
            placed_gates_count: placedGates.length,
            circuit_depth: calculateDepth(placedGates)
        });
    }, [placedGates, numWires, updateClientContext]);
    const [results, setResults] = useState<any>(null);
    const [activeDragGate, setActiveDragGate] = useState<GateType | null>(null);
    const [useNoise, setUseNoise] = useState(false);
    const [isSimulating, setIsSimulating] = useState(false);
    const [shots, setShots] = useState(1024);
    const [backend, setBackend] = useState<ExecutionBackend>('local');
    const [resultsTab, setResultsTab] = useState('chart');

    // Auto-disable noise for FREE users
    useEffect(() => {
        if (tier === 'FREE') {
            setUseNoise(false);
        }
    }, [tier]);

    // Live QASM — updates whenever gates change
    const liveQASM = useMemo(
        () => generateQASM3(placedGates, numWires),
        [placedGates, numWires]
    );

    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 8,
            },
        })
    );

    const runCircuit = useCallback(async () => {
        setIsSimulating(true);
        try {
            if (!user) {
                toast.error("Please log in to run simulations.");
                setIsSimulating(false);
                return;
            }

            if (placedGates.length === 0) {
                toast.error("Circuit is empty. Add some gates first!");
                setIsSimulating(false);
                return;
            }

            const payload = {
                num_qubits: numWires,
                shots: shots,
                gates: buildGatePayload(placedGates),
                use_noise: useNoise,
            };

            const data = await api.simulateV1(payload);
            setResults(data);
            setResultsTab('chart');
            toast.success("Simulation complete!", { icon: <Zap className="w-4 h-4 text-yellow-400" /> });
        } catch (error: any) {
            console.error("Simulation failed:", error);
            const msg = error instanceof Error ? error.message : String(error);
            toast.error(msg || "Failed to run circuit");
        } finally {
            setIsSimulating(false);
        }
    }, [user, placedGates, numWires, shots, useNoise]);

    const runCircuitRef = useRef(runCircuit);
    useEffect(() => {
        runCircuitRef.current = runCircuit;
    }, [runCircuit]);

    // AI Action Handler
    useEffect(() => {
        if (circuitActions.length === 0) return;

        const currentAction = circuitActions[0];
        const { action, params, id } = currentAction;

        console.log("Processing AI Action:", action, params);

        if (action === "add_gate") {
            const gateName = (params.gate || "H").toLowerCase();
            const controlWire = params.control !== undefined ? params.control : (params.qubit || 0);
            const targetWire = params.target !== undefined ? params.target : undefined;

            const gateDef = gates.find(g =>
                g.id === gateName ||
                g.name.toLowerCase() === gateName ||
                (gateName === 'cx' && g.id === 'cnot') ||
                (gateName === 'cnot' && g.id === 'cnot')
            );

            if (gateDef) {
                const involvedWires = [controlWire];
                if (targetWire !== undefined) involvedWires.push(targetWire);
                else if (gateDef.qubits > 1) {
                    const fallbackTarget = controlWire < 4 ? controlWire + 1 : controlWire - 1;
                    involvedWires.push(fallbackTarget);
                }

                setPlacedGates(prev => {
                    const existingInInvolved = prev.filter(g =>
                        involvedWires.includes(g.wire) ||
                        (g.targetWire !== undefined && involvedWires.includes(g.targetWire))
                    );

                    const step = existingInInvolved.length > 0
                        ? Math.max(...existingInInvolved.map(g => g.step)) + 1
                        : 0;

                    const newGate: PlacedGate = {
                        ...gateDef,
                        uid: `gate-${Date.now()}-${Math.random()}`,
                        wire: controlWire,
                        step: step,
                        targetWire: targetWire !== undefined ? targetWire : (gateDef.qubits > 1 ? involvedWires[1] : undefined)
                    };

                    return [...prev, newGate];
                });
                toast.info(`AI added ${gateDef.name} gate on ${involvedWires.length > 1 ? `wires ${involvedWires.join(' & ')}` : `wire ${controlWire}`}`);
            } else {
                toast.error(`Unknown gate: ${gateName}`);
            }
        } else if (action === "clear") {
            setPlacedGates([]);
            setResults(null);
            toast.info("AI cleared the circuit");
        } else if (action === "run") {
            runCircuitRef.current();
        }

        ackCircuitAction(id);
    }, [circuitActions, ackCircuitAction]);

    const handleDragStart = (event: DragStartEvent) => {
        const { active } = event;
        setActiveDragGate(active.data.current as GateType);
    };

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;
        setActiveDragGate(null);

        if (!over) return;

        const overId = over.id as string;
        if (overId.startsWith("trash")) return;

        const parts = overId.split("-");
        if (parts[0] !== "cell") return;

        const wire = parseInt(parts[1]);
        const step = parseInt(parts[2]);
        const gateData = active.data.current as GateType;

        let targetWire: number | undefined = undefined;
        if (gateData.qubits > 1) {
            if (wire < numWires - 1) targetWire = wire + 1;
            else if (wire > 0) targetWire = wire - 1;
        }

        let thirdWire: number | undefined = undefined;
        if (gateData.qubits > 2 && targetWire !== undefined) {
            // For CCX (Toffoli), add a third wire
            const candidate = Math.max(wire, targetWire) + 1;
            if (candidate < numWires) thirdWire = candidate;
            else {
                const candidate2 = Math.min(wire, targetWire) - 1;
                if (candidate2 >= 0) thirdWire = candidate2;
            }
        }

        // Intercept 6th wire drop for FREE tier
        if (tier === 'FREE' && (wire >= 5 || (targetWire !== undefined && targetWire >= 5) || (thirdWire !== undefined && thirdWire >= 5))) {
            window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'qubits' } }));
            toast.error("Using the 6th qubit wire requires a Pro subscription.");
            return;
        }

        const newGate: PlacedGate = {
            ...gateData,
            uid: `gate-${Date.now()}-${Math.random()}`,
            wire,
            step,
            targetWire,
            thirdWire,
        };

        setPlacedGates(prev => {
            const filtered = prev.filter(g => !(g.wire === wire && g.step === step));
            return [...filtered, newGate];
        });
    };

    const handleRemoveGate = useCallback((uid: string) => {
        setPlacedGates(prev => prev.filter(g => g.uid !== uid));
        toast.info("Gate removed");
    }, []);



    const exportQASM = () => {
        const blob = new Blob([liveQASM], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `circuit_${Date.now()}.qasm`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("Exported OpenQASM 3.0");
    };

    const clearCircuit = () => {
        setPlacedGates([]);
        setResults(null);
    };

    const currentBackend = BACKENDS.find(b => b.value === backend)!;

    return (
        <div className="min-h-screen relative overflow-hidden bg-slate-950 text-white font-sans">
            <Navbar />
            <div className="pt-20 pb-4 px-3 md:px-4 max-w-[1800px] mx-auto flex flex-col" style={{ height: 'calc(100vh - 0px)' }}>

                {/* ─── HEADER BAR ──────────────────────────────────── */}
                <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-3 gap-3 shrink-0">
                    <div>
                        <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500">
                            Circuit Builder
                        </h1>
                        <p className="text-slate-500 text-xs">Enterprise Quantum Circuit Design & Simulation</p>
                    </div>

                    <div className="flex items-center gap-3 flex-wrap">
                        {/* Execution Backend Dropdown */}
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="outline" size="sm" className="border-slate-700 bg-slate-900/70 hover:bg-slate-800 text-slate-300 gap-2 h-9">
                                    <Server className="w-3.5 h-3.5 text-cyan-400" />
                                    <span className="text-xs">{currentBackend.label}</span>
                                    <ChevronDown className="w-3 h-3 opacity-50" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent className="bg-slate-900 border-slate-700">
                                {BACKENDS.map(b => (
                                    <DropdownMenuItem
                                        key={b.value}
                                        onClick={() => b.available && setBackend(b.value)}
                                        className={`text-xs ${!b.available ? 'opacity-40 cursor-not-allowed' : 'text-slate-300 focus:text-white focus:bg-slate-800'}`}
                                        disabled={!b.available}
                                    >
                                        <span>{b.label}</span>
                                        {!b.available && <span className="ml-2 text-[9px] text-cyan-500 font-mono">SOON</span>}
                                    </DropdownMenuItem>
                                ))}
                            </DropdownMenuContent>
                        </DropdownMenu>

                        {/* Shots Input */}
                        <div className="flex items-center gap-2 bg-slate-900/70 border border-slate-700 rounded-lg px-3 h-9">
                            <label className="text-[10px] text-slate-500 uppercase tracking-wider">Shots</label>
                            <input
                                type="number"
                                min={1}
                                max={100000}
                                value={shots}
                                onChange={e => {
                                    const val = parseInt(e.target.value) || 1;
                                    if (tier === 'FREE' && val > 1024) {
                                        setShots(1024);
                                        window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'shots' } }));
                                        toast.error("Free tier is limited to a maximum of 1,024 shots.");
                                        return;
                                    }
                                    setShots(Math.max(1, Math.min(100000, val)));
                                }}
                                className="w-20 bg-transparent text-sm text-white font-mono text-right focus:outline-none border-none"
                            />
                        </div>

                        {/* Noise Toggle */}
                        <div className="flex items-center gap-2 bg-slate-900/70 border border-slate-700 rounded-lg px-3 h-9">
                            <Switch 
                                id="noise-mode" 
                                checked={useNoise} 
                                onCheckedChange={(val) => {
                                    if (tier === 'FREE') {
                                        window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'noise' } }));
                                        toast.error("Noise models require a Pro subscription.");
                                        return;
                                    }
                                    setUseNoise(val);
                                }} 
                                className="scale-90" 
                            />
                            <Label htmlFor="noise-mode" className="text-[10px] text-slate-400 cursor-pointer uppercase tracking-wider">Noise</Label>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={exportQASM} className="border-slate-700 bg-slate-900/70 hover:bg-slate-800 text-slate-300 h-9">
                                <Download className="w-3.5 h-3.5 mr-1.5" /> QASM
                            </Button>
                            <Button variant="outline" size="sm" onClick={clearCircuit} className="border-slate-700 bg-slate-900/70 hover:bg-slate-800 text-slate-300 h-9">
                                <RotateCcw className="w-3.5 h-3.5 mr-1.5" /> Clear
                            </Button>
                            <Button
                                className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20 h-9 px-5 font-semibold"
                                onClick={runCircuit}
                                disabled={isSimulating}
                            >
                                {isSimulating ? <RotateCcw className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
                                {isSimulating ? "Running..." : "Run Circuit"}
                            </Button>
                        </div>
                    </div>
                </header>

                {/* ─── 4-PANE IDE LAYOUT ──────────────────────────── */}
                <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
                    <div className="grid lg:grid-cols-12 gap-3 flex-1 min-h-0 overflow-hidden">

                        {/* ── LEFT PANE: Gate Library ─────────────────── */}
                        <div className="lg:col-span-2 overflow-y-auto custom-scrollbar">
                            <Card className="bg-slate-900/60 border-slate-800/80 backdrop-blur-sm h-full">
                                <CardHeader className="py-2.5 px-3 border-b border-slate-800/50">
                                    <CardTitle className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Gate Library</CardTitle>
                                </CardHeader>
                                <CardContent className="p-3">
                                    <GatePalette />
                                </CardContent>
                            </Card>
                        </div>

                        {/* ── CENTER PANE: Circuit Canvas ─────────────── */}
                        <div className="lg:col-span-7 flex flex-col min-h-0 overflow-hidden">
                            <Card className="bg-slate-900/60 border-slate-800/80 backdrop-blur-sm flex-1 overflow-hidden flex flex-col">
                                <div className="flex-1 overflow-auto relative">
                                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(6,182,212,0.03),transparent_70%)]" />
                                    <div className="p-6 min-w-[800px] relative z-10">
                                        <CircuitGrid
                                            placedGates={placedGates}
                                            numWires={numWires}
                                            numSteps={14}
                                            onRemoveGate={handleRemoveGate}
                                        />
                                    </div>
                                </div>
                                {/* Telemetry Bar */}
                                <TelemetryBar placedGates={placedGates} numWires={numWires} shots={shots} />
                            </Card>
                        </div>

                        {/* ── RIGHT PANE: Analytics & Export ──────────── */}
                        <div className="lg:col-span-3 overflow-hidden flex flex-col min-h-0">
                            <CircuitResults
                                results={results}
                                qasmCode={liveQASM}
                                activeTab={resultsTab}
                                onTabChange={setResultsTab}
                            />
                        </div>
                    </div>

                    <DragOverlay>
                        {activeDragGate ? (
                            <div className={`w-12 h-12 rounded-lg flex items-center justify-center bg-gradient-to-br ${activeDragGate.color} shadow-xl shadow-cyan-500/20 cursor-grabbing ring-2 ring-white/20`}>
                                <activeDragGate.icon className="w-6 h-6 text-white" />
                            </div>
                        ) : null}
                    </DragOverlay>
                </DndContext>

                <TutorialOverlay placedGates={placedGates} setPlacedGates={setPlacedGates} />
            </div>
        </div>
    );
};

export default CircuitBuilder;
