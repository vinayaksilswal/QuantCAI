import { usePageTracking } from '@/hooks/usePageTracking';
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowRight, Zap, Cloud, Users, Atom, Cpu, Rocket, Shield } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { NewsletterForm } from '@/components/NewsletterForm';
import { LogoProcessor } from '@/components/LogoProcessor';
import { FeatureSplit } from '@/components/landing/FeatureSplit';
import { PricingSection } from '@/components/landing/PricingSection';
import { TrustSection } from '@/components/landing/TrustSection';
import { CtaBanner } from '@/components/landing/CtaBanner';

const Index = () => {
  usePageTracking('home');
  return (
    <div className="min-h-screen relative overflow-hidden">
      <Navbar />

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6 relative z-10">
        <div className="max-w-7xl mx-auto w-full">
          <div className="grid lg:grid-cols-[1.1fr_0.9fr] gap-10 items-center">
            <div className="animate-fade-in">
              {/* Logo Section */}
              <div className="mb-6">
                <LogoProcessor
                  originalSrc="/lovable-uploads/56a0d2c9-73da-4624-bfb1-2bb520c4a4e3.png"
                  alt="QuantCAI Logo"
                  className="h-32 mb-1 drop-shadow-2xl brightness-110 contrast-125 saturate-110 hover:scale-105 transition-all duration-300"
                  style={{
                    filter: 'drop-shadow(0 0 20px rgba(59, 130, 246, 0.5)) drop-shadow(0 0 40px rgba(139, 92, 246, 0.3)) brightness(1.1) contrast(1.25) saturate(1.1)',
                    mixBlendMode: 'screen' as const,
                  }}
                />
              </div>

              <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight text-white drop-shadow-lg">
                Quantum Visionaries
              </h1>
              <h2 className="text-2xl md:text-3xl mb-5 font-light text-blue-100 drop-shadow-md">
                Leap Forward to Innovate, Educate, and Elevate <br />
                Tech Horizons
              </h2>
              <p className="text-lg md:text-lg mb-4 max-w-2xl leading-relaxed text-blue-200 drop-shadow-sm">
                QuantCAI is leading the quantum computer adaptation to the world through
                interactive education and cutting-edge simulations.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 md:gap-4">
                <Link to="/learn" className="w-full sm:w-auto">
                  <Button className="w-full bg-gradient-to-r from-blue-600 to-purple-700 hover:from-blue-700 hover:to-purple-800 text-white px-5 py-3 text-base md:px-6 md:py-3.5 md:text-base xl:px-8 xl:py-4 xl:text-lg rounded-lg transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2 shadow-2xl shadow-blue-500/30 border border-blue-400/30">
                    <Rocket className="h-5 w-5" />
                    Explore Quantum World
                  </Button>
                </Link>
                <Link to="/enterprise" className="w-full sm:w-auto">
                  <Button variant="outline" className="w-full border-2 border-blue-400 text-blue-200 hover:bg-blue-500/20 hover:text-white px-5 py-3 text-base md:px-6 md:py-3.5 md:text-base xl:px-8 xl:py-4 xl:text-lg rounded-lg transform hover:scale-105 transition-all duration-300 flex items-center justify-center gap-2 backdrop-blur-sm bg-white/5 shadow-xl">
                    <Shield className="h-5 w-5" />
                    For Enterprise: PQC Compliance
                  </Button>
                </Link>
              </div>
            </div>

            {/* Interactive Quantum States Section */}
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-8 border border-blue-400/40 shadow-2xl shadow-blue-500/30">
              <h3 className="text-2xl font-bold text-white mb-2 drop-shadow-md">
                Interactive Quantum States
              </h3>
              <p className="text-blue-100 mb-4 drop-shadow-sm">
                Experience real-time quantum superposition and entanglement
              </p>
              <div className="relative">
                <div className="bg-gradient-to-br from-blue-500/30 to-purple-500/30 p-6 rounded-xl border border-blue-400/40 backdrop-blur-sm shadow-xl">
                  <div className="flex items-center justify-center h-32 relative">
                    <div className="relative">
                      <Atom className="h-16 w-16 text-blue-300 animate-pulse drop-shadow-lg" />
                      <div className="absolute -top-2 -right-2 w-4 h-4 bg-yellow-400 rounded-full animate-ping shadow-lg" />
                      <div className="absolute -bottom-2 -left-2 w-3 h-3 bg-green-400 rounded-full animate-bounce shadow-md" />
                      <div className="absolute top-0 left-0 w-2 h-2 bg-purple-400 rounded-full animate-pulse shadow-sm" />
                    </div>
                  </div>
                  <div className="text-center mt-4">
                    <p className="text-white font-semibold text-xl drop-shadow-md">
                      |ψ⟩ = α|0⟩ + β|1⟩
                    </p>
                    <p className="text-blue-200 text-sm mt-2 drop-shadow-sm">
                      Quantum Superposition State
                    </p>
                  </div>
                </div>
              </div>
              <Link to="/quantum-states">
                <Button className="w-full mt-4 bg-gradient-to-r from-blue-600 to-purple-700 hover:from-blue-700 hover:to-purple-800 text-white flex items-center justify-center gap-2 shadow-2xl shadow-blue-500/30 border border-blue-400/30">
                  Launch Interactive Quantum States
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── New Sections: API, Scanner, Pricing, Trust, CTA ── */}
      <FeatureSplit />
      <PricingSection />
      <TrustSection />
      <CtaBanner />

      {/* About Section */}
      <section className="py-20 px-6 bg-white/5 backdrop-blur-sm relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="order-2 lg:order-1">
              <div className="bg-white/10 backdrop-blur-xl p-8 rounded-2xl border border-blue-400/40 shadow-2xl shadow-blue-500/30">
                <Atom className="h-16 w-16 text-blue-300 mb-6 drop-shadow-lg" />
                <h2 className="text-4xl font-bold text-white mb-6 drop-shadow-md">About QuantCAI</h2>
                <p className="text-blue-100 text-lg leading-relaxed drop-shadow-sm">
                  The idea is to make a website for quantum computer Learning, Simulation of qubits and qubits logic gates,
                  Implementation, Algorithm, and Development. It's an initiative for Quantum Computer Adaptation and Acceptance.
                  The main concern of Security and Encryption of data flow in the Quantum Computers era. To provide Security
                  and Encryption solutions in the later phase.
                </p>
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <div className="relative">
                <div className="bg-gradient-to-br from-white/20 to-white/10 p-1 rounded-2xl backdrop-blur-xl border border-blue-400/40 shadow-2xl shadow-blue-500/30">
                  <div className="bg-blue-900/40 p-8 rounded-2xl h-80 flex items-center justify-center backdrop-blur-sm">
                    <div className="text-center">
                      <Cpu className="h-24 w-24 text-blue-300 mx-auto mb-4 animate-pulse drop-shadow-lg" />
                      <h3 className="text-2xl font-bold text-white drop-shadow-md">Quantum Computing</h3>
                      <p className="text-blue-200 mt-2 drop-shadow-sm">The Future is Now</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section className="py-20 px-6 relative z-10">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center text-white mb-16 drop-shadow-lg">Our Offerings</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="bg-white/10 backdrop-blur-xl border-blue-400/40 hover:transform hover:scale-105 transition-all duration-300 shadow-2xl shadow-blue-500/30">
              <CardContent className="p-8">
                <Zap className="h-12 w-12 text-blue-300 mb-6 drop-shadow-lg" />
                <h3 className="text-2xl font-bold text-blue-200 mb-4 drop-shadow-md">Our Services</h3>
                <p className="text-blue-100 leading-relaxed drop-shadow-sm">
                  Our services include quantum computer learning, simulation, implementation, algorithm development,
                  and quantum consulting. We offer a range of solutions to help your business harness the power of quantum computing.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-xl border-purple-400/40 hover:transform hover:scale-105 transition-all duration-300 shadow-2xl shadow-purple-500/30">
              <CardContent className="p-8">
                <Cloud className="h-12 w-12 text-purple-300 mb-6 drop-shadow-lg" />
                <h3 className="text-2xl font-bold text-purple-200 mb-4 drop-shadow-md">Cloud Computing</h3>
                <p className="text-blue-100 leading-relaxed drop-shadow-sm">
                  Our cloud-based platform ensures scalability and flexibility, allowing you to access quantum computing
                  power from anywhere. Experience the future of computing in the cloud.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-white/10 backdrop-blur-xl border-green-400/40 hover:transform hover:scale-105 transition-all duration-300 shadow-2xl shadow-green-500/30">
              <CardContent className="p-8">
                <Users className="h-12 w-12 text-green-300 mb-6 drop-shadow-lg" />
                <h3 className="text-2xl font-bold text-green-200 mb-4 drop-shadow-md">Expertise</h3>
                <p className="text-blue-100 leading-relaxed drop-shadow-sm">
                  Our team of experts is dedicated to providing unparalleled support and guidance throughout your
                  quantum computing journey. Let us help you unlock the quantum advantage.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Newsletter Section */}
      <section className="py-20 px-6 bg-white/5 backdrop-blur-sm relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6 drop-shadow-lg">Stay Updated with Quantum Innovations</h2>
          <p className="text-xl text-blue-200 mb-8 drop-shadow-md">
            Get the latest insights on quantum computing, research breakthroughs, and educational content.
          </p>
          <NewsletterForm />
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Index;
