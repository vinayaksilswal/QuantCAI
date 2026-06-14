import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from '@/hooks/useAuth';
import { usePageTracking } from '@/hooks/usePageTracking';
import { Lock, GitMerge, Cpu, Infinity, CheckCircle2, AlertTriangle, ArrowRight, Code } from 'lucide-react';

const LearnGates = () => {
  usePageTracking('learn-gates');
  const navigate = useNavigate();
  const { subscriptionPlan } = useAuth();

  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizCorrect, setQuizCorrect] = useState<boolean | null>(null);

  const isPro = subscriptionPlan === 'pro' || subscriptionPlan === 'enterprise';

  const quiz = {
    question: "Which quantum gate is primarily used to put a qubit into a state of equal superposition?",
    options: [
      "X (Pauli-X) Gate",
      "H (Hadamard) Gate",
      "Z (Pauli-Z) Gate",
      "CNOT Gate"
    ],
    correctIndex: 1
  };

  const handleSelectOption = (index: number) => {
    if (quizSubmitted) return;
    setSelectedOption(index);
  };

  const handleSubmitQuiz = () => {
    if (selectedOption === null || quizSubmitted) return;
    const correct = selectedOption === quiz.correctIndex;
    setQuizCorrect(correct);
    setQuizSubmitted(true);
  };

  if (!isPro) {
    return (
      <div className="min-h-screen relative flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center pt-24 pb-20 px-6">
          <Card className="max-w-md w-full bg-slate-900/80 border-slate-800 shadow-2xl backdrop-blur-md text-center p-8">
            <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <Lock className="w-8 h-8 text-blue-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-4">Pro Access Required</h2>
            <p className="text-slate-400 mb-8">
              The "Quantum Gates & Circuits" module is part of the QuantCAI Pro Curriculum. Upgrade your workspace to unlock advanced tutorials, interactive circuits, and post-quantum concepts.
            </p>
            <div className="space-y-4">
              <Button onClick={() => navigate('/profile')} className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold py-2.5">
                Upgrade to Pro
              </Button>
              <Button onClick={() => navigate('/learn/qubits')} variant="outline" className="w-full border-slate-700 bg-transparent hover:bg-slate-800 text-slate-300">
                Go Back
              </Button>
            </div>
          </Card>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen relative">
      <Navbar />
      
      <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Module 2: <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Quantum Gates & Circuits</span>
          </h1>
          <p className="text-xl text-gray-300 leading-relaxed font-mono tracking-widest uppercase text-sm">
            Pro Curriculum
          </p>
        </div>

        <div className="space-y-12">
          <section>
            <div className="flex items-center mb-6">
              <Cpu className="h-8 w-8 text-yellow-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">Unitary Operations</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed mb-6">
                  In quantum mechanics, operations on quantum states are described by unitary transformations, represented by 
                  unitary matrices. These operations preserve the normalization of the quantum state and are reversible. A unitary 
                  matrix U has the property that U†U = I, where U† is the conjugate transpose.
                </p>
                <h4 className="text-lg font-semibold text-blue-400 mb-3">Qiskit: Define Operators</h4>
                <div className="bg-slate-900 p-4 rounded-lg overflow-x-auto">
                  <pre className="text-green-400 text-sm">
{`from qiskit.quantum_info import Operator
from numpy import sqrt

X = Operator([[0, 1], [1, 0]])
Y = Operator([[0, -1.0j], [1.0j, 0]])
Z = Operator([[1, 0], [0, -1]])
H = Operator([[1 / sqrt(2), 1 / sqrt(2)], [1 / sqrt(2), -1 / sqrt(2)]])
`}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </section>

          <section>
            <div className="flex items-center mb-6">
              <GitMerge className="h-8 w-8 text-blue-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">Hadamard (H) Gate</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed">
                  The Hadamard gate acts on a single qubit, mapping the basis states |0⟩ to ( |0⟩ + |1⟩ ) / √2 and |1⟩ to ( |0⟩ - |1⟩ ) / √2. This creates an equal superposition of the two computational basis states, making it the fundamental starting gate for almost all quantum algorithms.
                </p>
              </CardContent>
            </Card>
          </section>

          <section>
            <div className="flex items-center mb-6">
              <Cpu className="h-8 w-8 text-purple-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">CNOT (Controlled-NOT) Gate</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed">
                  The Controlled-NOT (CNOT or CX) gate is a 2-qubit gate that performs the NOT operation on the second qubit (target) only if the first qubit (control) is in the state |1⟩. It is represented by a 4x4 matrix and is crucial for creating quantum entanglement.
                </p>
              </CardContent>
            </Card>
          </section>

          <section>
            <div className="flex items-center mb-6">
              <Infinity className="h-8 w-8 text-green-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">Quantum Entanglement & Bell States</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed">
                  Quantum entanglement is a physical phenomenon that occurs when a pair or group of particles are generated, interact, or share spatial proximity in a way such that the quantum state of each particle cannot be described independently of the state of the others. By applying a Hadamard gate to qubit 0, followed by a CNOT gate with qubit 0 as control and qubit 1 as target, we create the Bell state (|00⟩ + |11⟩)/√2.
                </p>
              </CardContent>
            </Card>
          </section>

          <section>
            <div className="flex items-center mb-6">
              <Code className="h-8 w-8 text-cyan-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">Qiskit: Creating a Bell State</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed mb-6">Here is how you can create and measure entanglement using Qiskit:</p>
                
                <div className="bg-slate-900 p-4 rounded-lg overflow-x-auto">
                  <pre className="text-green-400 text-sm">
{`from qiskit import QuantumCircuit
from qiskit.visualization import plot_histogram

# Create a Quantum Circuit acting on a quantum register of 2 qubits
circ = QuantumCircuit(2)

# Add a H gate on qubit 0, putting it in superposition.
circ.h(0)

# Add a CX (CNOT) gate on control qubit 0 and target qubit 1, putting
# the qubits in a Bell state.
circ.cx(0, 1)

# Measure both qubits
circ.measure_all()

# Draw the circuit
circ.draw('mpl')`}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </section>
        </div>

        {/* Quiz Section */}
        <div className="mt-16 pt-8 border-t border-slate-800">
          <h3 className="text-2xl font-bold text-white mb-6">Concept Check</h3>
          <Card className="bg-slate-900/50 border-slate-800 shadow-2xl">
            <div className="p-6 space-y-5">
              <p className="text-sm font-semibold text-slate-200">
                {quiz.question}
              </p>

              <div className="space-y-2">
                {quiz.options.map((opt, oIdx) => {
                  const isSelected = selectedOption === oIdx;
                  return (
                    <button
                      key={oIdx}
                      onClick={() => handleSelectOption(oIdx)}
                      disabled={quizSubmitted}
                      className={`w-full text-left text-xs p-3.5 rounded-xl border transition-all ${
                        isSelected 
                          ? "bg-blue-600/20 border-blue-500 text-white font-medium" 
                          : "bg-slate-950/50 border-slate-800 text-slate-400 hover:bg-slate-900/60 hover:text-white hover:border-slate-700"
                      }`}
                    >
                      {opt}
                    </button>
                  );
                })}
              </div>

              {quizSubmitted ? (
                <div className={`p-4 rounded-xl border flex gap-3 text-xs leading-relaxed ${
                  quizCorrect 
                    ? "bg-emerald-950/20 border-emerald-900/50 text-emerald-300" 
                    : "bg-rose-950/20 border-rose-900/50 text-rose-300"
                }`}>
                  {quizCorrect ? (
                    <div className="w-full flex items-center justify-between">
                      <div className="flex gap-3 items-center">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                        <div>
                          <p className="font-bold">Correct!</p>
                          <p className="mt-0.5">You're getting the hang of Quantum Gates.</p>
                        </div>
                      </div>
                      <Button 
                        onClick={() => navigate('/learn/pqc')}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2"
                      >
                        Next: Post-Quantum Cryptography <ArrowRight className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <div className="flex gap-3">
                      <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
                      <div>
                        <p className="font-bold">Incorrect</p>
                        <p className="mt-0.5">Review the chapter content on Quantum Gates to try again.</p>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <Button
                  onClick={handleSubmitQuiz}
                  disabled={selectedOption === null}
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-xl font-bold shadow-lg shadow-blue-500/10 disabled:opacity-50"
                >
                  Submit Answer
                </Button>
              )}
            </div>
          </Card>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default LearnGates;
