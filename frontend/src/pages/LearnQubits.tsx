import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from '@/hooks/useAuth';
import { usePageTracking } from '@/hooks/usePageTracking';
import { useAI } from '@/hooks/useAI';
import { Lock, BookOpen, Atom, Zap, CheckCircle2, AlertTriangle, ArrowRight, Code } from 'lucide-react';

const LearnQubits = () => {
  usePageTracking('learn-qubits');
  const navigate = useNavigate();
  const { subscriptionPlan } = useAuth();
  const { updateClientContext } = useAI();

  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizCorrect, setQuizCorrect] = useState<boolean | null>(null);



  const quiz = {
    question: "What quantum phenomenon allows a qubit to be in a linear combination of |0⟩ and |1⟩ states simultaneously?",
    options: [
      "Quantum Decoherence",
      "Quantum Superposition",
      "Quantum Entanglement",
      "Classical Teleportation"
    ],
    correctIndex: 1
  };

  // Report page context to AI assistant
  useEffect(() => {
    const quizState = quizSubmitted ? (quizCorrect ? 'correct' : 'incorrect') : (selectedOption !== null ? 'in_progress' : 'unanswered');
    updateClientContext('learn', {
      page: 'learn/qubits',
      page_title: 'Understanding Qubits',
      quiz_state: quizState,
      selected_option: selectedOption,
    });
  }, [quizSubmitted, quizCorrect, selectedOption, updateClientContext]);

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



  return (
    <div className="min-h-screen relative">
      <Navbar />
      
      <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Module 1: <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Introduction to Qubits</span>
          </h1>
          <p className="text-xl text-gray-300 leading-relaxed font-mono tracking-widest uppercase text-sm">
            Pro Curriculum
          </p>
        </div>

        <div className="space-y-12">


          <section>
            <div className="flex items-center mb-6">
              <Atom className="h-8 w-8 text-purple-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">Bloch Sphere Representation</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed">
                  The Bloch sphere is a geometrical representation of the pure state space of a two-level quantum mechanical system (qubit). Any pure qubit state can be written as |ψ⟩ = cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩, mapping to a point on the surface of a unit sphere. The north pole represents |0⟩, the south pole represents |1⟩, and points on the equator represent equal superpositions (like |+⟩ and |−⟩).
                </p>
              </CardContent>
            </Card>
          </section>

          <section>
            <div className="flex items-center mb-6">
              <BookOpen className="h-8 w-8 text-green-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">Dirac Ket/Bra Notation</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed">
                  Dirac notation (bra-ket notation) is the standard notation for describing quantum states in quantum mechanics. A column vector representing a quantum state is called a ket, written as |ψ⟩. A row vector (the conjugate transpose of a ket) is called a bra, written as ⟨ψ|. The inner product (dot product) of two states is ⟨φ|ψ⟩, and the outer product is |ψ⟩⟨φ|.
                </p>
              </CardContent>
            </Card>
          </section>

          <section>
            <div className="flex items-center mb-6">
              <Code className="h-8 w-8 text-cyan-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">Qiskit: State Vectors</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed mb-6">First, make sure you have Qiskit installed: <code>pip install qiskit matplotlib numpy</code>. Then we can define state vectors.</p>
                
                <div className="bg-slate-900 p-4 rounded-lg overflow-x-auto">
                  <pre className="text-green-400 text-sm">
{`from qiskit.quantum_info import Statevector
from numpy import sqrt

# Define state vectors
u = Statevector([1 / sqrt(2), 1 / sqrt(2)])
v = Statevector([(1 + 2j) / 3, -2 / 3])
w = Statevector([1 / 3, 2 / 3])

# Check validity
display(u.is_valid())  # True
display(w.is_valid())  # False

# Measure
v.measure()  # e.g., (1, Statevector([0.+0.j, -1.+0.j], dims=(2,)))`}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </section>

          <section>
            <div className="flex items-center mb-6">
              <Code className="h-8 w-8 text-cyan-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">Qiskit: Bloch Sphere</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed mb-6">We can visualize the Bloch Sphere using Qiskit's built-in plotting tools:</p>
                
                <div className="bg-slate-900 p-4 rounded-lg overflow-x-auto">
                  <pre className="text-green-400 text-sm">
{`from qiskit.visualization import plot_bloch_multivector
from qiskit.quantum_info import Statevector
import math

# Create a state vector pointing to |0>
state = Statevector([1, 0])
plot_bloch_multivector(state)

# Create an equal superposition state |+>
state_plus = Statevector([1/math.sqrt(2), 1/math.sqrt(2)])
plot_bloch_multivector(state_plus)`}
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
                          <p className="mt-0.5">Superb. You have successfully mapped the concepts of superposition.</p>
                        </div>
                      </div>
                      <Button 
                        onClick={() => navigate('/learn/gates')}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2"
                      >
                        Next: Quantum Gates <ArrowRight className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <div className="flex gap-3">
                      <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
                      <div>
                        <p className="font-bold">Incorrect</p>
                        <p className="mt-0.5">Review the chapter content on superposition to try again.</p>
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

export default LearnQubits;
