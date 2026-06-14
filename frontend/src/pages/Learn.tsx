import { useState, useEffect } from 'react';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { usePageTracking } from '@/hooks/usePageTracking';
import { useAI } from '@/hooks/useAI';
import { BookOpen, Atom, Award, CheckCircle2, AlertTriangle, ArrowRight, BookOpenCheck, ShieldCheck } from 'lucide-react';

const CURRICULUM_MODULES = [
  {
    id: "mod-qubits",
    title: "Module 1: Introduction to Qubits",
    chapters: [
      { 
        id: "ch-superposition", 
        title: "Superposition & Classical Bits",
        content: "Classical computers process information using bits that are in a definite state of 0 or 1. Quantum computers leverage qubits that can exist in multiple states simultaneously due to superposition and entanglement, enabling them to perform certain calculations much faster than classical computers. A qubit's state is generally written as |ψ⟩ = α|0⟩ + β|1⟩, where α and β are complex numbers representing probability amplitudes, satisfying |α|² + |β|² = 1."
      },
      { 
        id: "ch-bloch", 
        title: "Bloch Sphere Representation",
        content: "The Bloch sphere is a geometrical representation of the pure state space of a two-level quantum mechanical system (qubit). Any pure qubit state can be written as |ψ⟩ = cos(θ/2)|0⟩ + e^(iφ)sin(θ/2)|1⟩, mapping to a point on the surface of a unit sphere. The north pole represents |0⟩, the south pole represents |1⟩, and points on the equator represent equal superpositions (like |+⟩ and |−⟩)."
      },
      { 
        id: "ch-dirac", 
        title: "Dirac Ket/Bra Notation",
        content: "Dirac notation (bra-ket notation) is the standard notation for describing quantum states in quantum mechanics. A column vector representing a quantum state is called a ket, written as |ψ⟩. A row vector (the conjugate transpose of a ket) is called a bra, written as ⟨ψ|. The inner product (dot product) of two states is ⟨φ|ψ⟩, and the outer product is |ψ⟩⟨φ|."
      }
    ],
    quizzes: [
      {
        question: "What quantum phenomenon allows a qubit to be in a linear combination of |0⟩ and |1⟩ states simultaneously?",
        options: [
          "Quantum Decoherence",
          "Quantum Superposition",
          "Quantum Entanglement",
          "Classical Teleportation"
        ],
        correctIndex: 1
      }
    ]
  },
  {
    id: "mod-gates",
    title: "Module 2: Quantum Gates & Circuits",
    chapters: [
      { 
        id: "ch-hadamard", 
        title: "Hadamard (H) Gate",
        content: "The Hadamard gate acts on a single qubit, mapping the basis states |0⟩ to ( |0⟩ + |1⟩ ) / √2 and |1⟩ to ( |0⟩ - |1⟩ ) / √2. This creates an equal superposition of the two computational basis states, making it the fundamental starting gate for almost all quantum algorithms."
      },
      { 
        id: "ch-cnot", 
        title: "CNOT (Controlled-NOT) Gate",
        content: "The Controlled-NOT (CNOT or CX) gate is a 2-qubit gate that performs the NOT operation on the second qubit (target) only if the first qubit (control) is in the state |1⟩. It is represented by a 4x4 matrix and is crucial for creating quantum entanglement."
      },
      { 
        id: "ch-entanglement", 
        title: "Quantum Entanglement & Bell States",
        content: "Quantum entanglement is a physical phenomenon that occurs when a pair or group of particles are generated, interact, or share spatial proximity in a way such that the quantum state of each particle cannot be described independently of the state of the others. By applying a Hadamard gate to qubit 0, followed by a CNOT gate with qubit 0 as control and qubit 1 as target, we create the Bell state (|00⟩ + |11⟩)/√2."
      }
    ],
    quizzes: [
      {
        question: "Which quantum gate is primarily used to put a qubit into a state of equal superposition?",
        options: [
          "X (Pauli-X) Gate",
          "H (Hadamard) Gate",
          "Z (Pauli-Z) Gate",
          "CNOT Gate"
        ],
        correctIndex: 1
      }
    ]
  },
  {
    id: "mod-pqc",
    title: "Module 3: Post-Quantum Cryptography",
    chapters: [
      { 
        id: "ch-shor", 
        title: "Shor's Algorithm & Threat Vector",
        content: "Shor's algorithm is a polynomial-time quantum algorithm for integer factorization. Since public-key cryptography schemes (like RSA and ECC) rely on the difficulty of integer factorization or discrete logarithms, Shor's algorithm running on a sufficiently large Cryptographically Relevant Quantum Computer (CRQC) will break all classical secure communications."
      },
      { 
        id: "ch-nist", 
        title: "NIST PQC Standardization",
        content: "Recognizing the quantum threat, the National Institute of Standards and Technology (NIST) initiated a process in 2016 to solicit, evaluate, and standardize quantum-resistant public-key cryptographic algorithms. The goal is to identify algorithms that remain secure against both classical and quantum computers."
      },
      { 
        id: "ch-standards", 
        title: "FIPS 203 (ML-KEM) & FIPS 204 (ML-DSA)",
        content: "In August 2024, NIST released its first finalized post-quantum standards. FIPS 203 defines ML-KEM (Module-Lattice-Based Key-Encapsulation Mechanism), designed for secure key exchange. FIPS 204 defines ML-DSA (Module-Lattice-Based Digital Signature Algorithm), designed for authentication and digital signatures. Organizations are mandated to transition to these standards before 2030."
      }
    ],
    quizzes: [
      {
        question: "Which cryptographic standard specifies ML-KEM for quantum-safe key exchange?",
        options: [
          "FIPS 197",
          "FIPS 203",
          "FIPS 204",
          "FIPS 140-3"
        ],
        correctIndex: 1
      }
    ]
  }
];

const Learn = () => {
  usePageTracking('learn');
  const { updateClientContext } = useAI();

  const [activeModuleIndex, setActiveModuleIndex] = useState(0);
  const [activeChapterIndex, setActiveChapterIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizCorrect, setQuizCorrect] = useState<boolean | null>(null);

  // Sync to AI Context whenever state changes
  useEffect(() => {
    const activeModule = CURRICULUM_MODULES[activeModuleIndex];
    const activeChapter = activeModule.chapters[activeChapterIndex];
    const quiz = activeModule.quizzes[0];
    
    updateClientContext('learn', {
      module_id: activeModule.id,
      chapter_title: activeChapter.title,
      quiz_state: {
        question: quiz.question,
        options: quiz.options,
        user_selected_option: selectedOption !== null ? quiz.options[selectedOption] : null,
        is_submitted: quizSubmitted,
        is_correct: quizCorrect
      }
    });
  }, [activeModuleIndex, activeChapterIndex, selectedOption, quizSubmitted, quizCorrect, updateClientContext]);

  const activeModule = CURRICULUM_MODULES[activeModuleIndex];
  const activeChapter = activeModule.chapters[activeChapterIndex];
  const activeQuiz = activeModule.quizzes[0];

  const handleSelectOption = (index: number) => {
    if (quizSubmitted) return;
    setSelectedOption(index);
  };

  const handleSubmitQuiz = () => {
    if (selectedOption === null || quizSubmitted) return;
    const correct = selectedOption === activeQuiz.correctIndex;
    setQuizCorrect(correct);
    setQuizSubmitted(true);
  };

  const handleNextChapter = () => {
    if (activeChapterIndex < activeModule.chapters.length - 1) {
      setActiveChapterIndex(activeChapterIndex + 1);
    } else if (activeModuleIndex < CURRICULUM_MODULES.length - 1) {
      setActiveModuleIndex(activeModuleIndex + 1);
      setActiveChapterIndex(0);
      setSelectedOption(null);
      setQuizSubmitted(false);
      setQuizCorrect(null);
    }
  };

  const selectChapter = (modIdx: number, chapIdx: number) => {
    setActiveModuleIndex(modIdx);
    setActiveChapterIndex(chapIdx);
    setSelectedOption(null);
    setQuizSubmitted(false);
    setQuizCorrect(null);
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-slate-950 text-slate-100">
      {/* Background radial highlight */}
      <div className="absolute top-20 left-10 w-[600px] h-[600px] bg-blue-500/[0.03] rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-20 right-10 w-[500px] h-[500px] bg-purple-500/[0.03] rounded-full blur-[120px] pointer-events-none" />

      <Navbar />

      <div className="pt-24 pb-20 px-6 max-w-7xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-3 bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
            Quantum Learning Hub
          </h1>
          <p className="text-sm font-mono text-cyan-400 uppercase tracking-widest">
            Socratic Curriculum & Concept Checks
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Curriculum Map & Chapter Content (8 Cols) */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Split Panel: Sidebar & Active Chapter */}
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
              
              {/* Module List Sidebar (4 Cols) */}
              <div className="md:col-span-4 space-y-4">
                <h3 className="font-mono text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Curriculum Map</h3>
                <div className="space-y-3">
                  {CURRICULUM_MODULES.map((mod, modIdx) => (
                    <div key={mod.id} className="space-y-1.5">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-slate-400 px-1 font-mono">
                        <BookOpen className="w-3 h-3 text-indigo-400" />
                        <span>{mod.title.split(":")[0]}</span>
                      </div>
                      <div className="space-y-1">
                        {mod.chapters.map((chap, chapIdx) => {
                          const isCurrent = activeModuleIndex === modIdx && activeChapterIndex === chapIdx;
                          return (
                            <button
                              key={chap.id}
                              onClick={() => selectChapter(modIdx, chapIdx)}
                              className={`w-full text-left text-xs px-3 py-2 rounded-xl transition-all border ${
                                isCurrent 
                                  ? "bg-indigo-600/20 border-indigo-500/50 text-white font-medium shadow-[0_0_15px_rgba(99,102,241,0.15)]" 
                                  : "bg-slate-900/40 border-slate-800/80 text-slate-400 hover:bg-slate-900/70 hover:border-slate-700 hover:text-white"
                              }`}
                            >
                              {chap.title}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Active Chapter Reader (8 Cols) */}
              <div className="md:col-span-8">
                <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-md shadow-2xl h-full flex flex-col justify-between rounded-2xl">
                  <CardHeader className="py-4 px-6 border-b border-white/5 bg-white/5">
                    <div className="flex items-center gap-2">
                      <Atom className="w-5 h-5 text-cyan-400 animate-spin-slow" />
                      <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider">
                        Active Chapter
                      </span>
                    </div>
                    <CardTitle className="text-lg font-bold text-white mt-1">
                      {activeChapter.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6 flex-1 flex flex-col justify-between gap-6">
                    <p className="text-slate-300 leading-relaxed text-sm font-light">
                      {activeChapter.content}
                    </p>
                    <div className="flex justify-end pt-4 border-t border-white/5">
                      <Button
                        onClick={handleNextChapter}
                        variant="outline"
                        className="border-slate-800 bg-slate-900/50 hover:bg-slate-800 hover:text-white text-slate-300 gap-2 text-xs"
                      >
                        Next Chapter <ArrowRight className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>

            </div>

          </div>

          {/* Right Column: Quiz Component (4 Cols) */}
          <div className="lg:col-span-4 space-y-6">
            <h3 className="font-mono text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">Concept Validation</h3>
            
            <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-md shadow-2xl overflow-hidden rounded-2xl flex flex-col">
              <div className="p-5 border-b border-white/5 bg-gradient-to-r from-blue-500/10 to-indigo-500/10 flex items-center gap-2.5">
                <Award className="w-5 h-5 text-yellow-400" />
                <div>
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">Module Quiz Check</h4>
                  <p className="text-[10px] text-slate-400 font-mono mt-0.5">Test your concept retention</p>
                </div>
              </div>

              <div className="p-6 space-y-5">
                <p className="text-sm font-semibold text-slate-200 leading-snug">
                  {activeQuiz.question}
                </p>

                <div className="space-y-2">
                  {activeQuiz.options.map((opt, oIdx) => {
                    const isSelected = selectedOption === oIdx;
                    return (
                      <button
                        key={oIdx}
                        onClick={() => handleSelectOption(oIdx)}
                        disabled={quizSubmitted}
                        className={`w-full text-left text-xs p-3.5 rounded-xl border transition-all ${
                          isSelected 
                            ? "bg-blue-600/20 border-blue-500 text-white font-medium" 
                            : "bg-slate-950/50 border-slate-850 text-slate-400 hover:bg-slate-900/60 hover:text-white hover:border-slate-800"
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
                      <>
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                        <div>
                          <p className="font-bold">Correct Answer!</p>
                          <p className="mt-0.5">Superb. You have successfully mapped the concepts of superposition. You can now consult the Copilot for deep math derivations.</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                        <div>
                          <p className="font-bold">Incorrect Selection</p>
                          <p className="mt-0.5">That is not correct. Review the chapter content on superposition or ask the AI Tutor: &quot;Explain this superposition quiz question.&quot;</p>
                        </div>
                      </>
                    )}
                  </div>
                ) : (
                  <Button
                    onClick={handleSubmitQuiz}
                    disabled={selectedOption === null}
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-xl font-bold shadow-lg shadow-blue-500/10 cursor-pointer disabled:opacity-40 disabled:pointer-events-none"
                  >
                    Submit Answer
                  </Button>
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

export default Learn;
