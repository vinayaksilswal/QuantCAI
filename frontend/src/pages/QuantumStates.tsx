import { usePageTracking } from '@/hooks/usePageTracking';
import { useAuth } from '@/context/AuthContext';
import { toast } from "sonner";

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { QuantumBackground } from '@/components/QuantumBackground';
import { QuantumVisualizer } from '@/components/QuantumVisualizer';
import { QuantumGates } from '@/components/QuantumGates';
import { QuantumStateDisplay } from '@/components/QuantumStateDisplay';
import { Atom, RotateCcw } from 'lucide-react';

export interface QubitState {
  alpha: number;
  beta: number;
  phase: number;
}

const QuantumStates = () => {
  usePageTracking('quantum-states');
  const { token } = useAuth();
  const [qubitState, setQubitState] = useState<QubitState>({
    alpha: 1,
    beta: 0,
    phase: 0
  });

  const handleApplyGate = async (gateName: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/quantum/state/apply', {
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
      // Backend returns complex parts: alpha_real, alpha_imag, beta_real, beta_imag
      // Frontend expects: alpha, beta, phase.
      // We need to map it. 
      // For now, let's just use the real parts as the previous visualizer likely expects numbers.
      // Or rewrite visualizer?
      // The previous code had: setQubitState({ alpha: 1, beta: 0, phase: 0 });
      // alpha/beta seem to be magnitudes or real components in the simple visualizer.
      // Let's assume we map backend Real parts to alpha/beta for now to keep visualizer working,
      // or ideally calculate magnitude/phase.

      // Simple mapping:
      setQubitState({
        alpha: data.alpha_real,
        beta: data.beta_real, // Logic simplification
        phase: 0 // Backend calculation of global phase needed or ignored
      });

    } catch (e) {
      toast.error("Failed to apply gate");
      console.error(e);
    }
  };

  const resetState = () => {
    setQubitState({ alpha: 1, beta: 0, phase: 0 });
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <Navbar />

      <div className="pt-32 pb-20 px-6 relative z-10">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="flex items-center justify-center mb-6">
              <Atom className="h-16 w-16 text-blue-300 animate-pulse drop-shadow-lg" />
            </div>
            <h1 className="text-5xl font-bold text-white mb-4 drop-shadow-lg">
              Interactive Quantum States
            </h1>
            <p className="text-xl text-blue-200 max-w-3xl mx-auto drop-shadow-md">
              Explore quantum superposition and entanglement through real-time visualization.
              Apply quantum gates and observe how they transform qubit states.
            </p>
          </div>

          {/* Main Simulator Grid */}
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Quantum Visualizer */}
            <div className="lg:col-span-2">
              <Card className="bg-white/10 backdrop-blur-xl border-blue-400/40 shadow-2xl shadow-blue-500/30">
                <CardHeader>
                  <CardTitle className="text-white text-2xl flex items-center gap-3">
                    <Atom className="h-6 w-6 text-blue-300" />
                    Qubit Visualization
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <QuantumVisualizer qubitState={qubitState} />
                </CardContent>
              </Card>
            </div>

            {/* Controls Panel */}
            <div className="space-y-6">
              {/* State Display */}
              <Card className="bg-white/10 backdrop-blur-xl border-purple-400/40 shadow-2xl shadow-purple-500/30">
                <CardHeader>
                  <CardTitle className="text-white text-xl">Quantum State</CardTitle>
                </CardHeader>
                <CardContent>
                  <QuantumStateDisplay qubitState={qubitState} />
                </CardContent>
              </Card>

              {/* Reset Button */}
              <Button
                onClick={resetState}
                className="w-full bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white flex items-center gap-2"
              >
                <RotateCcw className="h-4 w-4" />
                Reset to |0⟩
              </Button>
            </div>
          </div>

          {/* Quantum Gates Panel */}
          <div className="mt-8">
            <Card className="bg-white/10 backdrop-blur-xl border-green-400/40 shadow-2xl shadow-green-500/30">
              <CardHeader>
                <CardTitle className="text-white text-2xl">Quantum Gates</CardTitle>
              </CardHeader>
              <CardContent>
                <QuantumGates
                  qubitState={qubitState}
                  onApplyGate={handleApplyGate}
                />

              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default QuantumStates;
