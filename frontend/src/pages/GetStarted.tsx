
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Rocket, BookOpen, Users, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';

const GetStarted = () => {
  return (
    <div className="min-h-screen relative">
      <Navbar />
      
      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Get <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Started</span>
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed">
              Begin your quantum computing journey with QuantCAI
            </p>
          </div>

          <Card className="bg-gradient-to-br from-slate-800/80 to-purple-800/80 border-blue-500/30 backdrop-blur-sm mb-12">
            <CardContent className="p-8 text-center">
              <Rocket className="h-16 w-16 text-blue-400 mx-auto mb-6" />
              <h2 className="text-3xl font-bold text-white mb-4">Ready to Accelerate Your Quantum Journey?</h2>
              <p className="text-lg text-gray-300 leading-relaxed mb-8">
                Join QuantCAI to explore quantum computing, pioneer advanced research, and secure your enterprise infrastructure. Unlock the power of quantum 
                mechanics and prepare for the impending shift to Post-Quantum Cryptography (PQC).
              </p>
              <div className="grid md:grid-cols-3 gap-6 mb-8">
                <div className="text-center">
                  <BookOpen className="h-12 w-12 text-green-400 mx-auto mb-3" />
                  <h3 className="text-lg font-semibold text-white mb-2">Learn</h3>
                  <p className="text-gray-400 text-sm">Comprehensive educational resources</p>
                </div>
                <div className="text-center">
                  <Zap className="h-12 w-12 text-yellow-400 mx-auto mb-3" />
                  <h3 className="text-lg font-semibold text-white mb-2">Simulate</h3>
                  <p className="text-gray-400 text-sm">Advanced research environments</p>
                </div>
                <div className="text-center">
                  <Users className="h-12 w-12 text-purple-400 mx-auto mb-3" />
                  <h3 className="text-lg font-semibold text-white mb-2">Connect</h3>
                  <p className="text-gray-400 text-sm">Join our quantum community</p>
                </div>
              </div>
              <div className="space-y-4">
                <p className="text-gray-300 text-lg font-medium">More details coming soon!</p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Link to="/learn">
                    <Button className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white px-8 py-3">
                      Start Learning
                    </Button>
                  </Link>
                  <Link to="/soon">
                    <Button variant="outline" className="border-2 border-blue-400 text-blue-400 hover:bg-blue-400 hover:text-white px-8 py-3">
                      Contact Us
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid md:grid-cols-2 gap-8">
            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold text-blue-400 mb-4">What You'll Learn</h3>
                <ul className="space-y-3 text-gray-300">
                  <li className="flex items-start">
                    <span className="text-blue-400 mr-2">•</span>
                    Fundamental principles of quantum mechanics
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-400 mr-2">•</span>
                    Quantum states, qubits, and advanced circuit design
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-400 mr-2">•</span>
                    Post-Quantum Cryptography (PQC) integration
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-400 mr-2">•</span>
                    Real-world enterprise quantum algorithms
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-400 mr-2">•</span>
                    Cryptographic risk assessment strategies
                  </li>
                </ul>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-6">
                <h3 className="text-xl font-bold text-purple-400 mb-4">Why Choose QuantCAI?</h3>
                <ul className="space-y-3 text-gray-300">
                  <li className="flex items-start">
                    <span className="text-purple-400 mr-2">•</span>
                    Enterprise-grade educational cohorts
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-400 mr-2">•</span>
                    High-fidelity quantum simulators
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-400 mr-2">•</span>
                    CBOM & PQC compliance auditing
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-400 mr-2">•</span>
                    Dedicated engineering consulting
                  </li>
                  <li className="flex items-start">
                    <span className="text-purple-400 mr-2">•</span>
                    Future-ready quantum resilience
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default GetStarted;
