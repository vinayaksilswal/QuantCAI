import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '@/lib/api';
import { Navbar } from '@/components/Navbar';
import { CircuitGrid } from '@/components/CircuitGrid';
import { gates as baseGates } from '@/components/GatePalette';
import { PlacedGate } from '@/types/circuit';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Zap, Play, Download, Copy, ExternalLink, Shuffle, ArrowRight } from 'lucide-react';

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

export const SharedCircuit = () => {
    const { slug } = useParams<{ slug: string }>();
    const navigate = useNavigate();
    
    const [circuit, setCircuit] = useState<any>(null);
    const [placedGates, setPlacedGates] = useState<PlacedGate[]>([]);
    const [numWires, setNumWires] = useState(3);
    const [isLoading, setIsLoading] = useState(true);
    const [isSimulating, setIsSimulating] = useState(false);

    useEffect(() => {
        const fetchCircuit = async () => {
            if (!slug) return;
            try {
                const data = await api.getPublicCircuit(slug);
                setCircuit(data);
                
                // Parse placed gates and map base icons/colors
                if (data.circuit_data) {
                    const parsed: PlacedGate[] = JSON.parse(data.circuit_data);
                    const restored = parsed.map(g => {
                        const base = baseGates.find(bg => bg.id === g.id || bg.name.toLowerCase() === g.name.toLowerCase());
                        return {
                            ...g,
                            icon: base ? base.icon : Shuffle,
                            color: base ? base.color : 'from-blue-500 to-blue-600',
                            category: base ? base.category : 'single'
                        };
                    });
                    setPlacedGates(restored);
                    
                    // Determine wire count needed
                    if (restored.length > 0) {
                        const maxWire = Math.max(
                            ...restored.map(g => Math.max(g.wire, g.targetWire || 0, g.thirdWire || 0))
                        );
                        setNumWires(Math.max(3, maxWire + 1));
                    }
                }
            } catch (err: any) {
                console.error("Error fetching shared circuit:", err);
                toast.error(err.message || "Failed to load shared circuit.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchCircuit();
    }, [slug]);

    const maxCircuitStep = useMemo(() => {
        if (placedGates.length === 0) return 0;
        return Math.max(...placedGates.map(g => g.step));
    }, [placedGates]);

    const liveQASM = useMemo(
        () => generateQASM3(placedGates, numWires),
        [placedGates, numWires]
    );

    const handleRemix = () => {
        try {
            // Save current gates to builder history in localStorage
            localStorage.setItem('circuit-history', JSON.stringify([placedGates]));
            localStorage.setItem('circuit-history-index', '0');
            toast.success("Circuit loaded into builder! Redirecting...");
            setTimeout(() => {
                navigate('/circuit-builder');
            }, 800);
        } catch (err) {
            console.error("Failed to copy circuit to builder:", err);
            toast.error("Remix failed. Please try again.");
        }
    };

    const handleAnonymousRun = () => {
        toast.info("Simulation runs are reserved for registered developer accounts.", {
            description: "Sign up for a free account to execute and analyze this circuit.",
            action: {
                label: "Sign Up",
                onClick: () => navigate('/signup')
            }
        });
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-transparent">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-500" />
            </div>
        );
    }

    if (!circuit) {
        return (
            <div className="min-h-screen bg-transparent text-white flex flex-col items-center justify-center p-6">
                <Navbar />
                <h1 className="text-2xl font-bold text-red-400 mb-2">Circuit Unavailable</h1>
                <p className="text-slate-400 text-sm mb-6">This circuit is private or the link has expired.</p>
                <Button asChild className="bg-cyan-600 hover:bg-cyan-500">
                    <Link to="/circuit-builder">Back to Builder</Link>
                </Button>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-transparent text-white font-sans flex flex-col">
            <Navbar />
            
            <main className="flex-1 pt-24 pb-8 px-4 md:px-8 max-w-7xl mx-auto w-full flex flex-col gap-6">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/40 p-6 rounded-xl border border-slate-800/80 backdrop-blur">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <span className="bg-cyan-500/10 text-cyan-400 text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">
                                Shared Design
                            </span>
                            <span className="text-slate-500 text-xs">
                                Created on {new Date(circuit.created_at).toLocaleDateString()}
                            </span>
                        </div>
                        <h1 className="text-2xl font-extrabold text-white">
                            {circuit.name}
                        </h1>
                        <p className="text-xs text-slate-400 mt-1">
                            Designed by <span className="text-cyan-400 font-semibold">{circuit.author_name}</span>
                        </p>
                    </div>
                    
                    <div className="flex gap-2">
                        <Button 
                            onClick={handleRemix}
                            className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold h-10 px-5 flex items-center gap-2 rounded-lg shadow-lg shadow-cyan-500/15"
                        >
                            <Zap className="w-4 h-4 text-yellow-300" />
                            <span>Remix Circuit</span>
                        </Button>
                    </div>
                </div>

                {/* Circuit Grid Viewer */}
                <Card className="bg-slate-900/60 border-slate-800/80 backdrop-blur-sm overflow-hidden flex flex-col">
                    <CardHeader className="py-4 px-6 border-b border-slate-800/50 flex flex-row items-center justify-between">
                        <div>
                            <CardTitle className="text-sm font-semibold text-slate-300">Read-Only Circuit Board</CardTitle>
                            <CardDescription className="text-xs text-slate-500">Interactive schematic visualization of the quantum gates layout.</CardDescription>
                        </div>
                        <Button
                            variant="ghost"
                            onClick={handleAnonymousRun}
                            className="h-8 text-xs text-slate-400 hover:text-white hover:bg-slate-800 flex items-center gap-1.5"
                        >
                            <Play className="w-3.5 h-3.5" />
                            <span>Simulate</span>
                        </Button>
                    </CardHeader>
                    <CardContent className="p-6 overflow-auto">
                        <CircuitGrid
                            placedGates={placedGates}
                            numWires={numWires}
                            numSteps={Math.max(14, maxCircuitStep + 2)}
                        />
                    </CardContent>
                </Card>

                {/* Lower Panels */}
                <div className="grid md:grid-cols-3 gap-6">
                    {/* OpenQASM Panel */}
                    <Card className="md:col-span-2 bg-slate-900/60 border-slate-800/80 backdrop-blur flex flex-col h-[300px]">
                        <CardHeader className="py-3.5 px-5 border-b border-slate-800/50 flex flex-row items-center justify-between">
                            <CardTitle className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                                OpenQASM 3.0 Code
                            </CardTitle>
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 w-7 p-0 text-slate-400 hover:text-white"
                                onClick={() => {
                                    navigator.clipboard.writeText(liveQASM);
                                    toast.success("OpenQASM code copied!");
                                }}
                            >
                                <Copy className="w-4.5 h-4.5" />
                            </Button>
                        </CardHeader>
                        <CardContent className="p-4 flex-1 overflow-auto">
                            <pre className="text-xs font-mono text-cyan-200/90 whitespace-pre-wrap select-all">
                                {liveQASM}
                            </pre>
                        </CardContent>
                    </Card>

                    {/* Viral CTA Panel */}
                    <Card className="bg-gradient-to-br from-slate-900 to-indigo-950/40 border-slate-800 backdrop-blur p-6 flex flex-col justify-between h-[300px]">
                        <div className="space-y-3">
                            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20">
                                <Zap className="w-5 h-5 text-cyan-400" />
                            </div>
                            <h3 className="text-lg font-bold text-white leading-snug">
                                Build & Simulate Your Own Circuits
                            </h3>
                            <p className="text-slate-400 text-xs leading-relaxed">
                                Join QuantCAI to access enterprise features: high-fidelity noise models, statevector analyzers, one-click OpenQASM translation, and live deployment on physical QPUs.
                            </p>
                        </div>
                        <Button 
                            asChild
                            className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-semibold mt-4 flex items-center gap-1.5"
                        >
                            <Link to="/signup">
                                <span>Get Started for Free</span>
                                <ArrowRight className="w-4 h-4" />
                            </Link>
                        </Button>
                    </Card>
                </div>
            </main>
        </div>
    );
};

export default SharedCircuit;
