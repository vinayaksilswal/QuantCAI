import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useAI } from '@/context/AIContext';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { DndContext, DragEndEvent, DragOverlay, DragStartEvent, useSensor, useSensors, PointerSensor } from '@dnd-kit/core';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useAuth } from '@/context/AuthContext';
import { Play, RotateCcw, Download, Zap, Save } from 'lucide-react';
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

import { GatePalette } from '@/components/GatePalette';
import { CircuitGrid } from '@/components/CircuitGrid';
import { CircuitResults } from '@/components/CircuitResults';
import { GateType, PlacedGate } from '@/types/circuit';
import { TutorialOverlay } from '@/components/TutorialOverlay';

const CircuitBuilder = () => {
    // AuthContext doesn't expose token, so we get it from storage or assume cookie.
    // However, existing backend requires Bearer token.
    // api.ts stores it in 'auth_token'.
    // api.ts stores it in 'auth_token'.
    const { user } = useAuth();
    const { circuitAction, ackCircuitAction, activeTool } = useAI();

    const [circuitName, setCircuitName] = useState("Untitled Circuit");
    const [placedGates, setPlacedGates] = useState<PlacedGate[]>([]);
    const [results, setResults] = useState<any>(null);
    const [activeDragGate, setActiveDragGate] = useState<GateType | null>(null);
    const [useNoise, setUseNoise] = useState(false);
    const [isSimulating, setIsSimulating] = useState(false);
    const [numWires, setNumWires] = useState(5);


    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 8,
            },
        })
    );

    // AI Action Handler
    useEffect(() => {
        if (!circuitAction) return;

        const { action, params } = circuitAction;

        if (action === "add_gate") {
            const gateName = params.gate || "H";
            const wire = params.qubit || 0;
            // Find next available step on this wire
            const existingInWire = placedGates.filter(g => g.wire === wire);
            const step = existingInWire.length > 0
                ? Math.max(...existingInWire.map(g => g.step)) + 1
                : 0;

            // Simple gate mapping logic - you might want a proper lookup from your GatePalette
            // For now, constructing a basic gate object
            // This relies on the AI sending valid gate names
            // You might want to import 'gates' from GatePalette to look up properties like color/icon

            // Fallback for demo properties
            const newGate: PlacedGate = {
                id: gateName,
                name: gateName,
                icon: (props: any) => <span>{gateName}</span>, // Placeholder icon if regex fails, ideally import
                color: "from-blue-500 to-cyan-400",
                description: "AI Added Gate",
                qubits: 1,
                category: "single",
                uid: `gate-${Date.now()}-${Math.random()}`,
                wire: wire,
                step: step
            };

            setPlacedGates(prev => [...prev, newGate]);
            toast.info(`AI added ${gateName} gate on qubit ${wire}`);
        } else if (action === "clear") {
            setPlacedGates([]);
            setResults(null);
            toast.info("AI cleared the circuit");
        } else if (action === "run") {
            runCircuit();
        }

        ackCircuitAction();
    }, [circuitAction, placedGates, ackCircuitAction]);

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

        const newGate: PlacedGate = {
            ...gateData,
            uid: `gate-${Date.now()}-${Math.random()}`,
            wire,
            step,
            targetWire
        };

        setPlacedGates(prev => {
            const filtered = prev.filter(g => !(g.wire === wire && g.step === step));
            return [...filtered, newGate];
        });
    };

    const exportQASM = () => {
        let qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n';
        qasm += `qreg q[${numWires}];\n`;
        qasm += `creg c[${numWires}];\n`;

        const sortedGates = [...placedGates].sort((a, b) => a.step - b.step);
        sortedGates.forEach(g => {
            const name = g.name.toLowerCase();
            if (g.category === 'multi' && g.targetWire !== undefined) {
                if (name === 'cx') qasm += `cx q[${g.wire}],q[${g.targetWire}];\n`;
                else if (name === 'cz') qasm += `cz q[${g.wire}],q[${g.targetWire}];\n`;
                else if (name === 'swap') qasm += `swap q[${g.wire}],q[${g.targetWire}];\n`;
                else if (name === 'ccx') qasm += `ccx q[${g.wire}],q[${g.targetWire}],q[?] /* TODO */; \n`;
            } else {
                qasm += `${name} q[${g.wire}];\n`;
            }
        });

        const blob = new Blob([qasm], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `circuit_${Date.now()}.qasm`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        toast.success("Exported to QASM");
    };

    const runCircuit = async () => {
        setIsSimulating(true);
        try {
            const sortedGates = [...placedGates].sort((a, b) => a.step - b.step);
            const backendCircuit = sortedGates.map(g => {
                const qubits = [g.wire];
                if (g.targetWire !== undefined) qubits.push(g.targetWire);
                return {
                    name: g.name.toLowerCase(),
                    qubits: qubits,
                    params: g.params || []
                };
            });

            // Need to ensure user is logged in
            if (!localStorage.getItem('auth_token')) {
                toast.error("Please log in to run simulations.");
                setIsSimulating(false);
                return;
            }

            // Use the centralized API client
            // Import api at the top if not already there (it is used in AuthContext but not here yet)
            // We need to import 'api' from '@/lib/api'
            const data = await api.runCircuit(backendCircuit, numWires, useNoise);

            setResults(data);
            toast.success("Simulation complete!", { icon: <Zap className="w-4 h-4 text-yellow-400" /> });
        } catch (error: any) {
            console.error(error);
            toast.error(error.message || "Failed to run circuit");
        } finally {
            setIsSimulating(false);
        }
    };

    const clearCircuit = () => {
        setPlacedGates([]);
        setResults(null);
    };

    return (
        <div className="min-h-screen relative overflow-hidden bg-slate-950 text-white font-sans">
            <Navbar />
            <div className="pt-24 pb-20 px-4 md:px-8 max-w-[1600px] mx-auto">

                <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600">
                            Circuit Builder
                        </h1>
                        <p className="text-slate-400 text-sm">Design and simulate multi-qubit circuits</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 bg-slate-900 px-3 py-2 rounded-lg border border-slate-800">
                            <Switch id="noise-mode" checked={useNoise} onCheckedChange={setUseNoise} />
                            <Label htmlFor="noise-mode" className="text-sm text-slate-300 cursor-pointer">simulate noise</Label>
                        </div>
                        <div className="flex gap-2">
                            <Button variant="outline" size="sm" onClick={exportQASM} className="border-slate-700 bg-slate-900/50 hover:bg-slate-800 text-slate-300">
                                <Download className="w-4 h-4 mr-2" /> QASM
                            </Button>
                            <Button variant="outline" size="sm" onClick={clearCircuit} className="border-slate-700 bg-slate-900/50 hover:bg-slate-800 text-slate-300">
                                <RotateCcw className="w-4 h-4 mr-2" /> Clear
                            </Button>
                            <Button
                                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg shadow-blue-500/25"
                                onClick={runCircuit}
                                disabled={isSimulating}
                            >
                                {isSimulating ? <RotateCcw className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
                                {isSimulating ? "Running..." : "Run Circuit"}
                            </Button>
                        </div>
                    </div>
                </header>

                <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
                    <div className="grid lg:grid-cols-12 gap-6 h-[calc(100vh-200px)]">

                        {/* Sidebar: Gates */}
                        <div className="lg:col-span-2 space-y-4 overflow-y-auto pr-2 custom-scrollbar">
                            <Card className="bg-slate-900/80 border-slate-800 backdrop-blur">
                                <CardHeader className="py-3">
                                    <CardTitle className="text-sm font-medium text-slate-300">Gates</CardTitle>
                                </CardHeader>
                                <CardContent className="py-2">
                                    <GatePalette />
                                </CardContent>
                            </Card>

                            <Card className="bg-blue-900/20 border-blue-800/50">
                                <CardContent className="p-4">
                                    <h4 className="text-sm font-bold text-blue-300 mb-1">Tutorial Mode</h4>
                                    <p className="text-xs text-blue-200/70 mb-3">Learn by doing. Build a Bell State.</p>
                                    <Button size="sm" variant="secondary" className="w-full h-8 text-xs" onClick={() => toast.info("Click the ? icon below to start.")}>Start Tutorial</Button>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Main Canvas */}
                        <div className="lg:col-span-7 flex flex-col gap-6 overflow-hidden">
                            <Card className="bg-slate-900/80 border-slate-800 flex-1 overflow-auto relative">
                                <div className="absolute inset-0 bg-[#0f172a] opacity-50 pointer-events-none" />
                                <CardContent className="p-8 min-w-[800px]">
                                    <CircuitGrid placedGates={placedGates} numWires={numWires} numSteps={12} />
                                </CardContent>
                            </Card>
                        </div>

                        {/* Results Panel */}
                        <div className="lg:col-span-3 flex flex-col gap-4 overflow-y-auto">
                            {results ? (
                                <CircuitResults results={results} />
                            ) : (
                                <Card className="bg-slate-900/50 border-slate-800 border-dashed h-64 flex items-center justify-center">
                                    <div className="text-center text-slate-500">
                                        <ActivityIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                        <p className="text-sm">Run a circuit to see results</p>
                                    </div>
                                </Card>
                            )}

                            <Card className="bg-slate-900/50 border-slate-800">
                                <CardHeader className="py-3">
                                    <CardTitle className="text-sm font-medium text-slate-300">Circuit Info</CardTitle>
                                </CardHeader>
                                <CardContent className="text-xs text-slate-400 space-y-2">
                                    <div className="flex justify-between">
                                        <span>Gates:</span>
                                        <span className="text-white">{placedGates.length}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Qubits:</span>
                                        <span className="text-white">{numWires}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Est. Depth:</span>
                                        <span className="text-white">{Math.max(0, ...placedGates.map(g => g.step)) + 1}</span>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                    <DragOverlay>
                        {activeDragGate ? (
                            <div className={`w-12 h-12 rounded flex items-center justify-center bg-gradient-to-br ${activeDragGate.color} shadow-lg cursor-grabbing`}>
                                <activeDragGate.icon className="w-6 h-6 text-white" />
                            </div>
                        ) : null}
                    </DragOverlay>
                </DndContext>

                <TutorialOverlay placedGates={placedGates} setPlacedGates={setPlacedGates} />
            </div>
            <Footer />
        </div>
    );
};

const ActivityIcon = ({ className }: { className?: string }) => (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
);

export default CircuitBuilder;
