import { usePageTracking } from '@/hooks/usePageTracking';

import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from "@/components/ui/card";
import { Target, Users, Lightbulb, Shield } from 'lucide-react';

const Vision = () => {
  usePageTracking('vision');
  return (
    <div className="min-h-screen relative">
      <Navbar />
      
      <div className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Our <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Mission</span>
            </h1>
            <p className="text-xl text-gray-300 leading-relaxed">
              Shaping Tomorrow's Quantum Future Today
            </p>
          </div>

          <div className="space-y-12">
            <Card className="bg-gradient-to-br from-slate-800/80 to-purple-800/80 border-blue-500/30 backdrop-blur-sm">
              <CardContent className="p-8">
                <div className="flex items-center mb-6">
                  <Target className="h-8 w-8 text-blue-400 mr-4" />
                  <h2 className="text-3xl font-bold text-white">Our Core Mission</h2>
                </div>
                <p className="text-lg text-gray-300 leading-relaxed">
                  QuantCAI's mission is to democratize quantum computing education and safeguard global digital infrastructure. We provide an all-encompassing platform designed for learners and researchers to explore quantum mechanics and algorithms, while simultaneously delivering state-of-the-art Post-Quantum Cryptography (PQC) solutions to secure enterprise data against tomorrow's quantum threats. You can trust us as your professional partner in navigating the quantum era.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-8">
                <div className="flex items-center mb-6">
                  <Users className="h-8 w-8 text-purple-400 mr-4" />
                  <h2 className="text-3xl font-bold text-white">Our Expert Team</h2>
                </div>
                <p className="text-lg text-gray-300 leading-relaxed">
                  Our team at QuantCAI is comprised of seasoned professionals with deep expertise spanning quantum physics, software engineering, and cryptographic security. We are dedicated to staying at the cutting edge of this rapidly evolving field to provide our clients—from academic researchers to enterprise leaders—with unparalleled guidance. At QuantCAI, we believe that strong, forward-thinking leadership is the key to successfully adopting quantum technologies and PQC integration. Let us help you bring your quantum computing goals to life.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">
              <CardContent className="p-8">
                <div className="flex items-center mb-6">
                  <Lightbulb className="h-8 w-8 text-yellow-400 mr-4" />
                  <h2 className="text-3xl font-bold text-white">Our Foundation & Vision</h2>
                </div>
                <p className="text-lg text-gray-300 leading-relaxed">
                  QuantCAI was founded with a profound understanding of the intricacies of quantum physics and the transformative potential of quantum computing. We are at the forefront of this technological shift, recognizing that quantum computing will revolutionize industries ranging from healthcare to finance. At QuantCAI, we provide a continuous pipeline of value: comprehensive training and simulation tools for learners and researchers, alongside advanced PQC implementation and algorithm development services for enterprises. Let us help you unlock the power of quantum computing and secure your business for the future.
                </p>
              </CardContent>
            </Card>

            <div className="grid md:grid-cols-2 gap-8">
              <Card className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 border-blue-500/30 backdrop-blur-sm">
                <CardContent className="p-6">
                  <h3 className="text-xl font-bold text-blue-400 mb-4">What We Believe</h3>
                  <ul className="space-y-3 text-gray-300">
                    <li className="flex items-start">
                      <span className="text-blue-400 mr-2">•</span>
                      Quantum computing will transform technology
                    </li>
                    <li className="flex items-start">
                      <span className="text-blue-400 mr-2">•</span>
                      Education should be accessible to all
                    </li>
                    <li className="flex items-start">
                      <span className="text-blue-400 mr-2">•</span>
                      Innovation drives progress
                    </li>
                    <li className="flex items-start">
                      <span className="text-blue-400 mr-2">•</span>
                      Collaboration accelerates discovery
                    </li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-purple-900/30 to-blue-900/30 border-purple-500/30 backdrop-blur-sm">
                <CardContent className="p-6">
                  <h3 className="text-xl font-bold text-purple-400 mb-4">Our Focus Areas</h3>
                  <ul className="space-y-3 text-gray-300">
                    <li className="flex items-start">
                      <span className="text-purple-400 mr-2">•</span>
                      Interactive Quantum Education
                    </li>
                    <li className="flex items-start">
                      <span className="text-purple-400 mr-2">•</span>
                      Advanced Circuit Simulation for Researchers
                    </li>
                    <li className="flex items-start">
                      <span className="text-purple-400 mr-2">•</span>
                      Enterprise Post-Quantum Cryptography (PQC)
                    </li>
                    <li className="flex items-start">
                      <span className="text-purple-400 mr-2">•</span>
                      Quantum Algorithm Development & Consulting
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </div>

            <Card className="bg-gradient-to-r from-slate-800/80 to-purple-800/80 border-green-500/30 backdrop-blur-sm">
              <CardContent className="p-8 text-center">
                <Shield className="h-16 w-16 text-green-400 mx-auto mb-6" />
                <h2 className="text-3xl font-bold text-white mb-4">Security & Trust</h2>
                <p className="text-lg text-gray-300 leading-relaxed">
                  In the quantum era, security is paramount. We're committed to developing robust quantum-safe security 
                  solutions and educating the community about quantum cryptography. Our focus on security ensures that 
                  as quantum technology advances, it remains safe and trustworthy for all users.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default Vision;
