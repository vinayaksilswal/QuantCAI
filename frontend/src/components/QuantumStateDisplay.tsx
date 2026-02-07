
import { QubitState } from '@/pages/QuantumStates';

interface QuantumStateDisplayProps {
  qubitState: QubitState;
}

export const QuantumStateDisplay = ({ qubitState }: QuantumStateDisplayProps) => {
  const { alpha, beta, phase } = qubitState;
  
  // Calculate probabilities
  const prob0 = Math.abs(alpha) ** 2;
  const prob1 = Math.abs(beta) ** 2;
  
  // Format complex numbers
  const formatComplex = (real: number, imag: number = 0) => {
    if (Math.abs(imag) < 0.001) {
      return real.toFixed(3);
    }
    const sign = imag >= 0 ? '+' : '-';
    return `${real.toFixed(3)} ${sign} ${Math.abs(imag).toFixed(3)}i`;
  };

  const alphaReal = alpha * Math.cos(phase);
  const alphaImag = alpha * Math.sin(phase);
  const betaReal = beta * Math.cos(phase);
  const betaImag = beta * Math.sin(phase);

  return (
    <div className="space-y-4">
      {/* Quantum State Equation */}
      <div className="bg-black/30 p-4 rounded-lg border border-blue-400/30">
        <div className="text-center text-white font-mono text-lg">
          |ψ⟩ = {formatComplex(alphaReal, alphaImag)}|0⟩ + {formatComplex(betaReal, betaImag)}|1⟩
        </div>
      </div>

      {/* Probabilities */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-blue-200">P(|0⟩):</span>
          <span className="text-white font-mono">{prob0.toFixed(4)}</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-3">
          <div 
            className="bg-blue-500 h-3 rounded-full transition-all duration-300" 
            style={{ width: `${prob0 * 100}%` }}
          ></div>
        </div>
        
        <div className="flex justify-between items-center">
          <span className="text-red-200">P(|1⟩):</span>
          <span className="text-white font-mono">{prob1.toFixed(4)}</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-3">
          <div 
            className="bg-red-500 h-3 rounded-full transition-all duration-300" 
            style={{ width: `${prob1 * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Additional Information */}
      <div className="text-sm space-y-1 text-blue-200">
        <div>Phase: {phase.toFixed(3)} rad</div>
        <div>|α|: {Math.abs(alpha).toFixed(3)}</div>
        <div>|β|: {Math.abs(beta).toFixed(3)}</div>
      </div>
    </div>
  );
};
