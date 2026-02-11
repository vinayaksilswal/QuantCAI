import { usePageTracking } from '@/hooks/usePageTracking';
import { useAuth } from '@/hooks/useAuth';
import { toast } from "sonner";

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { QuantumVisualizer } from '@/components/QuantumVisualizer';
import { QuantumGates } from '@/components/QuantumGates';
import { QuantumStateDisplay } from '@/components/QuantumStateDisplay';
import { Atom, RotateCcw } from 'lucide-react';
import { api } from '@/lib/api';
import { useAI } from '@/hooks/useAI';
import { useEffect } from 'react';

export interface QubitState {
  alpha: number;
  beta: number;
  phase: number;
}

const QuantumStates = () => {
  usePageTracking('quantum-states');
  const { user } = useAuth();
  const { visualizerActions, ackVisualizerAction } = useAI();
  const [qubitState, setQubitState] = useState<QubitState>({
    alpha: 1,
    beta: 0,
    phase: 0
  });

  // AI Action Handler
  useEffect(() => {
    if (visualizerActions.length === 0) return;
    const action = visualizerActions[0];
    handleApplyGate(action.gate);
    ackVisualizerAction(action.id);
  }, [visualizerActions]);

  const handleApplyGate = async (gateName: string) => {
    try {
      // Reconstruct fully complex state for backend
      // We assume alpha is real mag, beta is mag * e^iPhase
      const backendInput = {
        alpha_real: qubitState.alpha,
        alpha_imag: 0,
        beta_real: qubitState.beta * Math.cos(qubitState.phase),
        beta_imag: qubitState.beta * Math.sin(qubitState.phase)
      };

      const data = await api.applyQuantumGate(backendInput, gateName);

      // Re-map back to mag/phase representation
      const alpha_mag = Math.sqrt(data.alpha_real ** 2 + data.alpha_imag ** 2);
      const beta_mag = Math.sqrt(data.beta_real ** 2 + data.beta_imag ** 2);

      const alpha_phase = Math.atan2(data.alpha_imag, data.alpha_real);
      const beta_phase = Math.atan2(data.beta_imag, data.beta_real);

      // Relative phase
      const rel_phase = beta_phase - alpha_phase;

      setQubitState({
        alpha: alpha_mag,
        beta: beta_mag,
        phase: rel_phase
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
