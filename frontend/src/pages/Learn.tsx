import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { BookOpen, Atom, Zap, Shield, Globe, Cpu } from 'lucide-react';
import { usePageTracking } from '@/hooks/usePageTracking';

const Learn = () => {
  usePageTracking('learn');

  return (
    <div className="min-h-screen relative">
      <Navbar />

      <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Welcome to <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent italic">QuantCAI</span>
          </h1>
          <p className="text-xl text-gray-400 font-light tracking-wide leading-relaxed">
            Explore the Frontiers of Computing
          </p>
        </div>

        <Card className="bg-slate-900/60 border-slate-800 backdrop-blur-md mb-12 shadow-xl">
          <CardContent className="p-8">
            <p className="text-lg text-slate-300 leading-relaxed font-light">
              Unlock the mysteries of the future with QuantCAI, your portal to the fascinating world of quantum computing.
              Enter a realm where bits transcend the boundaries of traditional computing and leap into the quantum age.
            </p>
          </CardContent>
        </Card>

        <div className="space-y-16">
          <section className="animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="flex items-center mb-6">
              <div className="p-2 rounded-lg bg-blue-500/10 mr-4">
                <Cpu className="h-8 w-8 text-blue-400" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">What is Quantum Computing?</h2>
            </div>
            <Card className="bg-slate-900/40 border-slate-800 hover:border-blue-500/30 transition-colors backdrop-blur-sm shadow-xl">
              <CardContent className="p-8">
                <p className="text-slate-300 leading-relaxed text-lg">
                  Quantum computing is not just an evolution; it's a revolution. While classical computers use bits that
                  represent either 0 or 1, quantum computers leverage qubits. These qubits can exist in multiple states
                  simultaneously, unlocking unparalleled computing power. Quantum computing holds the potential to solve
                  complex problems exponentially faster than classical computers, revolutionizing industries from healthcare
                  to finance and beyond.
                </p>
              </CardContent>
            </Card>
          </section>

          <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            <div className="flex items-center mb-6">
              <div className="p-2 rounded-lg bg-purple-500/10 mr-4">
                <Atom className="h-8 w-8 text-purple-400" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">What are Qubits?</h2>
            </div>
            <Card className="bg-slate-900/40 border-slate-800 hover:border-purple-500/30 transition-colors backdrop-blur-sm shadow-xl">
              <CardContent className="p-8">
                <p className="text-slate-300 leading-relaxed text-lg">
                  Qubits are the fundamental units of quantum information. Unlike classical bits that represent either a 0 or a 1,
                  qubits can exist in a state known as superposition, representing both 0 and 1 simultaneously. Additionally,
                  qubits can be entangled, meaning the state of one qubit can instantly affect the state of another, even if
                  they are physically separated.
                </p>
              </CardContent>
            </Card>
          </section>

          <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
            <div className="flex items-center mb-6">
              <div className="p-2 rounded-lg bg-green-500/10 mr-4">
                <Zap className="h-8 w-8 text-green-400" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">Potential Applications</h2>
            </div>
            <Card className="bg-slate-900/40 border-slate-800 hover:border-green-500/30 transition-colors backdrop-blur-sm shadow-xl">
              <CardContent className="p-8">
                <p className="text-slate-300 leading-relaxed text-lg">
                  Quantum computers have the potential to revolutionize various fields such as cryptography, optimization problems,
                  drug discovery, material science, and artificial intelligence. They could solve problems that are currently
                  intractable for classical computers due to their ability to process vast amounts of data and perform complex
                  calculations rapidly.
                </p>
              </CardContent>
            </Card>
          </section>

          <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300">
            <div className="flex items-center mb-6">
              <div className="p-2 rounded-lg bg-blue-500/10 mr-4">
                <Globe className="h-8 w-8 text-blue-400" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">Current Availability</h2>
            </div>
            <Card className="bg-slate-900/40 border-slate-800 hover:border-blue-500/30 transition-colors backdrop-blur-sm shadow-xl">
              <CardContent className="p-8">
                <p className="text-slate-300 leading-relaxed text-lg">
                  Quantum computers are still in the early stages of development and are primarily in the hands of research
                  institutions and tech companies. However, as the technology progresses, efforts are being made to make quantum
                  computing more accessible through cloud-based platforms that allow users to run algorithms on quantum hardware remotely.
                </p>
              </CardContent>
            </Card>
          </section>

          <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-400">
            <div className="flex items-center mb-6">
              <div className="p-2 rounded-lg bg-red-500/10 mr-4">
                <Shield className="h-8 w-8 text-red-400" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">Development Challenges</h2>
            </div>
            <Card className="bg-slate-900/40 border-slate-800 hover:border-red-500/30 transition-colors backdrop-blur-sm shadow-xl">
              <CardContent className="p-8">
                <p className="text-slate-300 leading-relaxed text-lg">
                  Developing practical quantum computers faces several challenges, including maintaining the stability of qubits
                  (decoherence), error correction, scaling up the number of qubits while retaining their quantum properties,
                  and creating a robust infrastructure for large-scale quantum computing.
                </p>
              </CardContent>
            </Card>
          </section>

          <section className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-500">
            <div className="flex items-center mb-6">
              <div className="p-2 rounded-lg bg-yellow-500/10 mr-4">
                <BookOpen className="h-8 w-8 text-yellow-500" />
              </div>
              <h2 className="text-3xl font-bold text-white tracking-tight">Quantum vs Classical Computing</h2>
            </div>
            <Card className="bg-slate-900/40 border-slate-800 hover:border-yellow-500/30 transition-colors backdrop-blur-sm shadow-xl">
              <CardContent className="p-8">
                <p className="text-slate-300 leading-relaxed text-lg">
                  Classical computers process information using bits that are in a definite state of 0 or 1. Quantum computers
                  leverage qubits that can exist in multiple states simultaneously due to superposition and entanglement, enabling
                  them to perform certain calculations much faster than classical computers.
                </p>
              </CardContent>
            </Card>
          </section>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default Learn;
