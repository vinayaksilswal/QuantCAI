import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  BookOpen, Atom, Zap, Shield, Globe, Cpu, CheckCircle2, 
  AlertTriangle, ArrowRight
} from 'lucide-react';
import { usePageTracking } from '@/hooks/usePageTracking';
import { SEO } from '@/components/SEO';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';

const Learn = () => {
  usePageTracking('learn');
  const navigate = useNavigate();

  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizCorrect, setQuizCorrect] = useState<boolean | null>(null);

  const quiz = {
    question: "What is the fundamental unit of quantum information that can exist in a superposition of states?",
    options: ["Classical Bit", "Qubit", "Quantum Byte", "Trit"],
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



  return (
    <div className="min-h-screen relative overflow-hidden font-sans bg-transparent text-slate-100 selection:bg-purple-500/30">
      <SEO 
        title="Learn Quantum Computing - QuantCAI Tutorials" 
        description="Master quantum mechanics, quantum circuits, and post-quantum cryptography with our interactive learning platform." 
        keywords="quantum computing, learn quantum, quantum tutorials, quantum circuits, post-quantum cryptography"
      />
      <Navbar />
      
      <div className="flex pt-32 pb-20 px-6 gap-8 items-stretch max-w-7xl mx-auto">

        {/* Main Content */}
        <div className="flex-1 max-w-4xl mx-auto flex flex-col">
          <div className="text-center mb-12">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Welcome to <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">QuantCAI</span>
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed">
              Explore the Frontiers of Computing
            </p>
          </div>

          <Card className="bg-gradient-to-br from-slate-800/80 to-purple-800/80 border-blue-500/30 backdrop-blur-sm mb-12">
            <CardContent className="p-8">
              <p className="text-lg text-gray-300 leading-relaxed">
                Unlock the mysteries of the future with QuantCAI, your portal to the fascinating world of quantum computing. 
                Enter a realm where bits transcend the boundaries of traditional computing and leap into the quantum age.
              </p>
            </CardContent>
          </Card>



          <div className="space-y-12">
            <section>
              <div className="flex items-center mb-6">
                <Cpu className="h-8 w-8 text-blue-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Start Your Quantum Journey with our Interactive Simulator</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    Quantum computing sounds like science fiction, but learning how it works shouldn't require a PhD in physics. If you're a student, hobbyist, or developer curious about the quantum revolution, the biggest hurdle is usually complex math and intimidating code. That's why we built a visual, interactive playground. You don't need to write a single line of code to experience the magic of quantum mechanics—you just need curiosity and a web browser.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Atom className="h-8 w-8 text-purple-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">1. Visual Drag-and-Drop Learning</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    Forget staring at lines of confusing syntax. Our platform uses an intuitive drag-and-drop interface that makes building a quantum circuit as easy as playing with digital building blocks. Simply grab a "gate" (like the Hadamard gate) and drop it onto a qubit wire. Instantly watch how the quantum state changes in real-time, helping you visually grasp abstract concepts.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Zap className="h-8 w-8 text-green-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">2. Experience Real-Time Superposition and Entanglement</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    What exactly is superposition? Instead of reading a textbook definition, see it happen live. As you interact with our simulator, you'll see visualizations of quantum states collapsing and changing. Experiment with entangling two qubits together, so that a change in one instantly affects the other. It's hands-on, visual learning that makes the impossible feel tangible.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Globe className="h-8 w-8 text-blue-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">3. Pre-Built Templates to Get You Started</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed mb-4">
                    Staring at a blank screen can be overwhelming. We've included a library of beginner-friendly templates ranging from coin-flip probability generators to basic teleportation algorithms. Load a template with one click, run the simulation, and tinker with the gates to see what happens. Learning by doing is the fastest way to become a quantum visionary!
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <Card className="bg-gradient-to-r from-blue-900/40 to-purple-900/40 border-blue-500/50 backdrop-blur-sm">
                <CardContent className="p-8 text-center">
                  <h3 className="text-2xl font-bold text-white mb-4">Ready to leap into the quantum world?</h3>
                  <p className="text-slate-300 mb-6">
                    Discover how easy it is to build your very first quantum algorithm. Create your Free QuantCAI Account today and start experimenting with our interactive simulator!
                  </p>
                  <Button onClick={() => navigate('/signup')} className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-8 rounded-xl shadow-lg shadow-blue-500/20">
                    Create your Free QuantCAI Account <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </CardContent>
              </Card>
            </section>
          </div>

          {/* Quiz Section to Mark Completion */}
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
                        {opt
                      }</button>
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
                        <div className="flex gap-3">
                          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                          <div>
                            <p className="font-bold">Correct!</p>
                            <p className="mt-0.5">You have mastered the basics of Quantum Computing.</p>
                          </div>
                        </div>
                        <Button 
                          onClick={() => navigate('/quantum-computing')}
                          className="bg-emerald-600 hover:bg-emerald-500 text-white gap-2 animate-bounce"
                        >
                          Next: Quantum Basics <ArrowRight className="w-4 h-4" />
                        </Button>
                      </div>
                    ) : (
                      <>
                        <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
                        <div>
                          <p className="font-bold">Incorrect</p>
                          <p className="mt-0.5">Review the sections above to try again. (Refresh to retry)</p>
                        </div>
                      </>
                    )}
                  </div>
                ) : (
                  <Button
                    onClick={handleSubmitQuiz}
                    disabled={selectedOption === null}
                    className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-xl font-bold shadow-lg shadow-blue-500/10"
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
