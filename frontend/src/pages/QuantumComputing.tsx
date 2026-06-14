import { usePageTracking } from '@/hooks/usePageTracking';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Atom, Calculator, Code, Zap } from 'lucide-react';

declare global {
  interface Window {
    MathJax: any;
  }
}

const QuantumComputing = () => {
  usePageTracking('quantum-computing');
  const navigate = useNavigate();

  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizCorrect, setQuizCorrect] = useState<boolean | null>(null);

  const quiz = {
    question: "What defines a valid quantum state vector?",
    options: [
      "The entries are real numbers that sum to 1.",
      "The entries are complex numbers where the sum of their absolute values squared is 1.",
      "The vector can be any set of complex numbers.",
      "The matrix is unitary."
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

  useEffect(() => {
    // Load MathJax
    const mathJaxScript = document.createElement('script');
    mathJaxScript.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
    mathJaxScript.id = 'MathJax-script';
    mathJaxScript.async = true;
    document.head.appendChild(mathJaxScript);

    // Configure MathJax
    window.MathJax = {
      tex: {
        inlineMath: [['\\(', '\\)']],
        displayMath: [['\\[', '\\]']],
      },
      options: {
        ignoreHtmlClass: 'tex2jax_ignore',
        processHtmlClass: 'tex2jax_process',
      },
    };

    return () => {
      if (mathJaxScript.parentNode) {
        document.head.removeChild(mathJaxScript);
      }
    };
  }, []);

  return (
    <div className="min-h-screen relative">
      <Navbar />
      
      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Understanding of <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Single Qubit</span>
            </h1>
          </div>

          <div className="space-y-12">
            <section>
              <div className="flex items-center mb-6">
                <Atom className="h-8 w-8 text-blue-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Quantum Information</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    Quantum information refers to the field that explores how information can be stored and manipulated using 
                    the principles of quantum mechanics. In classical computing, information is processed in bits, which can 
                    represent either a 0 or a 1. However, in quantum computing, quantum bits or qubits can exist in a superposition 
                    of both 0 and 1 states simultaneously, allowing for parallel computation and potentially solving certain problems 
                    much faster than classical computers.
                  </p>
                  <p className="text-gray-300 leading-relaxed">
                    Quantum information also deals with concepts like entanglement, where the state of one qubit becomes dependent 
                    on the state of another, regardless of the distance between them. This property can be utilized for secure 
                    communication and cryptography, where any eavesdropping would disturb the entangled particles, alerting the 
                    communicating parties.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Calculator className="h-8 w-8 text-purple-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Quantum State Vectors</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    The quantum state of a system is represented by a column vector, similar to probabilistic states. 
                    Vectors representing quantum states are characterized by two properties:
                  </p>
                  <ol className="list-decimal list-inside text-gray-300 mb-6 space-y-2">
                    <li>The entries of a quantum state vector are complex numbers.</li>
                    <li>The sum of the absolute values squared of the entries of the vector is 1.</li>
                  </ol>
                  <p className="text-gray-300 mb-4">
                    The Euclidean norm of a column vector is denoted and defined as follows:
                  </p>
                  <div className="bg-slate-900/50 p-4 rounded-lg mb-4 text-center">
                    <span className="text-blue-400 font-mono text-lg">
                      ||v|| = √(Σ|αₖ|²)
                    </span>
                  </div>
                  <p className="text-gray-300 leading-relaxed">
                    Quantum state vectors are unit vectors concerning the Euclidean norm.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Zap className="h-8 w-8 text-green-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Measuring Quantum States</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    Measuring quantum states is a fundamental aspect of quantum mechanics. A measurement collapses the quantum 
                    state of a system into one of its possible outcomes. For instance, measuring the spin of a particle along 
                    a certain axis might yield "up" or "down." Before measurement, the particle's spin might exist in a superposition 
                    of both states, but upon measurement, it collapses to one state.
                  </p>
                  <p className="text-gray-300 leading-relaxed">
                    The act of measurement is inherently probabilistic, and measuring entangled particles can instantly determine 
                    the state of another, regardless of distance.
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
                          <svg className="w-5 h-5 text-emerald-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <div>
                            <p className="font-bold">Correct!</p>
                            <p className="mt-0.5">Excellent understanding of Quantum States.</p>
                          </div>
                        </div>
                        <button 
                          onClick={() => navigate('/learn/qubits')}
                          className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 transition-colors"
                        >
                          Next: Advanced Qubits (Pro) <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                        </button>
                      </div>
                    ) : (
                      <div className="flex gap-3">
                        <svg className="w-5 h-5 text-rose-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <div>
                          <p className="font-bold">Incorrect</p>
                          <p className="mt-0.5">Review the Quantum State Vectors section to try again.</p>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <button
                    onClick={handleSubmitQuiz}
                    disabled={selectedOption === null}
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-xl font-bold shadow-lg shadow-blue-500/10 disabled:opacity-50"
                  >
                    Submit Answer
                  </button>
                )}
              </div>
            </Card>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default QuantumComputing;
