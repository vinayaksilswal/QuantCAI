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
                  QuantCAI is committed to bringing quantum computing to the masses. Our website provides an all-encompassing 
                  platform for learning and exploring the world of qubits and quantum logic gates. Our mission is to make 
                  quantum computing accessible to everyone and to promote the understanding and acceptance of this exciting 
                  technology. At QuantCAI, we prioritize the security and encryption of data flow in the quantum era, so you 
                  can trust us with your valuable information.
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
                  Our team at QuantCAI is comprised of seasoned professionals with years of experience in the field of quantum 
                  computing. From physicists to software engineers, we have the expertise to tackle any quantum computing challenge. 
                  We are dedicated to staying at the cutting edge of this exciting field and to sharing our knowledge and expertise 
                  with our clients. At QuantCAI, we believe that strong leadership is key to success, which is why we prioritize 
                  the development of our team members' leadership skills. Let us help you bring your quantum computing goals to life.
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
                  QuantCAI was founded with a passion for quantum computing and a desire to share this enthusiasm with the world. 
                  Our team of experts has a deep understanding of the intricacies of quantum physics and the potential of quantum 
                  computing. We believe that quantum computing will revolutionize many industries, from healthcare to finance, and 
                  we want to be at the forefront of this technological shift. At QuantCAI, we provide comprehensive training and 
                  simulation tools for qubits and quantum logic gates, as well as implementation and algorithm development services. 
                  Let us help you unlock the power of quantum computing and take your business to the next level.
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
                      Quantum algorithm development
                    </li>
                    <li className="flex items-start">
                      <span className="text-purple-400 mr-2">•</span>
                      Security and cryptography
                    </li>
                    <li className="flex items-start">
                      <span className="text-purple-400 mr-2">•</span>
                      Educational platform development
                    </li>
                    <li className="flex items-start">
                      <span className="text-purple-400 mr-2">•</span>
                      Industry adaptation consulting
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
