
import { Button } from "@/components/ui/button";
import { QubitState } from '@/pages/QuantumStates';
import { Zap, RotateCw, Shuffle, Target } from 'lucide-react';

interface QuantumGatesProps {
  qubitState: QubitState;
  onApplyGate: (gateName: string) => void;
}

export const QuantumGates = ({ qubitState, onApplyGate }: QuantumGatesProps) => {

  // Gates call the API handler
  const applyXGate = () => onApplyGate('X (NOT)');
  const applyYGate = () => onApplyGate('Y');
  const applyZGate = () => onApplyGate('Z');
  const applyHadamardGate = () => onApplyGate('H (Hadamard)');
  const applyPhaseGate = () => onApplyGate('S (Phase)');
  const applyTGate = () => onApplyGate('T');

  const gates = [
    {
      name: 'X (NOT)',
      description: 'Flips qubit state',
      action: applyXGate,
      icon: Target,
      color: 'from-red-500 to-red-600 hover:from-red-600 hover:to-red-700'
    },
    {
      name: 'Y',
      description: 'Pauli-Y rotation',
      action: applyYGate,
      icon: RotateCw,
      color: 'from-green-500 to-green-600 hover:from-green-600 hover:to-green-700'
    },
    {
      name: 'Z',
      description: 'Phase flip',
      action: applyZGate,
      icon: Zap,
      color: 'from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700'
    },
    {
      name: 'H (Hadamard)',
      description: 'Creates superposition',
      action: applyHadamardGate,
      icon: Shuffle,
      color: 'from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700'
    },
    {
      name: 'S (Phase)',
      description: 'π/2 phase shift',
      action: applyPhaseGate,
      icon: RotateCw,
      color: 'from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700'
    },
    {
      name: 'T',
      description: 'π/4 phase shift',
      action: applyTGate,
      icon: RotateCw,
      color: 'from-pink-500 to-pink-600 hover:from-pink-600 hover:to-pink-700'
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {gates.map((gate) => (
        <Button
          key={gate.name}
          onClick={gate.action}
          className={`bg-gradient-to-r ${gate.color} text-white p-4 h-auto flex flex-col items-center gap-2 shadow-lg transform hover:scale-105 transition-all duration-200`}
        >
          <gate.icon className="h-6 w-6" />
          <div className="text-center">
            <div className="font-bold">{gate.name}</div>
            <div className="text-xs opacity-90">{gate.description}</div>
          </div>
        </Button>
      ))}
    </div>
  );
};
