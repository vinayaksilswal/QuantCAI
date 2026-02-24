import { useAI } from "../hooks/useAI";
import { Button } from "./ui/button";
import { X, Atom } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { QuantumVisualizer } from "./QuantumVisualizer";
import { QuantumGates } from "./QuantumGates";
import { QuantumStateDisplay } from "./QuantumStateDisplay";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { api, API_BASE } from "@/lib/api";

// Reusing QubitState interface
export interface QubitState {
    alpha: number;
    beta: number;
    phase: number;
}

export const TeachingOverlay = () => {
    const { activeTool, closeTool } = useAI();

    // Local state for Quantum State Tool
    const [qubitState, setQubitState] = useState<QubitState>({
        alpha: 1,
        beta: 0,
        phase: 0
    });

    // Reset state when tool opens
    useEffect(() => {
        if (activeTool === 'quantum-states') {
            setQubitState({ alpha: 1, beta: 0, phase: 0 });
        }
    }, [activeTool]);

    const handleApplyGate = async (gateName: string) => {
        const token = api.getAuthToken();
        if (!token) {
            toast.error("Please login to use tools");
            return;
        }
        try {
            const response = await fetch(`${API_BASE}/api/quantum/state/apply`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    current_state: qubitState,
                    gate: gateName
                })
            });

            if (!response.ok) throw new Error("Failed to calculate state");

            const data = await response.json();
            setQubitState({
                alpha: data.alpha_real,
                beta: data.beta_real,
                phase: 0
            });
        } catch (e) {
            toast.error("Failed to apply gate");
            console.error(e);
        }
    };

    if (!activeTool) return null;

    return (
        <div className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm flex items-center justify-center p-8">
            <div className="relative w-full max-w-5xl max-h-[90vh] overflow-auto">
                <Button
                    variant="destructive"
                    size="icon"
                    className="absolute top-4 right-4 z-50 rounded-full"
                    onClick={closeTool}
                >
                    <X className="h-6 w-6" />
                </Button>

                {activeTool === 'quantum-states' && (
                    <Card className="bg-background/95 border-primary/50 shadow-2xl">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Atom className="h-6 w-6 text-primary" />
                                Quantum State Teaching: Superposition & Gates
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold">Visualizer</h3>
                                <QuantumVisualizer qubitState={qubitState} />
                                <QuantumStateDisplay qubitState={qubitState} />
                            </div>
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold">Apply Gates</h3>
                                <p className="text-muted-foreground text-sm">
                                    Click a gate to see how it affects the qubit state on the Bloch Sphere.
                                </p>
                                <QuantumGates qubitState={qubitState} onApplyGate={handleApplyGate} />
                            </div>
                        </CardContent>
                    </Card>
                )}

                {activeTool === 'circuit-builder' && (
                    <Card className="bg-background/95 border-primary/50 shadow-2xl h-[80vh]">
                        <CardHeader>
                            <CardTitle>Circuit Builder (Teaching Mode)</CardTitle>
                        </CardHeader>
                        <CardContent className="h-full flex items-center justify-center">
                            <p className="text-xl text-muted-foreground">
                                Circuit Builder overlay coming soon! (Use the main page for now)
                            </p>
                            {/* To implement full circuit builder here, we'd need to refactor CircuitBuilder page into a component */}
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    );
};
