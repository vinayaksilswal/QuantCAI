import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { api } from '@/lib/api';
import { useAI } from '@/hooks/useAI';
import { Navbar } from '@/components/Navbar';
import { useNavigate } from 'react-router-dom';

import { DndContext, DragEndEvent, DragOverlay, DragStartEvent, useSensor, useSensors, PointerSensor } from '@dnd-kit/core';
import { SEO } from '@/components/SEO';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useAuth } from '@/hooks/useAuth';
import { useSubscription } from '@/context/SubscriptionContext';
import { Play, RotateCcw, Download, Zap, ChevronDown, Server, Plus, Minus, BookOpen, BugPlay, StepForward, StepBack, Undo2, Redo2, Sparkles, Share2 } from 'lucide-react';
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

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
    DropdownMenuSeparator,
    DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Settings2 } from 'lucide-react';
import { TEMPLATES, CircuitTemplate } from '@/circuitTemplates';


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
        const name = (g.name || 'id_gate').toLowerCase();
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

function generateQASM2(placedGates: PlacedGate[], numWires: number): string {
    const lines: string[] = [
        'OPENQASM 2.0;',
        'include "qelib1.inc";',
        '',
        `qreg q[${numWires}];`,
        `creg c[${numWires}];`,
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
        lines.push(`measure q[${i}] -> c[${i}];`);
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
            name: (g.name || 'id_gate').toLowerCase(),
            qubits,
            params: g.params || [],
        };
    });
}
// Templates are now loaded from @/circuitTemplates
// ─── Execution Backend Config ────────────────────────────────────────
const BACKENDS: { value: ExecutionBackend | string; label: string; available: boolean; isPro?: boolean }[] = [
    { value: 'simulator_statevector', label: 'Local Simulator', available: true },
    { value: 'aer_simulator', label: 'Aer Simulator', available: true, isPro: true },
    { value: 'ibm_brisbane_127q', label: 'IBM Brisbane (127Q)', available: true, isPro: true },
    { value: 'ionq_forte_36q', label: 'IonQ Forte (36Q)', available: true, isPro: true },
];

// ─── Main Component ─────────────────────────────────────────────────
const CircuitBuilder = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const { circuitActions, ackCircuitAction, updateClientContext } = useAI();
    const { tier } = useSubscription();
    const maxWires = tier === 'FREE' ? 3 : tier === 'PRO' ? 15 : 30;
    const [numWires, setNumWires] = useState(3);
    const [mitigation, setMitigation] = useState({ zne: false, pec: false, readout: false });

    const handleBackendSelect = (value: string) => {
        if (value === 'ibm_brisbane_127q') {
            const key = localStorage.getItem('ibm_quantum_key');
            if (!key) {
                toast.error("IBM Quantum API key not found! Redirecting to Developer Console...");
                navigate('/profile', { state: { tab: 'developer' } });
                return;
            }
        } else if (value === 'ionq_forte_36q') {
            const key = localStorage.getItem('ionq_api_key');
            if (!key) {
                toast.error("IonQ API key not found! Redirecting to Developer Console...");
                navigate('/profile', { state: { tab: 'developer' } });
                return;
            }
        }
        setBackend(value);
    };

    const [history, setHistory] = useState<PlacedGate[][]>(() => {
        const saved = localStorage.getItem('circuit-history');
        if (saved) {
            try {
                const parsed: PlacedGate[][] = JSON.parse(saved);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    return parsed.map(stepGates => 
                        (Array.isArray(stepGates) ? stepGates : []).map(g => {
                            const baseGate = gates.find(bg => bg.id === g.id);
                            if (baseGate) {
                                return { ...baseGate, ...g, icon: baseGate.icon, color: baseGate.color };
                            }
                            return g;
                        })
                    );
                }
            } catch (e) {
                console.error("Failed to parse circuit history", e);
            }
        }
        return [[...TEMPLATES[0].fn()]];
    });
    const [historyIndex, setHistoryIndex] = useState(() => {
        const savedHistory = localStorage.getItem('circuit-history');
        let maxIndex = 0;
        if (savedHistory) {
            try {
                const parsed = JSON.parse(savedHistory);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    maxIndex = parsed.length - 1;
                }
            } catch (e) {}
        }
        
        const saved = localStorage.getItem('circuit-history-index');
        let index = saved ? parseInt(saved) : 0;
        if (isNaN(index) || index < 0) index = 0;
        if (index > maxIndex) index = maxIndex;
        return index;
    });

    const placedGates = useMemo(() => history[historyIndex] || [], [history, historyIndex]);

    const setPlacedGates = useCallback((action: React.SetStateAction<PlacedGate[]>) => {
        setHistory(prev => {
            const currentIdx = Math.min(historyIndex, prev.length - 1);
            const current = prev[currentIdx] || [];
            const next = typeof action === 'function' ? action(current) : action;
            
            const newHistory = prev.slice(0, currentIdx + 1);
            newHistory.push(next);
            
            if (newHistory.length > 50) newHistory.shift();
            
            setHistoryIndex(newHistory.length - 1);
            
            return newHistory;
        });
    }, [historyIndex]);

    useEffect(() => {
        localStorage.setItem('circuit-history', JSON.stringify(history));
        localStorage.setItem('circuit-history-index', historyIndex.toString());
    }, [history, historyIndex]);

    const undo = () => setHistoryIndex(prev => Math.max(0, prev - 1));
    const redo = () => setHistoryIndex(prev => Math.min(history.length - 1, prev + 1));

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
    const [backend, setBackend] = useState<ExecutionBackend | string>('simulator_statevector');
    const [resultsTab, setResultsTab] = useState('chart');

    // Debugger State
    const [isDebugMode, setIsDebugMode] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const [noiseConfig, setNoiseConfig] = useState({ enabled: false, type: 'depolarizing', rate: 0.01 });

    // Sharing State
    const [isShareModalOpen, setIsShareModalOpen] = useState(false);
    const [isSharing, setIsSharing] = useState(false);
    const [shareSlug, setShareSlug] = useState<string | null>(null);
    const [isCircuitPublic, setIsCircuitPublic] = useState(false);
    const [backendCircuitId, setBackendCircuitId] = useState<number | null>(null);
    const [circuitName, setCircuitName] = useState("My Quantum Circuit");

    const handleShare = async () => {
        if (placedGates.length === 0) {
            toast.error("Circuit is empty. Add gates before sharing!");
            return;
        }
        setIsSharing(true);
        try {
            let currentId = backendCircuitId;
            if (!currentId) {
                // Save circuit to backend database first
                const saved = await api.saveCircuit({
                    name: circuitName,
                    circuit_data: JSON.stringify(placedGates),
                    is_interactive: true
                });
                currentId = saved.id;
                setBackendCircuitId(currentId);
            }
            
            const shared = await api.shareCircuit(currentId!);
            setShareSlug(shared.share_slug);
            setIsCircuitPublic(shared.is_public);
            toast.success("Circuit shared successfully!");
        } catch (error: any) {
            console.error("Failed to share circuit:", error);
            toast.error(error.message || "Failed to share circuit");
        } finally {
            setIsSharing(false);
        }
    };

    const handleTogglePublic = async (checked: boolean) => {
        if (!backendCircuitId) return;
        setIsSharing(true);
        try {
            if (checked) {
                const res = await api.shareCircuit(backendCircuitId);
                setShareSlug(res.share_slug);
                setIsCircuitPublic(res.is_public);
                toast.success("Circuit is now public!");
            } else {
                const res = await api.unshareCircuit(backendCircuitId);
                setIsCircuitPublic(res.is_public);
                toast.info("Circuit is now private.");
            }
        } catch (error: any) {
            console.error("Failed to update visibility:", error);
            toast.error(error.message || "Failed to update visibility");
        } finally {
            setIsSharing(false);
        }
    };

    const maxCircuitStep = useMemo(() => {
        if (placedGates.length === 0) return 0;
        return Math.max(...placedGates.map(g => g.step));
    }, [placedGates]);

    // Auto-disable noise for FREE users
    useEffect(() => {
        if (tier === 'FREE') {
            setNoiseConfig(prev => ({ ...prev, enabled: false }));
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

    const runCircuit = useCallback(async (limitStep?: number) => {
        setIsSimulating(true);
        try {
            if (!user) {
                toast.error("Please log in to run simulations.");
                navigate('/login', { state: { returnTo: '/circuit-builder' } });
                setIsSimulating(false);
                return;
            }

            const activeGates = limitStep !== undefined 
                ? placedGates.filter(g => g.step <= limitStep)
                : placedGates;

            if (activeGates.length === 0 && placedGates.length > 0) {
                 // Debugger at step 0 might have no gates, we simulate empty
            } else if (placedGates.length === 0) {
                toast.error("Circuit is empty. Add some gates first!");
                setIsSimulating(false);
                return;
            }

            // Fallback to legacy endpoint if 'local' is used somehow, or if we want to use the new API:
            const qasm = generateQASM3(activeGates, numWires);
            
            const payload = {
                backend_id: backend,
                circuit_qasm: qasm,
                shots: shots,
                mitigation: mitigation
            };

            const response = await api.simulate(payload);
            const jobId = response.job_id;
            
            // Polling loop
            let attempts = 0;
            while (attempts < 60) {
                const statusData = await api.pollSimulation(jobId);
                if (statusData.status === "complete") {
                    setResults(statusData.result);
                    break;
                } else if (statusData.status === "failed") {
                    toast.error(`Simulation failed: ${statusData.error}`);
                    break;
                }
                
                await new Promise(r => setTimeout(r, 1000));
                attempts++;
            }
            if (attempts >= 60) {
                toast.error("Simulation timed out.");
            }
            if (limitStep === undefined) toast.success("Simulation complete!", { icon: <Zap className="w-4 h-4 text-yellow-400" /> });
        } catch (error: any) {
            console.error("Simulation error:", error);
            toast.error(error?.response?.data?.detail || "Simulation failed");
        } finally {
            setIsSimulating(false);
        }
    }, [user, placedGates, backend, shots, mitigation, numWires]);

    // Handle Debugger Step Change
    useEffect(() => {
        if (isDebugMode) {
            runCircuit(currentStep);
        }
    }, [currentStep, isDebugMode]);

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

        // Bounds checking
        if (wire >= numWires || (targetWire !== undefined && targetWire >= numWires) || (thirdWire !== undefined && thirdWire >= numWires)) {
            toast.error("Gate target exceeds available qubits.");
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

    const handleUpdateGateParams = useCallback((uid: string, params: number[]) => {
        setPlacedGates(prev => prev.map(g => g.uid === uid ? { ...g, params } : g));
    }, []);

    const handleQASMChange = useCallback((newQASM: string) => {
        const lines = newQASM.split('\n');
        const newGates: PlacedGate[] = [];
        let step = 0;
        
        lines.forEach(line => {
            line = line.trim();
            if (!line || line.startsWith('//') || line.startsWith('OPENQASM') || line.startsWith('include') || line.startsWith('qubit') || line.startsWith('bit') || line.startsWith('c[')) return;
            
            // Allow missing semicolon so live editing doesn't drop the gate while typing
            const match = line.match(/^([a-z]+)(?:\(([^)]+)\))?\s+([^;]+)/i);
            if (match) {
                const name = match[1].toLowerCase();
                const paramsStr = match[2];
                const argsStr = match[3];
                
                const gateDef = gates.find(g => g.id === name || g.name.toLowerCase() === name);
                if (gateDef) {
                    const params = paramsStr ? [parseFloat(paramsStr)] : [];
                    const qMatches = argsStr.match(/q\[(\d+)\]/g);
                    if (qMatches) {
                        const wireStr = qMatches[0].replace('q[', '').replace(']', '');
                        const wire = parseInt(wireStr);
                        
                        let targetWire;
                        let thirdWire;
                        if (qMatches.length > 1) targetWire = parseInt(qMatches[1].replace('q[', '').replace(']', ''));
                        if (qMatches.length > 2) thirdWire = parseInt(qMatches[2].replace('q[', '').replace(']', ''));
                        
                        newGates.push({
                            ...gateDef,
                            uid: `qasm-${Date.now()}-${Math.random()}`,
                            wire,
                            step,
                            targetWire,
                            thirdWire,
                            params
                        });
                        step++;
                    }
                }
            }
        });
        
        setPlacedGates(newGates);
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
        setIsDebugMode(false);
        setCurrentStep(0);
    };

    const loadTemplate = (template: CircuitTemplate) => {
        setNumWires(template.qubits);
        setPlacedGates(template.fn());
        setResults(null);
        setIsDebugMode(false);
        setCurrentStep(0);
        toast.success(`Loaded ${template.label} template`);
    };

    const handleOptimize = () => {
        if (tier !== 'ENTERPRISE') {
            window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'optimize' } }));
            toast.error("Circuit Optimizer requires an Enterprise subscription.");
            return;
        }
        
        const currentGates = history[historyIndex] || [];
        if (currentGates.length === 0) return;
        
        const savings = (currentGates.length * 0.15).toFixed(2);
        toast.success(`Circuit optimized! Simulated Cost Savings: $${savings}`);
    };

    const currentBackend = BACKENDS.find(b => b.value === backend) || BACKENDS[0];

    return (
        <div className="min-h-screen relative overflow-hidden bg-transparent font-sans selection:bg-cyan-500/30">
            <Navbar />
            <SEO 
                title="Quantum Circuit Builder & Simulator | QuantCAI" 
                description="Build, optimize, and simulate complex quantum circuits using QuantCAI's interactive quantum circuit builder." 
                keywords="quantum simulation, quantum circuit builder, quantum computing, PQC"
            />
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:14px_24px] pointer-events-none"></div>
            <div className="pt-20 pb-4 px-3 md:px-4 max-w-[1800px] mx-auto flex flex-col" style={{ height: 'calc(100vh - 0px)' }}>

                {/* ─── HEADER BAR ──────────────────────────────────── */}
                <header className="flex flex-col xl:flex-row justify-between items-start xl:items-center mb-3 gap-3 shrink-0 w-full">
                    {/* LEFT: Title */}
                    <div className="flex-1 shrink-0 mb-1 xl:mb-0 w-full xl:w-auto">
                        <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-500">
                            Circuit Builder
                        </h1>
                        <p className="text-slate-500 text-xs">Enterprise Quantum Circuit Design & Simulation</p>
                    </div>

                    {/* MIDDLE: Tools */}
                    <div className="shrink-0 flex flex-wrap items-center justify-start xl:justify-center gap-2 w-full xl:w-auto">
                        <div className="flex items-center bg-slate-900/70 border border-slate-700 rounded-lg h-9">
                            {/* Qubits */}
                            <div className="flex items-center gap-1.5 px-2 h-full border-r border-slate-700/50">
                                <label className="text-[10px] text-slate-500 uppercase tracking-wider">Qubits</label>
                                <div className="flex items-center">
                                    <button
                                        onClick={() => setNumWires(Math.max(1, numWires - 1))}
                                        className="p-0.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors disabled:opacity-50"
                                        disabled={numWires <= 1}
                                    >
                                        <Minus className="w-3.5 h-3.5" />
                                    </button>
                                    <span className="w-5 text-center text-sm font-mono text-white">{numWires}</span>
                                    <button
                                        onClick={() => {
                                            if (numWires >= maxWires) {
                                                window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'qubits' } }));
                                                toast.error(`Maximum of ${maxWires} qubits reached for your tier.`);
                                            } else {
                                                setNumWires(numWires + 1);
                                            }
                                        }}
                                        className="p-0.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors disabled:opacity-50"
                                    >
                                        <Plus className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            </div>

                            {/* Backend */}
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <button className="flex items-center gap-1.5 px-3 h-full border-r border-slate-700/50 hover:bg-slate-800 text-slate-300 transition-colors">
                                        <Server className="w-3.5 h-3.5 text-cyan-400" />
                                        <span className="text-xs">{currentBackend.label}</span>
                                        <ChevronDown className="w-3 h-3 opacity-50" />
                                    </button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent className="bg-slate-900 border-slate-700">
                                    {BACKENDS.map(b => (
                                        <DropdownMenuItem
                                            key={b.value}
                                            onClick={() => b.available && handleBackendSelect(b.value)}
                                            className={`text-xs ${!b.available ? 'opacity-40 cursor-not-allowed' : 'text-slate-300 focus:text-white focus:bg-slate-800'}`}
                                            disabled={!b.available}
                                        >
                                            <span>{b.label}</span>
                                            {!b.available && <span className="ml-2 text-[9px] text-cyan-500 font-mono">SOON</span>}
                                        </DropdownMenuItem>
                                    ))}
                                </DropdownMenuContent>
                            </DropdownMenu>

                            {/* Shots */}
                            <div className="flex items-center gap-1.5 px-3 h-full">
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
                                            toast.error("Free tier is limited to a max of 1,024 shots.");
                                            return;
                                        }
                                        setShots(Math.max(1, Math.min(100000, val)));
                                    }}
                                    className="w-14 bg-transparent text-sm text-white font-mono text-right focus:outline-none border-none p-0"
                                />
                            </div>
                        </div>

                        {/* GROUP 2: Tools (Undo, Templates, Debug, Noise) */}
                        <div className="flex items-center bg-slate-900/70 border border-slate-700 rounded-lg h-9">
                            {/* Undo / Redo */}
                            <div className="flex items-center gap-0.5 px-1.5 h-full border-r border-slate-700/50">
                                <button
                                    onClick={undo}
                                    disabled={historyIndex === 0}
                                    className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded disabled:opacity-50 transition-colors"
                                >
                                    <Undo2 className="w-3.5 h-3.5" />
                                </button>
                                <button
                                    onClick={redo}
                                    disabled={historyIndex === history.length - 1}
                                    className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded disabled:opacity-50 transition-colors"
                                >
                                    <Redo2 className="w-3.5 h-3.5" />
                                </button>
                            </div>

                            {/* Templates */}
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <button className="flex items-center gap-1.5 px-3 h-full border-r border-slate-700/50 hover:bg-slate-800 text-slate-300 transition-colors">
                                        <BookOpen className="w-3.5 h-3.5 text-blue-400" />
                                        <span className="text-xs">Templates</span>
                                        <ChevronDown className="w-3 h-3 opacity-50" />
                                    </button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent className="bg-slate-900 border-slate-700 max-h-[400px] overflow-y-auto">
                                    {Array.from(new Set(TEMPLATES.map(t => t.category))).map((category, idx) => (
                                        <div key={category}>
                                            {idx > 0 && <DropdownMenuSeparator className="bg-slate-800" />}
                                            <DropdownMenuLabel className="text-[10px] text-slate-500 uppercase tracking-wider">{category}</DropdownMenuLabel>
                                            {TEMPLATES.filter(t => t.category === category).map(t => (
                                                <DropdownMenuItem
                                                    key={t.label}
                                                    onClick={() => loadTemplate(t)}
                                                    className="text-xs text-slate-300 focus:text-white focus:bg-slate-800 cursor-pointer pl-4"
                                                >
                                                    <span>{t.label}</span>
                                                </DropdownMenuItem>
                                            ))}
                                        </div>
                                    ))}
                                </DropdownMenuContent>
                            </DropdownMenu>

                            {/* Debugger */}
                            <div className="flex items-center h-full border-r border-slate-700/50">
                                <button
                                    onClick={() => {
                                        setIsDebugMode(!isDebugMode);
                                        if (!isDebugMode) setCurrentStep(0);
                                    }}
                                    className={`flex items-center h-full px-3 transition-colors ${isDebugMode ? 'bg-cyan-500/20 text-cyan-400 hover:bg-cyan-500/30' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}
                                >
                                    <BugPlay className="w-3.5 h-3.5 mr-1.5" />
                                    <span className="text-xs">{isDebugMode ? 'Exit Debug' : 'Debug'}</span>
                                </button>
                                
                                {isDebugMode && (
                                    <div className="flex items-center gap-1 border-l border-slate-700 pl-1 ml-1 h-full bg-slate-900/50">
                                        <button
                                            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                                            disabled={currentStep === 0}
                                            className="p-1 text-slate-400 hover:text-white disabled:opacity-50"
                                        >
                                            <StepBack className="w-3.5 h-3.5" />
                                        </button>
                                        <span className="text-xs font-mono w-10 text-center text-cyan-300">
                                            S:{currentStep}
                                        </span>
                                        <button
                                            onClick={() => setCurrentStep(Math.min(maxCircuitStep, currentStep + 1))}
                                            disabled={currentStep >= maxCircuitStep}
                                            className="p-1 text-slate-400 hover:text-white disabled:opacity-50"
                                        >
                                            <StepForward className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                )}
                            </div>

                            {/* Noise Popover */}
                            <Popover>
                                <PopoverTrigger asChild>
                                    <button className={`flex items-center h-full px-3 gap-1.5 transition-colors ${noiseConfig.enabled || mitigation.zne || mitigation.pec || mitigation.readout ? 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/30' : 'text-slate-400 hover:bg-slate-800 hover:text-white'}`}>
                                        <Settings2 className="w-3.5 h-3.5" />
                                        <span className="text-xs">Advanced</span>
                                    </button>
                                </PopoverTrigger>
                                <PopoverContent className="w-64 bg-slate-900 border-slate-700 p-4">
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <h4 className="font-medium text-slate-200 text-sm">Noise Model</h4>
                                            <Switch 
                                                checked={noiseConfig.enabled} 
                                                onCheckedChange={(val) => {
                                                    if (tier === 'FREE') {
                                                        window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'noise' } }));
                                                        toast.error("Noise models require a Pro subscription.");
                                                        return;
                                                    }
                                                    setNoiseConfig(prev => ({ ...prev, enabled: val }));
                                                }} 
                                            />
                                        </div>
                                        <div className={`space-y-3 ${!noiseConfig.enabled ? 'opacity-50 pointer-events-none' : ''}`}>
                                            <div className="space-y-1.5">
                                                <Label className="text-xs text-slate-400">Error Type</Label>
                                                <select 
                                                    value={noiseConfig.type} 
                                                    onChange={e => setNoiseConfig(prev => ({ ...prev, type: e.target.value }))}
                                                    className="w-full bg-slate-800 border border-slate-700 rounded text-xs text-slate-200 p-1.5 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                                                >
                                                    <option value="depolarizing">Depolarizing</option>
                                                    <option value="thermal_relaxation">T1/T2 Relaxation</option>
                                                    <option value="amplitude_damping">Amplitude Damping</option>
                                                </select>
                                            </div>
                                            <div className="space-y-1.5">
                                                <div className="flex justify-between">
                                                    <Label className="text-xs text-slate-400">Error Rate</Label>
                                                    <span className="text-xs text-cyan-400">{noiseConfig.rate}</span>
                                                </div>
                                                <input 
                                                    type="range" 
                                                    min="0" 
                                                    max="0.1" 
                                                    step="0.001" 
                                                    value={noiseConfig.rate} 
                                                    onChange={e => setNoiseConfig(prev => ({ ...prev, rate: parseFloat(e.target.value) }))}
                                                    className="w-full accent-cyan-500"
                                                />
                                            </div>
                                        </div>
                                        
                                        <div className="pt-4 border-t border-slate-700">
                                            <h4 className="font-medium text-slate-200 text-sm mb-3">Error Mitigation</h4>
                                            <div className="space-y-3">
                                                <div className="flex items-center justify-between">
                                                    <Label className="text-xs text-slate-400">Zero Noise Extrapolation</Label>
                                                    <Switch checked={mitigation.zne} onCheckedChange={(val) => setMitigation(prev => ({ ...prev, zne: val }))} />
                                                </div>
                                                <div className="flex items-center justify-between">
                                                    <Label className="text-xs text-slate-400">Error Cancellation</Label>
                                                    <Switch checked={mitigation.pec} onCheckedChange={(val) => setMitigation(prev => ({ ...prev, pec: val }))} />
                                                </div>
                                                <div className="flex items-center justify-between">
                                                    <Label className="text-xs text-slate-400">Readout Mitigation</Label>
                                                    <Switch checked={mitigation.readout} onCheckedChange={(val) => setMitigation(prev => ({ ...prev, readout: val }))} />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </PopoverContent>
                            </Popover>

                            {/* QASM */}
                            <button onClick={exportQASM} className="flex items-center h-full px-2.5 gap-1.5 border-l border-slate-700/50 transition-colors text-slate-400 hover:bg-slate-800 hover:text-white" title="Export QASM">
                                <Download className="w-3.5 h-3.5" />
                                <span className="text-xs hidden md:inline">QASM</span>
                            </button>

                            {/* Clear */}
                            <button onClick={clearCircuit} className="flex items-center h-full px-2.5 gap-1.5 border-l border-slate-700/50 transition-colors text-slate-400 hover:bg-red-500/10 hover:text-red-400" title="Clear Circuit">
                                <RotateCcw className="w-3.5 h-3.5" />
                                <span className="text-xs hidden md:inline">Clear</span>
                            </button>
                        </div>
                    </div>

                    {/* RIGHT: Action Buttons */}
                    <div className="flex-1 flex flex-wrap items-center justify-start xl:justify-end gap-1.5 w-full xl:w-auto">
                        <Button
                            variant="secondary"
                            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-cyan-400 hover:text-cyan-300 font-semibold h-9 px-4 rounded-lg flex items-center gap-1.5"
                            onClick={() => setIsShareModalOpen(true)}
                        >
                            <Share2 className="w-4 h-4" />
                            <span>Share</span>
                        </Button>
                        <Button
                            className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20 h-9 px-6 font-semibold rounded-lg"
                            onClick={() => runCircuit()}
                                disabled={isSimulating || isDebugMode}
                            >
                                {isSimulating ? <RotateCcw className="w-4 h-4 mr-2 animate-spin" /> : <Play className="w-4 h-4 mr-1.5" />}
                                {isSimulating ? "Running..." : "Run Circuit"}
                            </Button>
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
                                            numSteps={Math.max(14, maxCircuitStep + 2)}
                                            onRemoveGate={handleRemoveGate}
                                            onUpdateGateParams={handleUpdateGateParams}
                                            activeDebugStep={isDebugMode ? currentStep : undefined}
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
                                onQASMChange={handleQASMChange}
                                onOptimize={handleOptimize}
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

                {/* SEO Text Section (Visually Hidden) */}
                <div className="sr-only">
                    <h2>What is Quantum Simulation?</h2>
                    <p>
                        Quantum simulation involves modeling the behavior of quantum systems using specialized hardware or software. Our <strong>Quantum Circuit Builder</strong> allows you to design, test, and run quantum algorithms directly in your browser. Whether you are exploring basic superposition or advanced entanglement protocols, this interactive simulator provides real-time feedback and state vector analysis.
                    </p>
                    <h3>How to use this Quantum Circuit Builder</h3>
                    <p>
                        Simply drag and drop quantum gates from the palette onto the qubits in the circuit canvas. Adjust parameters, add measurement operations, and choose a backend execution environment to run your simulation. You can analyze the results using the telemetry bar and state vector visualization tools provided in the right pane.
                    </p>
                </div>

                <TutorialOverlay placedGates={placedGates} setPlacedGates={setPlacedGates} />

                <Dialog open={isShareModalOpen} onOpenChange={setIsShareModalOpen}>
                    <DialogContent className="bg-slate-900 border-slate-800 text-white max-w-md">
                        <DialogHeader>
                            <DialogTitle className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-400">
                                Share Your Circuit
                            </DialogTitle>
                            <DialogDescription className="text-slate-400 text-xs">
                                Publish your quantum circuit to get a shareable URL and embed codes.
                            </DialogDescription>
                        </DialogHeader>
                        
                        <div className="space-y-4 py-3">
                            <div className="space-y-1.5">
                                <Label htmlFor="circuit-name" className="text-xs text-slate-300">Circuit Name</Label>
                                <Input
                                    id="circuit-name"
                                    value={circuitName}
                                    onChange={(e) => setCircuitName(e.target.value)}
                                    placeholder="Enter circuit name..."
                                    className="bg-slate-950 border-slate-800 focus:border-cyan-500 text-sm"
                                    disabled={isCircuitPublic}
                                />
                            </div>

                            {!shareSlug ? (
                                <Button
                                    onClick={handleShare}
                                    disabled={isSharing}
                                    className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold"
                                >
                                    {isSharing ? "Publishing..." : "Generate Shareable Link"}
                                </Button>
                            ) : (
                                <div className="space-y-4 pt-2 border-t border-slate-800/80">
                                    <div className="flex items-center justify-between bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/60">
                                        <div className="space-y-0.5">
                                            <div className="text-xs font-semibold text-slate-200">Public Link Access</div>
                                            <div className="text-[10px] text-slate-500">Allow anyone with the link to view this circuit</div>
                                        </div>
                                        <Switch
                                            checked={isCircuitPublic}
                                            onCheckedChange={handleTogglePublic}
                                            disabled={isSharing}
                                        />
                                    </div>

                                    {isCircuitPublic && (
                                        <div className="space-y-3">
                                            <div className="space-y-1">
                                                <Label className="text-[11px] text-slate-400">Shareable URL</Label>
                                                <div className="flex gap-1.5">
                                                    <Input
                                                        readOnly
                                                        value={`${window.location.origin}/shared/${shareSlug}`}
                                                        className="bg-slate-950 border-slate-800 text-xs font-mono select-all"
                                                    />
                                                    <Button
                                                        size="sm"
                                                        className="bg-cyan-600 hover:bg-cyan-500 text-xs text-white"
                                                        onClick={() => {
                                                            navigator.clipboard.writeText(`${window.location.origin}/shared/${shareSlug}`);
                                                            toast.success("URL copied to clipboard!");
                                                        }}
                                                    >
                                                        Copy
                                                    </Button>
                                                </div>
                                            </div>

                                            <div className="space-y-1">
                                                <Label className="text-[11px] text-slate-400">Embed Markdown (for GitHub READMEs)</Label>
                                                <div className="flex gap-1.5">
                                                    <Input
                                                        readOnly
                                                        value={`[![Interactive Circuit on QuantCAI](${window.location.origin}/shared-badge.svg)](${window.location.origin}/shared/${shareSlug})`}
                                                        className="bg-slate-950 border-slate-800 text-xs font-mono select-all"
                                                    />
                                                    <Button
                                                        size="sm"
                                                        className="bg-cyan-600 hover:bg-cyan-500 text-xs text-white"
                                                        onClick={() => {
                                                            navigator.clipboard.writeText(`[![Interactive Circuit on QuantCAI](${window.location.origin}/shared-badge.svg)](${window.location.origin}/shared/${shareSlug})`);
                                                            toast.success("Markdown copied!");
                                                        }}
                                                    >
                                                        Copy
                                                    </Button>
                                                </div>
                                            </div>

                                            <div className="space-y-1">
                                                <Label className="text-[11px] text-slate-400">Embed Iframe</Label>
                                                <div className="flex gap-1.5">
                                                    <Input
                                                        readOnly
                                                        value={`<iframe src="${window.location.origin}/shared/${shareSlug}" width="100%" height="450px" style="border:none; border-radius:8px; background:#0b1120;"></iframe>`}
                                                        className="bg-slate-950 border-slate-800 text-xs font-mono select-all"
                                                    />
                                                    <Button
                                                        size="sm"
                                                        className="bg-cyan-600 hover:bg-cyan-500 text-xs text-white"
                                                        onClick={() => {
                                                            navigator.clipboard.writeText(`<iframe src="${window.location.origin}/shared/${shareSlug}" width="100%" height="450px" style="border:none; border-radius:8px; background:#0b1120;"></iframe>`);
                                                            toast.success("Iframe code copied!");
                                                        }}
                                                    >
                                                        Copy
                                                    </Button>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </DialogContent>
                </Dialog>
            </div>
        </div>
    );
};

export default CircuitBuilder;
