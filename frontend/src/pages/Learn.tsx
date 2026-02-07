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
      
      <div className="flex pt-32 pb-20 px-6 gap-8 items-stretch">
        {/* Left Ad */}
        <div className="w-[10%] min-w-[80px] bg-gray-200 p-2 flex-shrink-0 rounded-lg shadow-md self-stretch flex flex-col justify-start">
          <h3 className="text-sm font-bold">Advertisement</h3>
          <p className="text-xs">Your ad content here.</p>
        </div>

        {/* Main Content */}
        <div className="flex-1 max-w-4xl mx-auto flex flex-col">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Welcome to <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">QuantCAI</span>
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed">
              Explore the Frontiers of Computing
            </p>
          </div>

          <Card className="bg-gradient-to-br from-slate-800/80 to-purple-800/80 border-blue-500/30 backdrop-blur-sm mb-8">
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
                <h2 className="text-3xl font-bold text-white">What is Quantum Computing?</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed">
                    Quantum computing is not just an evolution; it's a revolution. While classical computers use bits that 
                    represent either 0 or 1, quantum computers leverage qubits. These qubits can exist in multiple states 
                    simultaneously, unlocking unparalleled computing power. Quantum computing holds the potential to solve 
                    complex problems exponentially faster than classical computers, revolutionizing industries from healthcare 
                    to finance and beyond.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Atom className="h-8 w-8 text-purple-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">What are Qubits?</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed">
                    Qubits are the fundamental units of quantum information. Unlike classical bits that represent either a 0 or a 1, 
                    qubits can exist in a state known as superposition, representing both 0 and 1 simultaneously. Additionally, 
                    qubits can be entangled, meaning the state of one qubit can instantly affect the state of another, even if 
                    they are physically separated.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Zap className="h-8 w-8 text-green-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Potential Applications</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed">
                    Quantum computers have the potential to revolutionize various fields such as cryptography, optimization problems, 
                    drug discovery, material science, and artificial intelligence. They could solve problems that are currently 
                    intractable for classical computers due to their ability to process vast amounts of data and perform complex 
                    calculations rapidly.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Globe className="h-8 w-8 text-blue-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Current Availability</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed">
                    Quantum computers are still in the early stages of development and are primarily in the hands of research 
                    institutions and tech companies. However, as the technology progresses, efforts are being made to make quantum 
                    computing more accessible through cloud-based platforms that allow users to run algorithms on quantum hardware remotely.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <Shield className="h-8 w-8 text-red-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Development Challenges</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed">
                    Developing practical quantum computers faces several challenges, including maintaining the stability of qubits 
                    (decoherence), error correction, scaling up the number of qubits while retaining their quantum properties, 
                    and creating a robust infrastructure for large-scale quantum computing.
                  </p>
                </CardContent>
              </Card>
            </section>

            <section>
              <div className="flex items-center mb-6">
                <BookOpen className="h-8 w-8 text-yellow-400 mr-4" />
                <h2 className="text-3xl font-bold text-white">Quantum vs Classical Computing</h2>
              </div>
              <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
                <CardContent className="p-6">
                  <p className="text-gray-300 leading-relaxed">
                    Classical computers process information using bits that are in a definite state of 0 or 1. Quantum computers 
                    leverage qubits that can exist in multiple states simultaneously due to superposition and entanglement, enabling 
                    them to perform certain calculations much faster than classical computers.
                  </p>
                </CardContent>
              </Card>
            </section>
          </div>
        </div>

        {/* Right Ad */}
        <div className="w-[10%] min-w-[80px] bg-gray-200 p-2 flex-shrink-0 rounded-lg shadow-md self-stretch flex flex-col justify-start">
          <h3 className="text-sm font-bold">Advertisement</h3>
          <p className="text-xs">Your ad content here.</p>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default Learn;
