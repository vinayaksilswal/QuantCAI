import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from '@/hooks/useAuth';
import { usePageTracking } from '@/hooks/usePageTracking';
import { useAI } from '@/hooks/useAI';
import { Lock, AlertTriangle, ShieldCheck, FileCheck, CheckCircle2, Award, Code } from 'lucide-react';

const LearnPQC = () => {
  usePageTracking('learn-pqc');
  const navigate = useNavigate();
  const { subscriptionPlan } = useAuth();

  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizCorrect, setQuizCorrect] = useState<boolean | null>(null);

  const isPro = subscriptionPlan === 'pro' || subscriptionPlan === 'enterprise';
  const { updateClientContext } = useAI();

  const quiz = {
    question: "Which cryptographic standard specifies ML-KEM for quantum-safe key exchange?",
    options: [
      "FIPS 197",
      "FIPS 203",
      "FIPS 204",
      "FIPS 140-3"
    ],
    correctIndex: 1
  };

  // Report page context to AI assistant
  useEffect(() => {
    const quizState = quizSubmitted ? (quizCorrect ? 'correct' : 'incorrect') : (selectedOption !== null ? 'in_progress' : 'unanswered');
    updateClientContext('learn', {
      page: 'learn/pqc',
      page_title: 'Post-Quantum Cryptography',
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
              The "Post-Quantum Cryptography" module is part of the QuantCAI Pro Curriculum. Upgrade your workspace to unlock advanced tutorials and PQC scanners.
            </p>
            <div className="space-y-4">
              <Button onClick={() => navigate('/profile')} className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold py-2.5">
                Upgrade to Pro
              </Button>
              <Button onClick={() => navigate('/learn/gates')} variant="outline" className="w-full border-slate-700 bg-transparent hover:bg-slate-800 text-slate-300">
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
            Module 3: <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Post-Quantum Cryptography</span>
          </h1>
          <p className="text-xl text-gray-300 leading-relaxed font-mono tracking-widest uppercase text-sm">
            Pro Curriculum
          </p>
        </div>

        <div className="space-y-12">
          <section>
            <div className="flex items-center mb-6">
              <AlertTriangle className="h-8 w-8 text-rose-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">Shor's Algorithm & Threat Vector</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed">
                  Shor's algorithm is a polynomial-time quantum algorithm for integer factorization. Since public-key cryptography schemes (like RSA and ECC) rely on the difficulty of integer factorization or discrete logarithms, Shor's algorithm running on a sufficiently large Cryptographically Relevant Quantum Computer (CRQC) will break all classical secure communications.
                </p>
              </CardContent>
            </Card>
          </section>

          <section>
            <div className="flex items-center mb-6">
              <Code className="h-8 w-8 text-cyan-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">Qiskit: Shor's Algorithm</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed mb-6">Qiskit Algorithms previously included a direct implementation of Shor's algorithm for educational purposes, simulating period finding:</p>
                
                <div className="bg-slate-900 p-4 rounded-lg overflow-x-auto">
                  <pre className="text-green-400 text-sm">
{`from qiskit.algorithms import Shor
from qiskit.utils import QuantumInstance
from qiskit import Aer

# We want to factor N = 15
N = 15
backend = Aer.get_backend('aer_simulator')
quantum_instance = QuantumInstance(backend, shots=1024)

# Run Shor's algorithm
shor = Shor(quantum_instance=quantum_instance)
result = shor.factor(N)

print(f"Factors of {N}: {result.factors}")
# Output: Factors of 15: [[3, 5]]`}
                  </pre>
                </div>
              </CardContent>
            </Card>
          </section>

          <section>
            <div className="flex items-center mb-6">
              <ShieldCheck className="h-8 w-8 text-emerald-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">NIST PQC Standardization</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed">
                  Recognizing the quantum threat, the National Institute of Standards and Technology (NIST) initiated a process in 2016 to solicit, evaluate, and standardize quantum-resistant public-key cryptographic algorithms. The goal is to identify algorithms that remain secure against both classical and quantum computers.
                </p>
              </CardContent>
            </Card>
          </section>

          <section>
            <div className="flex items-center mb-6">
              <FileCheck className="h-8 w-8 text-blue-400 mr-4" />
              <h2 className="text-3xl font-bold text-white">FIPS 203 (ML-KEM) & FIPS 204 (ML-DSA)</h2>
            </div>
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <p className="text-gray-300 leading-relaxed">
                  In August 2024, NIST released its first finalized post-quantum standards. FIPS 203 defines ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism), designed for secure key exchange. FIPS 204 defines ML-DSA (Module-Lattice-Based Digital Signature Algorithm), designed for authentication and digital signatures. Organizations are mandated to transition to these standards before 2030.
                </p>
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
                          <p className="mt-0.5">Congratulations on completing the QuantCAI Curriculum!</p>
                        </div>
                      </div>
                      <Button 
                        onClick={() => navigate('/profile')}
                        className="bg-purple-600 hover:bg-purple-500 text-white gap-2"
                      >
                        <Award className="w-4 h-4" /> Go to Dashboard
                      </Button>
                    </div>
                  ) : (
                    <div className="flex gap-3">
                      <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
                      <div>
                        <p className="font-bold">Incorrect</p>
                        <p className="mt-0.5">Review the chapter content on PQC to try again.</p>
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

export default LearnPQC;
